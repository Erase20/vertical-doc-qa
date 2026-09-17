from typing import Literal

DocumentDomain = Literal["general", "psychoeducation", "assessment", "professional"]
DomainMode = Literal["psychoeducation", "assessment", "professional"]
DocumentType = Literal["article", "guide", "scale_manual", "paper", "policy", "reference"]
Audience = Literal["public", "student", "teacher", "clinician", "researcher"]
AccessLevel = Literal["public", "restricted", "professional_only"]
ReviewStatus = Literal["draft", "reviewed", "approved", "expired"]

DOCUMENT_DOMAINS: tuple[str, ...] = (
    "general",
    "psychoeducation",
    "assessment",
    "professional",
)
DOCUMENT_TYPES: tuple[str, ...] = (
    "article",
    "guide",
    "scale_manual",
    "paper",
    "policy",
    "reference",
)
AUDIENCES: tuple[str, ...] = ("public", "student", "teacher", "clinician", "researcher")
ACCESS_LEVELS: tuple[str, ...] = ("public", "restricted", "professional_only")
REVIEW_STATUSES: tuple[str, ...] = ("draft", "reviewed", "approved", "expired")

ACCESS_LEVEL_RANK: dict[str, int] = {
    "public": 1,
    "restricted": 2,
    "professional_only": 3,
}


def allowed_access_levels(clearance: str) -> tuple[str, ...]:
    clearance_rank = ACCESS_LEVEL_RANK.get(clearance, 1)
    return tuple(
        level
        for level in ACCESS_LEVELS
        if ACCESS_LEVEL_RANK[level] <= clearance_rank
    )
