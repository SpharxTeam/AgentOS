# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 双模型协同协调器（1大+2小冗余）。
# 负责管理主思考者和辅思考者，实现交叉验证、冲突检测与仲裁。

from typing import Optional, Dict, Any, Tuple, List
import asyncio
import time
import uuid
from agentos_cta.utils.observability import get_logger
from agentos_cta.utils.error import ConsensusError, ModelUnavailableError
from .schemas import Intent, TaskPlan, TaskDAG, TaskNode

logger = get_logger(__name__)


class DualModelCoordinator:
    """
    双模型协同协调器。
    维护一个主思考者和两个辅思考者，提供冗余和交叉验证能力。
    """

    def __init__(self, primary_model: str, secondary_models: List[str], config: Dict[str, Any]):
        """
        初始化协调器。

        Args:
            primary_model: 主思考者模型名称（最强推理）。
            secondary_models: 辅思考者模型列表（通常两个，轻量/专业）。
            config: 配置字典（包含 API 密钥、超时等）。
        """
        self.primary_model = primary_model
        self.secondary_models = secondary_models
        self.config = config
        self._primary_available = True
        self._secondary_available = [True] * len(secondary_models)

    async def _call_model(self, model_name: str, prompt: str) -> Tuple[str, float]:
        """
        模拟调用模型（实际应调用 LLM API）。
        返回 (输出文本, 延迟秒数)
        """
        await asyncio.sleep(0.5)  # 模拟网络延迟
        if model_name == self.primary_model:
            output = f"[Primary] Processed: {prompt[:50]}..."
            latency = 0.8
        else:
            output = f"[Secondary] Processed: {prompt[:50]}..."
            latency = 0.3
        return output, latency

    async def generate_plan(self, intent: Intent, context: Dict[str, Any]) -> TaskPlan:
        """
        主入口：使用主模型生成初始规划，同时启动辅模型交叉验证。
        """
        prompt = self._build_planning_prompt(intent, context)

        primary_task = asyncio.create_task(self._call_model(self.primary_model, prompt))
        secondary_tasks = [
            asyncio.create_task(self._call_model(m, prompt))
            for m in self.secondary_models
        ]

        results = await asyncio.gather(primary_task, *secondary_tasks, return_exceptions=True)

        primary_output, primary_latency = results[0] if not isinstance(results[0], Exception) else (None, 0)
        secondary_outputs = []
        for i, res in enumerate(results[1:]):
            if isinstance(res, Exception):
                logger.error(f"Secondary model {self.secondary_models[i]} failed: {res}")
                self._secondary_available[i] = False
                secondary_outputs.append(None)
            else:
                secondary_outputs.append(res[0])

        if primary_output is None:
            # 主模型失败，尝试用辅模型接管
            for i, out in enumerate(secondary_outputs):
                if out is not None:
                    logger.warning(f"Primary failed, using secondary {self.secondary_models[i]} as fallback")
                    primary_output = out
                    break
            if primary_output is None:
                raise ModelUnavailableError("All models failed to generate plan")

        # 交叉验证一致性
        consensus = self._check_consensus(primary_output, secondary_outputs)
        if not consensus['is_consistent']:
            logger.warning(f"Consensus conflict detected: {consensus['details']}")
            # 触发仲裁：可交由审计委员会或人工介入
            # 这里简单记录并返回主模型输出

        plan = self._parse_output_to_plan(primary_output, intent)
        return plan

    def _build_planning_prompt(self, intent: Intent, context: Dict[str, Any]) -> str:
        """构建规划提示词。"""
        return f"""
You are an AI planner. Based on the user intent, generate a detailed task plan as a JSON DAG.

User intent: {intent.goal}
Context: {context}

The plan should include tasks with dependencies. Output only valid JSON.
"""

    def _check_consensus(self, primary: str, secondaries: List[Optional[str]]) -> Dict[str, Any]:
        """检查主模型与辅模型输出的一致性。"""
        valid_secondaries = [s for s in secondaries if s is not None]
        if not valid_secondaries:
            return {"is_consistent": True, "details": "No secondary outputs"}

        avg_len = sum(len(s) for s in valid_secondaries) / len(valid_secondaries)
        primary_len = len(primary)
        ratio = abs(primary_len - avg_len) / max(avg_len, 1)
        is_consistent = ratio < 0.5
        return {"is_consistent": is_consistent, "details": f"Primary length {primary_len}, avg secondary {avg_len:.1f}"}

    def _parse_output_to_plan(self, output: str, intent: Intent) -> TaskPlan:
        """将模型输出解析为 TaskPlan。简化实现。"""
        import json

        try:
            data = json.loads(output)
        except:
            data = {"tasks": []}

        dag = TaskDAG()
        # 这里简化处理，实际应根据 data 构建节点
        # 添加一个模拟节点
        node = TaskNode(
            task_id=str(uuid.uuid4()),
            name="Requirement Analysis",
            agent_role="product_manager",
            input_schema={"goal": intent.goal},
            output_schema={"prd": "string"}
        )
        dag.add_node(node)
        dag.entry_points = [node.task_id]

        plan = TaskPlan(
            plan_id=str(uuid.uuid4()),
            dag=dag,
            created_at=time.time(),
            updated_at=time.time(),
            metadata={"intent": intent.goal}
        )
        return plan

    def get_available_models(self) -> List[str]:
        """返回当前可用的模型列表。"""
        available = []
        if self._primary_available:
            available.append(self.primary_model)
        for i, avail in enumerate(self._secondary_available):
            if avail:
                available.append(self.secondary_models[i])
        return available