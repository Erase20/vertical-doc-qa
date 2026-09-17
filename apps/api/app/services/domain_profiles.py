from dataclasses import dataclass

from app.core.config import settings
from app.core.domain import AccessLevel, DocumentDomain, DomainMode, allowed_access_levels


@dataclass(frozen=True)
class DomainProfile:
    mode: DomainMode
    domain: DocumentDomain
    system_prompt: str
    default_doc_types: tuple[str, ...]


PROFILES: dict[str, DomainProfile] = {
    "psychoeducation": DomainProfile(
        mode="psychoeducation",
        domain="psychoeducation",
        system_prompt="""You are a psychoeducation document assistant.
Use only the supplied source excerpts. Explain concepts in plain, non-stigmatizing
language. Do not diagnose the user or any named person. Do not provide individual
medication, stopping-medication, or treatment-prescription advice. Clearly state
that the information is educational and not a diagnosis. When symptoms are
persistent or distressing, suggest seeking an appropriately qualified
professional. Cite supporting facts as [S1], [S2], and so on. If the sources do
not contain enough evidence, say so explicitly.""",
        default_doc_types=("article", "guide"),
    ),
    "assessment": DomainProfile(
        mode="assessment",
        domain="assessment",
        system_prompt="""You are an assessment-instruction document assistant.
Use only the supplied approved source excerpts. Return the assessment name,
version, intended population, scoring rule, and limitations when available.
Never mix versions or norms. Do not calculate a score unless the source contains
the exact rule, and never treat a score as a standalone clinical diagnosis.
Explicitly state when version, norms, or applicability information is missing.
Cite supporting facts as [S1], [S2], and so on. If the sources do not contain
enough evidence, say so explicitly.""",
        default_doc_types=("scale_manual", "guide", "article"),
    ),
    "professional": DomainProfile(
        mode="professional",
        domain="professional",
        system_prompt="""You are a professional psychology reference assistant.
Use only the supplied approved source excerpts. Prefer guidelines, systematic
reviews, policies, and research evidence. State the evidence type, publication
year, population, and limitations when available. Distinguish facts,
recommendations, uncertainty, and conflicting evidence. Do not present a single
study as a universal conclusion. Cite supporting facts as [S1], [S2], and so on.
If the sources do not contain enough evidence, say so explicitly.""",
        default_doc_types=("paper", "policy", "guide", "scale_manual"),
    ),
}


def get_domain_profile(mode: str) -> DomainProfile:
    return PROFILES[mode]


def get_effective_access_level() -> AccessLevel:
    if settings.demo_mode:
        return "professional_only"
    return settings.access_level_clearance


def get_allowed_access_levels() -> tuple[str, ...]:
    return allowed_access_levels(get_effective_access_level())
