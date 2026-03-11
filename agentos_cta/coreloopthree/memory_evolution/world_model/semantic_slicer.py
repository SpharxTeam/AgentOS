# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 语义切片器：将上下文窗口视为可寻址语义空间，按需切片和检索。
# 基于 arXiv:2602.20934 "Architecting AgentOS" 中的 "Addressable Semantic Space" 概念。

import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.token_counter import TokenCounter

logger = get_logger(__name__)


@dataclass
class SemanticChunk:
    """语义切片单元。"""
    chunk_id: str
    text: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_token: int = 0
    end_token: int = 0
    importance_score: float = 1.0  # 重要性分数，用于选择性保留


class SemanticSlicer:
    """
    语义切片器。
    将连续文本或上下文切分为语义完整的块，支持按需检索和动态加载。
    核心思想：将上下文窗口从被动缓冲区转变为可主动寻址的语义空间。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化语义切片器。

        Args:
            config: 配置参数
                - chunk_size: 目标切片大小（token数）
                - overlap_tokens: 切片间重叠token数
                - min_chunk_tokens: 最小切片token数
                - embedding_model: 嵌入模型名称（用于语义检索）
        """
        self.chunk_size = config.get("chunk_size", 512)
        self.overlap_tokens = config.get("overlap_tokens", 50)
        self.min_chunk_tokens = config.get("min_chunk_tokens", 100)
        self.embedding_model = config.get("embedding_model", "text-embedding-3-small")
        self.token_counter = TokenCounter(self.embedding_model)
        
        # 切片缓存
        self.chunks: Dict[str, SemanticChunk] = {}
        self.chunk_indices: Dict[str, List[str]] = {}  # 文档ID -> chunk_id列表

    def _compute_chunk_id(self, text: str, start_pos: int) -> str:
        """计算切片的唯一ID。"""
        content = f"{text[:100]}:{start_pos}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def slice_text(self, text: str, doc_id: Optional[str] = None, metadata: Optional[Dict] = None) -> List[SemanticChunk]:
        """
        将文本切分为语义切片。

        Args:
            text: 待切分的文本
            doc_id: 文档标识（可选）
            metadata: 附加元数据

        Returns:
            语义切片列表
        """
        # 计算token序列
        tokens = self.token_counter.encoding.encode(text)
        total_tokens = len(tokens)
        
        if total_tokens <= self.chunk_size:
            # 文本本身就是一个切片
            chunk_id = self._compute_chunk_id(text, 0)
            chunk = SemanticChunk(
                chunk_id=chunk_id,
                text=text,
                metadata=metadata or {},
                start_token=0,
                end_token=total_tokens,
                importance_score=1.0
            )
            self.chunks[chunk_id] = chunk
            if doc_id:
                if doc_id not in self.chunk_indices:
                    self.chunk_indices[doc_id] = []
                self.chunk_indices[doc_id].append(chunk_id)
            return [chunk]

        # 滑动窗口切片
        chunks = []
        start = 0
        while start < total_tokens:
            end = min(start + self.chunk_size, total_tokens)
            # 如果剩余部分太少，并入前一个切片
            if total_tokens - end < self.min_chunk_tokens and start > 0:
                # 调整前一个切片的结束位置
                prev_chunk = chunks[-1]
                prev_chunk.end_token = total_tokens
                prev_chunk.text = self.token_counter.encoding.decode(tokens[prev_chunk.start_token:total_tokens])
                break

            chunk_tokens = tokens[start:end]
            chunk_text = self.token_counter.encoding.decode(chunk_tokens)
            
            # 计算切片重要性（可根据位置、关键词等调整）
            importance = 1.0
            if "error" in chunk_text.lower() or "fail" in chunk_text.lower():
                importance = 1.5  # 错误信息更重要
            elif start < self.chunk_size:
                importance = 1.2  # 开头部分更重要

            chunk_id = self._compute_chunk_id(chunk_text, start)
            chunk = SemanticChunk(
                chunk_id=chunk_id,
                text=chunk_text,
                metadata=metadata or {},
                start_token=start,
                end_token=end,
                importance_score=importance
            )
            chunks.append(chunk)
            self.chunks[chunk_id] = chunk
            
            # 移动窗口，考虑重叠
            start = end - self.overlap_tokens

        # 记录文档索引
        if doc_id:
            self.chunk_indices[doc_id] = [c.chunk_id for c in chunks]

        logger.info(f"Sliced text into {len(chunks)} chunks (total tokens: {total_tokens})")
        return chunks

    def get_chunk(self, chunk_id: str) -> Optional[SemanticChunk]:
        """获取指定切片。"""
        return self.chunks.get(chunk_id)

    def get_document_chunks(self, doc_id: str) -> List[SemanticChunk]:
        """获取文档的所有切片。"""
        chunk_ids = self.chunk_indices.get(doc_id, [])
        return [self.chunks[cid] for cid in chunk_ids if cid in self.chunks]

    async def retrieve_relevant_chunks(self, query: str, top_k: int = 5) -> List[SemanticChunk]:
        """
        检索与查询最相关的切片。
        实际应用中应使用向量检索，此处简化为关键词匹配。

        Args:
            query: 查询文本
            top_k: 返回的最大切片数

        Returns:
            相关切片列表（按相关性排序）
        """
        # 简化实现：关键词匹配 + 重要性加权
        query_terms = set(query.lower().split())
        scored_chunks = []

        for chunk_id, chunk in self.chunks.items():
            # 计算关键词匹配得分
            chunk_terms = set(chunk.text.lower().split())
            if not chunk_terms:
                continue
            overlap = query_terms.intersection(chunk_terms)
            score = len(overlap) / max(len(query_terms), 1)
            # 重要性加权
            score *= chunk.importance_score
            
            if score > 0:
                scored_chunks.append((score, chunk))

        # 排序并返回top_k
        scored_chunks.sort(reverse=True, key=lambda x: x[0])
        return [chunk for score, chunk in scored_chunks[:top_k]]

    def prune_by_importance(self, max_chunks: int = 1000) -> int:
        """
        根据重要性裁剪切片缓存，保留最重要的切片。
        用于Token预算管理。

        Args:
            max_chunks: 最大保留切片数

        Returns:
            移除的切片数量
        """
        if len(self.chunks) <= max_chunks:
            return 0

        # 按重要性排序
        sorted_chunks = sorted(
            self.chunks.items(),
            key=lambda x: x[1].importance_score,
            reverse=True
        )
        
        # 保留重要切片
        keep_chunks = dict(sorted_chunks[:max_chunks])
        removed_count = len(self.chunks) - len(keep_chunks)
        self.chunks = keep_chunks
        
        # 更新文档索引（移除已被裁剪的切片）
        for doc_id in list(self.chunk_indices.keys()):
            self.chunk_indices[doc_id] = [
                cid for cid in self.chunk_indices[doc_id]
                if cid in self.chunks
            ]
            if not self.chunk_indices[doc_id]:
                del self.chunk_indices[doc_id]

        logger.info(f"Pruned {removed_count} chunks, remaining: {len(self.chunks)}")
        return removed_count

    def estimate_token_usage(self, chunk_ids: List[str]) -> int:
        """估算指定切片的token总数。"""
        total = 0
        for cid in chunk_ids:
            chunk = self.chunks.get(cid)
            if chunk:
                total += (chunk.end_token - chunk.start_token)
        return total