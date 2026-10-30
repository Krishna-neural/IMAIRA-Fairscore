"""
IMAIRA FairScore — Placement Officer Intelligence Package
=========================================================
Enterprise cohort analytics, skill gap intelligence, and AI evaluation quality monitoring.
"""

from analytics.cohort_models import (
    CohortFilter,
    AuthContext,
    CohortOverviewKPIs,
    SkillGapItem,
    EvaluationQualityBreakdown,
    EvaluationAlert,
    PlacementIntelligenceReport
)
from analytics.cohort_intelligence import CohortIntelligenceEngine

__all__ = [
    "CohortFilter",
    "AuthContext",
    "CohortOverviewKPIs",
    "SkillGapItem",
    "EvaluationQualityBreakdown",
    "EvaluationAlert",
    "PlacementIntelligenceReport",
    "CohortIntelligenceEngine"
]
