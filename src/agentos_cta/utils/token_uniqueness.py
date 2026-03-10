# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# Token 独特性预测模块。
# 评估跨查询的 token 重复率，用于优化缓存策略，降低冗余计算。

from typing import List, Set, Dict
import hashlib
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class TokenUniquenessPredictor:
    """
    Token 独特性预测器。
    基于历史查询分析 token 重复模式，为缓存决策提供依据。
    """

    def __init__(self, window_size: int = 1000):
        """
        初始化预测器。

        Args:
            window_size: 保留最近查询的数量，用于计算重复率。
        """
        self.window_size = window_size
        self.query_history: List[str] = []  # 存储历史查询的 hash 或摘要
        self.token_ngram_cache: Dict[str, Set[str]] = defaultdict(set)  # n-gram 到查询 ID 的映射

    def _hash_query(self, query: str) -> str:
        """生成查询的摘要标识。"""
        return hashlib.md5(query.encode()).hexdigest()

    def _extract_ngrams(self, text: str, n: int = 3) -> Set[str]:
        """提取文本的 n-gram 集合，用于局部重复检测。"""
        ngrams = set()
        if len(text) < n:
            return {text}
        for i in range(len(text) - n + 1):
            ngrams.add(text[i:i + n])
        return ngrams

    def record_query(self, query: str):
        """记录一次查询，更新历史窗口。"""
        qid = self._hash_query(query)
        self.query_history.append(qid)
        if len(self.query_history) > self.window_size:
            removed = self.query_history.pop(0)
            # 清理 n-gram 缓存中的对应记录（可选，保持简洁可省略）
        # 提取 n-gram 并记录
        ngrams = self._extract_ngrams(query)
        for ng in ngrams:
            self.token_ngram_cache[ng].add(qid)

    def predict_uniqueness(self, query: str) -> float:
        """
        预测给定查询的 token 独特性分数（0~1）。
        1 表示完全独特（无重复），0 表示完全重复。
        """
        if not self.query_history:
            return 1.0  # 无历史，视为独特

        ngrams = self._extract_ngrams(query)
        if not ngrams:
            return 1.0

        total_occurrences = 0
        for ng in ngrams:
            total_occurrences += len(self.token_ngram_cache.get(ng, set()))
        avg_occurrences = total_occurrences / len(ngrams)
        # 归一化：假设最大重复数为历史窗口大小
        uniqueness = 1.0 - (avg_occurrences / self.window_size)
        return max(0.0, min(1.0, uniqueness))  # 限制在 [0,1]

    def should_cache(self, query: str, threshold: float = 0.3) -> bool:
        """
        根据独特性决定是否应该使用缓存。
        若独特性低于阈值，表示重复度高，适合缓存。

        Args:
            query: 查询文本。
            threshold: 独特性阈值，低于此值建议缓存。

        Returns:
            True 表示建议缓存，False 不建议。
        """
        uniqueness = self.predict_uniqueness(query)
        return uniqueness < threshold