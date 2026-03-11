# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 增量规划器：分阶段生成任务 DAG，并根据执行反馈动态调整。

from typing import Dict, Any, Optional, List
import time
import uuid
from agentos_cta.utils.observability import get_logger
from .schemas import TaskPlan, TaskDAG, TaskNode, TaskStatus

logger = get_logger(__name__)


class IncrementalPlanner:
    """
    增量规划器。
    不一次性生成全部计划，而是先生成第一阶段，后续根据反馈动态扩展。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_retries = config.get('max_plan_retries', 3)

    def create_initial_plan(self, goal: str, context: Dict[str, Any]) -> TaskPlan:
        """
        根据目标生成初始阶段计划。
        实际应由 LLM 生成，这里模拟一个简单的固定计划。
        """
        plan_id = str(uuid.uuid4())
        dag = TaskDAG()

        task1 = TaskNode(
            task_id=str(uuid.uuid4()),
            name="Requirement Analysis",
            agent_role="product_manager",
            input_schema={"goal": goal, "context": context},
            output_schema={"prd": "string"},
            depends_on=[]
        )
        dag.add_node(task1)
        dag.entry_points = [task1.task_id]

        plan = TaskPlan(
            plan_id=plan_id,
            dag=dag,
            created_at=time.time(),
            updated_at=time.time(),
            metadata={"goal": goal}
        )
        logger.info(f"Initial plan created with {len(dag.nodes)} tasks")
        return plan

    def extend_plan(self, current_plan: TaskPlan, completed_task_ids: List[str],
                    feedback: Dict[str, Any]) -> TaskPlan:
        """
        根据已完成任务和反馈，扩展后续阶段。
        返回更新后的计划。
        """
        new_task = TaskNode(
            task_id=str(uuid.uuid4()),
            name="System Design",
            agent_role="architect",
            input_schema={"prd": "..."},
            output_schema={"design_doc": "string"},
            depends_on=completed_task_ids
        )
        current_plan.dag.add_node(new_task)
        current_plan.updated_at = time.time()
        logger.info(f"Plan extended with new task: {new_task.name}")
        return current_plan

    def revise_plan(self, plan: TaskPlan, failed_task_id: str, reason: str) -> TaskPlan:
        """
        根据失败任务修订计划（回退或替换）。
        """
        if failed_task_id in plan.dag.nodes:
            node = plan.dag.nodes[failed_task_id]
            node.status = TaskStatus.FAILED
            node.error = reason

            alt_task = TaskNode(
                task_id=str(uuid.uuid4()),
                name=f"{node.name} (retry)",
                agent_role=node.agent_role,
                input_schema=node.input_schema,
                output_schema=node.output_schema,
                depends_on=node.depends_on
            )
            plan.dag.add_node(alt_task)
            logger.info(f"Revised plan: added alternative for {failed_task_id}")
        plan.updated_at = time.time()
        return plan