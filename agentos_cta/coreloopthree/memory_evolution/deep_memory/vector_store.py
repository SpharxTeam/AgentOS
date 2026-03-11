# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# L3 Vector：向量存储，支持混合检索（BM25 + 向量）。

import sqlite3
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np
from agentos_cta.utils.structured_logger import get_logger

logger = get_logger(__name__)

# 尝试导入向量相关库，若无则使用模拟
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("chromadb not installed, vector store will use fallback")


class VectorStore:
    """
    L3 Vector：向量存储，支持混合检索。
    使用 ChromaDB 作为向量数据库，并集成 SQLite 存储元数据。
    """

    def __init__(self, persist_dir: str = "data/workspace/memory/vector"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # 初始化 ChromaDB（如果可用）
        if CHROMA_AVAILABLE:
            self.chroma_client = chromadb.PersistentClient(path=str(self.persist_dir / "chroma"))
            self.collection = self.chroma_client.get_or_create_collection(name="memory")
        else:
            self.chroma_client = None
            self.collection = None
            logger.warning("Using fallback in-memory dict for vector store")
            self._fallback_store = {}  # id -> (embedding, metadata)

        # SQLite 存储元数据（如文本内容、时间戳等）
        self.db_path = self.persist_dir / "metadata.db"
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                text TEXT,
                metadata TEXT,
                created_at REAL
            )
        """)
        # 创建全文搜索虚拟表（BM25）
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(text, content=chunks);
        """)
        conn.commit()
        conn.close()

    async def add(self, chunk_id: str, text: str, embedding: List[float], metadata: Dict[str, Any]):
        """添加一个文本块及其向量。"""
        # 存入向量数据库
        if self.collection:
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[text]
            )
        else:
            self._fallback_store[chunk_id] = (embedding, metadata, text)

        # 存入 SQLite 用于全文检索
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO chunks (id, text, metadata, created_at) VALUES (?, ?, ?, ?)",
            (chunk_id, text, json.dumps(metadata), metadata.get("timestamp", 0))
        )
        # 插入全文索引（使用 fts5 的自动同步需要额外操作，此处简化）
        cursor.execute("INSERT INTO chunks_fts (rowid, text) VALUES (?, ?)", (cursor.lastrowid, text))
        conn.commit()
        conn.close()

    async def search(self, query: str, top_k: int = 10, method: str = "hybrid") -> List[Dict[str, Any]]:
        """
        搜索最相似的文本块。
        method: "vector", "bm25", "hybrid"
        """
        if method in ("vector", "hybrid") and self.collection:
            # 向量搜索（需要将 query 转为 embedding，此处简化）
            # 实际应调用 embedding 模型，这里返回模拟结果
            results = self.collection.query(query_texts=[query], n_results=top_k)
            vector_results = [
                {"id": results["ids"][0][i], "score": results["distances"][0][i], "text": results["documents"][0][i]}
                for i in range(len(results["ids"][0]))
            ]
        else:
            vector_results = []

        if method in ("bm25", "hybrid"):
            # BM25 全文搜索
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, text, rank FROM chunks_fts WHERE text MATCH ? ORDER BY rank LIMIT ?",
                (query, top_k)
            )
            bm25_rows = cursor.fetchall()
            conn.close()
            bm25_results = [{"id": row[0], "score": row[2], "text": row[1]} for row in bm25_rows]
        else:
            bm25_results = []

        if method == "vector":
            return vector_results
        elif method == "bm25":
            return bm25_results
        else:  # hybrid
            # 简单合并去重，按分数加权（此处略）
            combined = {r["id"]: r for r in vector_results}
            for r in bm25_results:
                if r["id"] not in combined:
                    combined[r["id"]] = r
            return list(combined.values())