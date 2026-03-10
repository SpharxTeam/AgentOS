# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 技术委员会：负责技术债务评估、规范更新。

from typing import Dict, Any, List, Optional
import time
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.file_utils import FileUtils

logger = get_logger(__name__)


class TechnicalCommittee:
    """
    技术委员会。
    分析技术债务，评审技术选型，更新技术规范。
    """

    def __init__(self, config: Dict[str, Any], specs_dir: str = "config/specs"):
        self.config = config
        self.specs_dir = specs_dir
        FileUtils.ensure_dir(specs_dir)

    async def analyze_round(self, round_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析技术数据，生成技术回顾报告。

        Args:
            round_data: 包含代码评审报告、测试报告、架构决策等

        Returns:
            技术回顾报告
        """
        debt = self._assess_technical_debt(round_data)
        spec_updates = self._propose_spec_updates(round_data, debt)

        report = {
            "round_id": round_data.get("round_id"),
            "timestamp": time.time(),
            "technical_debt": debt,
            "spec_updates": spec_updates,
            "recommendations": self._generate_recommendations(debt),
        }
        logger.info(f"Technical analysis completed for round {round_data.get('round_id')}")
        return report

    def _assess_technical_debt(self, round_data: Dict) -> Dict:
        """评估技术债务。"""
        review = round_data.get("code_review", {})
        issues = review.get("issues", [])
        # 分类问题
        categories = {}
        for issue in issues:
            cat = issue.get("category", "other")
            categories[cat] = categories.get(cat, 0) + 1

        # 量化债务分数
        debt_score = len(issues) * 0.1  # 简单示例
        return {
            "total_issues": len(issues),
            "categories": categories,
            "debt_score": debt_score,
            "critical_issues": [i for i in issues if i.get("severity") == "critical"],
        }

    def _propose_spec_updates(self, round_data: Dict, debt: Dict) -> List[Dict]:
        """根据问题提出规范更新建议。"""
        updates = []
        for cat, count in debt.get("categories", {}).items():
            if count > self.config.get("spec_update_threshold", 5):
                updates.append({
                    "spec": f"{cat}_spec.md",
                    "reason": f"High frequency of {cat} issues ({count})",
                    "suggestion": f"Add stricter guidelines for {cat}",
                })
        return updates

    def _generate_recommendations(self, debt: Dict) -> List[str]:
        """生成技术建议。"""
        recs = []
        if debt.get("debt_score", 0) > 10:
            recs.append("Schedule a dedicated refactoring sprint to address technical debt.")
        if debt.get("critical_issues"):
            recs.append("Critical issues must be fixed before next release.")
        return recs

    async def update_spec(self, spec_name: str, content: str) -> bool:
        """更新技术规范文件。"""
        path = f"{self.specs_dir}/{spec_name}"
        return FileUtils.safe_write(path, content)