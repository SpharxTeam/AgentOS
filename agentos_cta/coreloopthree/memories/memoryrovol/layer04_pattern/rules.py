# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 规则生成器：将持久模式转换为可复用的 Agent 规则。

import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.file_utils import FileUtils

logger = get_logger(__name__)


@dataclass
class Rule:
    """Agent 规则。"""
    rule_id: str
    name: str
    description: str
    condition: str  # 规则条件（如 "if memory retrieval confidence > 0.8"）
    action: str     # 规则动作（如 "use L4 pattern for planning"）
    confidence: float  # 置信度
    source_cluster_id: str  # 来源模式聚类 ID
    created_at: float
    version: int = 1
    enabled: bool = True


class RuleGenerator:
    """
    规则生成器。
    将持久模式挖掘得到的模式聚类转换为可复用的 Agent 规则。
    规则可注入 Agent 规则库或更新 Agent 契约。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化规则生成器。

        Args:
            config: 配置参数。
                - rules_dir: 规则存储目录
                - min_confidence: 最小置信度阈值
                - auto_activate: 是否自动激活规则
        """
        self.config = config
        self.rules_dir = Path(config.get("rules_dir", "data/rules"))
        self.rules_dir.mkdir(parents=True, exist_ok=True)
        self.min_confidence = config.get("min_confidence", 0.7)
        self.auto_activate = config.get("auto_activate", False)
        self.rules: List[Rule] = []

    async def generate_rules_from_clusters(
        self,
        clusters: List['PatternCluster'],
        existing_rules: Optional[List[Rule]] = None
    ) -> List[Rule]:
        """
        从模式聚类生成规则。

        Args:
            clusters: 模式聚类列表。
            existing_rules: 已有规则列表（用于版本控制）。

        Returns:
            生成的规则列表。
        """
        new_rules = []

        for cluster in clusters:
            # 跳过置信度低的聚类
            if not cluster.persistent_features:
                continue

            # 计算聚类置信度（基于持久特征的平均持久性）
            if cluster.persistent_features:
                avg_persistence = np.mean([f.persistence for f in cluster.persistent_features])
                confidence = min(1.0, avg_persistence)
            else:
                confidence = 0.5

            if confidence < self.min_confidence:
                continue

            # 为聚类生成规则
            rule = await self._cluster_to_rule(cluster, confidence)
            if rule:
                new_rules.append(rule)

        # 版本控制：检查是否与已有规则重复
        if existing_rules:
            new_rules = self._deduplicate_rules(new_rules, existing_rules)

        self.rules.extend(new_rules)
        logger.info(f"Generated {len(new_rules)} rules from {len(clusters)} clusters")
        return new_rules

    async def _cluster_to_rule(self, cluster: 'PatternCluster', confidence: float) -> Optional[Rule]:
        """
        将单个聚类转换为规则。
        这里使用模板生成规则，实际应用可使用 LLM 生成更自然的规则。
        """
        # 根据聚类的持久特征维度生成规则
        dims = set(f.dimension for f in cluster.persistent_features)

        if 0 in dims:
            # 0 维特征：连通分量 -> 相似性规则
            rule_template = {
                "name": f"Similarity Pattern from {cluster.cluster_id}",
                "description": f"Cluster contains {len(cluster.memory_ids)} memories with strong connectivity",
                "condition": "if memory similarity > threshold",
                "action": "group memories together for context",
            }
        elif 1 in dims:
            # 1 维特征：环 -> 循环模式或依赖规则
            rule_template = {
                "name": f"Cyclic Pattern from {cluster.cluster_id}",
                "description": "Detected cyclic dependencies in memory structure",
                "condition": "if circular reference detected",
                "action": "apply cyclic resolution strategy",
            }
        elif 2 in dims:
            # 2 维特征：空洞 -> 异常或缺失规则
            rule_template = {
                "name": f"Anomaly Pattern from {cluster.cluster_id}",
                "description": "Detected voids in memory coverage",
                "condition": "if information gap > threshold",
                "action": "trigger information seeking",
            }
        else:
            # 通用规则
            rule_template = {
                "name": f"Generic Pattern from {cluster.cluster_id}",
                "description": cluster.summary,
                "condition": "if context matches cluster centroid",
                "action": "use cluster as reference",
            }

        rule_id = f"rule_{cluster.cluster_id}_{int(time.time())}"
        rule = Rule(
            rule_id=rule_id,
            name=rule_template["name"],
            description=rule_template["description"],
            condition=rule_template["condition"],
            action=rule_template["action"],
            confidence=confidence,
            source_cluster_id=cluster.cluster_id,
            created_at=time.time(),
            enabled=self.auto_activate,
        )
        return rule

    def _deduplicate_rules(self, new_rules: List[Rule], existing_rules: List[Rule]) -> List[Rule]:
        """
        去重：避免生成重复规则。
        基于规则的条件和动作进行相似度比较。
        """
        unique_rules = []

        for new_rule in new_rules:
            duplicate = False
            for existing in existing_rules:
                # 简单去重：比较条件字符串
                if new_rule.condition == existing.condition:
                    duplicate = True
                    break
                # 也可使用语义相似度，但这里简化
            if not duplicate:
                unique_rules.append(new_rule)

        return unique_rules

    async def save_rules(self, rules: Optional[List[Rule]] = None):
        """
        保存规则到文件。
        """
        save_rules = rules if rules is not None else self.rules

        rules_data = []
        for r in save_rules:
            rules_data.append({
                "rule_id": r.rule_id,
                "name": r.name,
                "description": r.description,
                "condition": r.condition,
                "action": r.action,
                "confidence": r.confidence,
                "source_cluster_id": r.source_cluster_id,
                "created_at": r.created_at,
                "version": r.version,
                "enabled": r.enabled,
            })

        # 按创建时间排序
        rules_data.sort(key=lambda x: x["created_at"], reverse=True)

        file_path = self.rules_dir / "rules.json"
        FileUtils.write_json(file_path, {"rules": rules_data})
        logger.info(f"Saved {len(rules_data)} rules to {file_path}")

    async def load_rules(self) -> List[Rule]:
        """
        从文件加载规则。
        """
        file_path = self.rules_dir / "rules.json"
        data = FileUtils.read_json(file_path)

        if not data or "rules" not in data:
            return []

        rules = []
        for r_data in data["rules"]:
            rule = Rule(
                rule_id=r_data["rule_id"],
                name=r_data["name"],
                description=r_data["description"],
                condition=r_data["condition"],
                action=r_data["action"],
                confidence=r_data["confidence"],
                source_cluster_id=r_data["source_cluster_id"],
                created_at=r_data["created_at"],
                version=r_data.get("version", 1),
                enabled=r_data.get("enabled", True),
            )
            rules.append(rule)

        self.rules = rules
        logger.info(f"Loaded {len(rules)} rules from {file_path}")
        return rules

    async def inject_rules_to_agents(self, rules: List[Rule], agent_registry) -> bool:
        """
        将规则注入到 Agent 注册中心。
        更新 Agent 契约或规则文件。
        """
        success_count = 0
        for rule in rules:
            try:
                # 将规则格式化为 Agent 可读的形式
                rule_entry = {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "condition": rule.condition,
                    "action": rule.action,
                    "confidence": rule.confidence,
                    "enabled": rule.enabled,
                }

                # 通过 Agent 注册中心更新规则
                # 这里假设 agent_registry 有 update_rules 方法
                if hasattr(agent_registry, 'update_rules'):
                    await agent_registry.update_rules(rule_entry)
                    success_count += 1
                else:
                    logger.warning("Agent registry does not support rule update")

            except Exception as e:
                logger.error(f"Failed to inject rule {rule.rule_id}: {e}")

        logger.info(f"Injected {success_count}/{len(rules)} rules to agent registry")
        return success_count == len(rules)