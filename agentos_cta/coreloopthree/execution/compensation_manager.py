# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 补偿事务管理器。

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import asyncio
from agentos_cta.utils.observability import get_logger

logger = get_logger(__name__)


@dataclass
class CompensableAction:
    """可补偿的动作记录。"""
    action_id: str
    task_id: str
    unit_id: str
    input_data: Dict[str, Any]
    result: Dict[str, Any]
    compensator_id: Optional[str] = None  # 用于补偿的单元 ID
    compensated: bool = False
    compensation_result: Optional[Dict[str, Any]] = None
    compensation_error: Optional[str] = None


class CompensationManager:
    """
    补偿事务管理器。
    记录所有已执行的可补偿操作，并在需要时触发补偿。
    对于不可逆操作，记录到人工介入队列。
    """

    def __init__(self, unit_pool):
        """
        初始化补偿管理器。

        Args:
            unit_pool: 执行单元池，用于获取补偿单元。
        """
        self.unit_pool = unit_pool
        self.actions: Dict[str, CompensableAction] = {}
        self._lock = asyncio.Lock()
        self.human_intervention_queue: List[Dict] = []  # 人工介入队列

    async def register_action(self, action_id: str, task_id: str, unit_id: str,
                              input_data: Dict[str, Any], result: Dict[str, Any],
                              compensator_id: Optional[str] = None):
        """注册一个已执行的动作。"""
        async with self._lock:
            action = CompensableAction(
                action_id=action_id,
                task_id=task_id,
                unit_id=unit_id,
                input_data=input_data,
                result=result,
                compensator_id=compensator_id
            )
            self.actions[action_id] = action
            logger.info(f"Registered compensable action {action_id} for task {task_id}")

    async def compensate(self, action_id: str) -> bool:
        """对指定动作进行补偿（如果可补偿）。"""
        async with self._lock:
            action = self.actions.get(action_id)
            if not action:
                logger.warning(f"Action {action_id} not found for compensation")
                return False
            if action.compensated:
                logger.info(f"Action {action_id} already compensated")
                return True

        # 如果有指定的补偿单元
        if action.compensator_id:
            try:
                unit = await self.unit_pool.get_unit(action.compensator_id)
                comp_input = {
                    "original_input": action.input_data,
                    "original_result": action.result
                }
                comp_result = await unit.execute(comp_input)
                async with self._lock:
                    action.compensated = True
                    action.compensation_result = comp_result
                logger.info(f"Compensated action {action_id}")
                return True
            except Exception as e:
                async with self._lock:
                    action.compensation_error = str(e)
                logger.error(f"Compensation failed for {action_id}: {e}")
                await self.add_to_human_queue(action_id, reason=f"Compensation failed: {e}")
                return False
        else:
            await self.add_to_human_queue(action_id, reason="No compensator defined")
            return False

    async def add_to_human_queue(self, action_id: str, reason: str):
        """将动作加入人工介入队列。"""
        async with self._lock:
            self.human_intervention_queue.append({
                "action_id": action_id,
                "reason": reason,
                "timestamp": asyncio.get_event_loop().time()
            })
            logger.warning(f"Action {action_id} added to human intervention queue: {reason}")

    def get_human_queue(self) -> List[Dict]:
        """获取当前人工介入队列。"""
        return self.human_intervention_queue.copy()