# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 调度官：从 Agent 注册中心查询匹配的 Agent，多目标优化分配任务。

from typing import List, Dict, Any, Optional
import asyncio
from agentos_cta.utils.observability import get_logger
from agentos_cta.utils.error import ResourceLimitError
from .schemas import TaskNode, TaskPlan

logger = get_logger(__name__)


class Dispatcher:
    """
    调度官。
    负责查询 Agent 注册中心，根据成本、性能、信任度选择最佳 Agent 并分配任务。
    """

    def __init__(self, registry_client, config: Dict[str, Any]):
        """
        初始化调度官。

        Args:
            registry_client: Agent 注册中心客户端，需实现 query_agents() 方法。
            config: 配置（如权重、超时等）。
        """
        self.registry = registry_client
        self.config = config
        self.weights = config.get('selection_weights', {
            'cost': 0.3,
            'performance': 0.4,
            'trust': 0.3
        })

    async def select_agent(self, task: TaskNode, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        为单个任务选择最佳 Agent。

        Args:
            task: 待分配的任务节点。
            context: 全局上下文（项目信息等）。

        Returns:
            选中的 Agent 信息（包含 agent_id、契约等），若无可选返回 None。
        """
        candidates = await self.registry.query_agents(role=task.agent_role, task_schema=task.input_schema)

        if not candidates:
            logger.warning(f"No agents found for role {task.agent_role}")
            return None

        scored = []
        for agent in candidates:
            cost_score = 1.0 / (agent.get('cost_estimate', 1) + 1)
            perf_score = agent.get('success_rate', 0.5)
            trust_score = agent.get('trust_score', 0.5)

            total = (self.weights['cost'] * cost_score +
                     self.weights['performance'] * perf_score +
                     self.weights['trust'] * trust_score)
            scored.append((total, agent))

        scored.sort(reverse=True, key=lambda x: x[0])
        best_agent = scored[0][1]
        logger.info(f"Selected agent {best_agent.get('agent_id')} for task {task.task_id} with score {scored[0][0]:.2f}")
        return best_agent

    async def dispatch_task(self, task: TaskNode, agent_info: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        向选中的 Agent 分配任务并等待执行结果。
        实际应通过 runtime 调用 Agent，这里模拟返回。
        """
        await asyncio.sleep(1)
        result = {
            "task_id": task.task_id,
            "status": "success",
            "output": {"design_doc": "..."},
            "execution_time_ms": 1200
        }
        logger.info(f"Task {task.task_id} completed")
        return result

    async def dispatch_plan(self, plan: TaskPlan, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        调度整个计划，依次执行就绪任务。
        返回执行结果汇总。
        """
        completed = set()
        results = {}
        while True:
            ready_tasks = plan.dag.get_ready_tasks(completed)
            if not ready_tasks:
                break

            async def execute_one(task: TaskNode):
                agent = await self.select_agent(task, context)
                if agent is None:
                    task.status = "failed"
                    task.error = "No agent available"
                    return task.task_id, None
                result = await self.dispatch_task(task, agent, context)
                task.status = result.get('status', 'failed')
                task.result = result.get('output')
                task.error = result.get('error')
                return task.task_id, result

            tasks = [execute_one(task) for task in ready_tasks]
            completed_results = await asyncio.gather(*tasks)

            for task_id, result in completed_results:
                completed.add(task_id)
                if result:
                    results[task_id] = result

        all_success = all(node.status == 'succeeded' for node in plan.dag.nodes.values())
        return {
            "plan_id": plan.plan_id,
            "success": all_success,
            "results": results
        }