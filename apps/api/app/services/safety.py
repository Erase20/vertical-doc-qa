from dataclasses import dataclass

from app.core.config import settings

_CRISIS_PATTERNS = (
    "自杀",
    "想死",
    "不想活",
    "结束生命",
    "结束自己",
    "活不下去",
    "伤害自己",
    "自残",
    "割腕",
    "跳楼",
    "服药自杀",
    "杀了自己",
    "suicide",
    "kill myself",
    "end my life",
    "self-harm",
    "hurt myself",
)


@dataclass(frozen=True)
class SafetyDecision:
    level: str
    action: str


def detect_safety_issue(question: str) -> SafetyDecision:
    normalized = " ".join(question.casefold().split())
    if settings.crisis_support_enabled and any(
        pattern in normalized for pattern in _CRISIS_PATTERNS
    ):
        return SafetyDecision(level="crisis", action="show_support")
    return SafetyDecision(level="normal", action="continue")


def crisis_support_message() -> str:
    if settings.crisis_support_message.strip():
        return settings.crisis_support_message.strip()

    region = settings.crisis_region.strip()
    region_label = "当地" if region in {"", "CN"} else region
    return (
        "你描述的内容可能涉及紧急安全风险。请优先确保自己处于安全环境，尽快联系"
        f"{region_label}急救服务、危机支持热线或身边可信任的人。如果危险正在发生，请不要"
        "独处，并立即联系当地紧急服务。这个系统不能替代紧急援助或专业评估。"
    )
