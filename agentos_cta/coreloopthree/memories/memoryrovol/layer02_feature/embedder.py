# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 嵌入模型封装：支持多模态文本/图像嵌入，向量归一化。

import asyncio
from typing import List, Optional, Union, Dict, Any
import numpy as np
from agentos_cta.utils.observability import get_logger
from agentos_cta.utils.error import AgentOSError

logger = get_logger(__name__)


class Embedder:
    """
    语义嵌入器。
    封装嵌入模型，支持文本和图像等多模态输入，提供批次处理和向量归一化。
    符合 Aeon 架构中对嵌入层的要求 [citation:1]。
    """

    SUPPORTED_MODELS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "all-MiniLM-L6-v2": 384,
        "clip-vit-base-patch32": 512,
    }

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", config: Optional[Dict[str, Any]] = None):
        """
        初始化嵌入器。

        Args:
            model_name: 嵌入模型名称，需在 SUPPORTED_MODELS 中。
            config: 配置参数，如批次大小、归一化选项等。
        """
        if model_name not in self.SUPPORTED_MODELS:
            raise AgentOSError(f"Unsupported model: {model_name}. Supported: {list(self.SUPPORTED_MODELS.keys())}")

        self.model_name = model_name
        self.dimension = self.SUPPORTED_MODELS[model_name]
        self.config = config or {}
        self.batch_size = self.config.get("batch_size", 32)
        self.normalize = self.config.get("normalize", True)  # 默认进行 L2 归一化
        self._model = None  # 延迟加载模型

    def _lazy_load_model(self):
        """延迟加载嵌入模型（实际集成 sentence-transformers、OpenAI 等）。"""
        if self._model is not None:
            return

        try:
            if self.model_name.startswith("text-embedding-3"):
                # OpenAI 嵌入模型
                import openai
                self._model = openai.Embedding
                logger.info(f"Loaded OpenAI model: {self.model_name}")
            elif self.model_name.startswith("all-"):
                # Sentence-Transformers 模型
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Loaded SentenceTransformer model: {self.model_name}")
            elif self.model_name.startswith("clip-"):
                # CLIP 模型（支持图像和文本）
                import clip
                import torch
                self._model, _ = clip.load("ViT-B/32")
                logger.info(f"Loaded CLIP model: {self.model_name}")
            else:
                raise AgentOSError(f"Model {self.model_name} loading not implemented")
        except ImportError as e:
            raise AgentOSError(f"Required library not installed for {self.model_name}: {e}")

    async def embed_text(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        将文本转换为嵌入向量。

        Args:
            texts: 单个文本字符串或文本列表。

        Returns:
            numpy 数组，形状为 (n_texts, dimension)。
            如果 normalize=True，向量长度为 1。
        """
        self._lazy_load_model()
        single = isinstance(texts, str)
        if single:
            texts = [texts]

        # 批次处理
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            if self.model_name.startswith("text-embedding-3"):
                # OpenAI API 调用（模拟）
                response = await asyncio.to_thread(
                    self._model.create,
                    input=batch,
                    model=self.model_name
                )
                batch_embeddings = [item["embedding"] for item in response["data"]]
            elif self.model_name.startswith("all-"):
                # Sentence-Transformers 同步调用，需异步包装
                batch_embeddings = await asyncio.to_thread(self._model.encode, batch)
            elif self.model_name.startswith("clip-"):
                # CLIP 文本编码
                import torch
                text_tokens = await asyncio.to_thread(
                    lambda: torch.cat([clip.tokenize(t) for t in batch])
                )
                with torch.no_grad():
                    batch_embeddings = self._model.encode_text(text_tokens).cpu().numpy()
            else:
                raise AgentOSError(f"Embedding not implemented for {self.model_name}")

            all_embeddings.extend(batch_embeddings)

        embeddings = np.array(all_embeddings)

        # L2 归一化（确保向量位于单位超球面上）
        if self.normalize:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1  # 避免除零
            embeddings = embeddings / norms

        if single:
            return embeddings[0]
        return embeddings

    async def embed_image(self, images: Union[str, List[str]]) -> np.ndarray:
        """
        将图像路径或 URL 转换为嵌入向量。
        仅支持多模态模型（如 CLIP）。
        """
        if not self.model_name.startswith("clip-"):
            raise AgentOSError(f"Image embedding not supported by {self.model_name}")

        self._lazy_load_model()
        single = isinstance(images, str)
        if single:
            images = [images]

        import torch
        from PIL import Image
        import requests
        from io import BytesIO

        all_embeddings = []
        for img_path in images:
            # 加载图像（支持本地路径或 URL）
            if img_path.startswith(('http://', 'https://')):
                response = requests.get(img_path)
                img = Image.open(BytesIO(response.content))
            else:
                img = Image.open(img_path)

            # 预处理
            import clip
            image_input = await asyncio.to_thread(
                lambda: clip.preprocess(img).unsqueeze(0)
            )

            with torch.no_grad():
                embedding = self._model.encode_image(image_input).cpu().numpy()[0]
            all_embeddings.append(embedding)

        embeddings = np.array(all_embeddings)

        if self.normalize:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1
            embeddings = embeddings / norms

        if single:
            return embeddings[0]
        return embeddings

    def get_dimension(self) -> int:
        """返回嵌入向量维度。"""
        return self.dimension