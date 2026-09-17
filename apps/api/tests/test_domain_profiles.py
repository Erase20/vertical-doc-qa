from app.core.domain import allowed_access_levels
from app.services.domain_profiles import get_domain_profile
from app.services.safety import detect_safety_issue


def test_domain_profiles_have_distinct_retrieval_scope() -> None:
    psychoeducation = get_domain_profile("psychoeducation")
    assessment = get_domain_profile("assessment")
    professional = get_domain_profile("professional")

    assert psychoeducation.domain == "psychoeducation"
    assert "scale_manual" not in psychoeducation.default_doc_types
    assert "scale_manual" in assessment.default_doc_types
    assert "paper" in professional.default_doc_types


def test_access_level_clearance_expands_allowed_levels() -> None:
    assert allowed_access_levels("public") == ("public",)
    assert allowed_access_levels("restricted") == ("public", "restricted")
    assert allowed_access_levels("professional_only") == (
        "public",
        "restricted",
        "professional_only",
    )


def test_crisis_question_is_detected() -> None:
    decision = detect_safety_issue("我最近不想活了，应该怎么办？")

    assert decision.level == "crisis"
    assert decision.action == "show_support"


def test_normal_question_is_not_flagged() -> None:
    decision = detect_safety_issue("焦虑通常有哪些表现？")

    assert decision.level == "normal"
