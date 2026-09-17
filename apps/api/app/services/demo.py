import hashlib
import math
import re
from collections import Counter

from app.vectorstores.base import SearchResult

_WORD_RE = re.compile(r"[a-z0-9]+")
_CJK_RE = re.compile(r"[\u3400-\u9fff]")
_SENTENCE_RE = re.compile(r"(?<=[。！？.!?])\s*")


def _features(text: str) -> Counter[str]:
    normalized = " ".join(text.casefold().split())
    features = _WORD_RE.findall(normalized)
    cjk = _CJK_RE.findall(normalized)
    features.extend(cjk)
    features.extend(
        "".join(cjk[index : index + size])
        for size in (2, 3)
        for index in range(max(0, len(cjk) - size + 1))
    )
    return Counter(features)


def embed_text(text: str, dimension: int) -> list[float]:
    vector = [0.0] * dimension
    for feature, count in _features(text).items():
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, byteorder="big", signed=False)
        index = value % dimension
        sign = 1.0 if value & 1 else -1.0
        vector[index] += sign * float(count)

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def build_demo_answer(
    question: str,
    sources: list[SearchResult],
    mode: str = "psychoeducation",
) -> str:
    if not sources:
        return "当前文档中没有找到足够依据回答这个问题。"

    question_features = set(_features(question))
    selected: list[str] = []
    for source_index, source in enumerate(sources[:3], start=1):
        normalized_content = _normalize_content(source.content)
        sentences = [
            sentence.strip()
            for sentence in _SENTENCE_RE.split(normalized_content)
            if sentence.strip()
        ]
        if not sentences:
            continue

        ranked = []
        for sentence_index, sentence in enumerate(sentences):
            if _is_question_echo(sentence, question_features):
                continue
            overlap = len(question_features & set(_features(sentence)))
            ranked.append((overlap, -len(sentence), sentence_index, sentence))

        ranked.sort(reverse=True)
        if not ranked:
            continue
        best_score = ranked[0][0]
        relevance_floor = max(1, int(best_score * 0.6))
        take = 3 if source_index == 1 else 1
        for score, _, _, sentence in ranked[:take]:
            if score < relevance_floor:
                continue
            excerpt = sentence[:240].rstrip()
            if excerpt:
                selected.append(f"{excerpt} [S{source_index}]")

    if not selected:
        return "当前文档中没有找到足够依据回答这个问题。"

    prefixes = {
        "psychoeducation": "根据检索到的科普资料：",
        "assessment": "根据已审核的测评资料：",
        "professional": "根据检索到的专业资料：",
    }
    prefix = prefixes.get(mode, "根据检索到的资料：")
    return f"{prefix}\n\n" + "\n\n".join(selected[:4])


def _is_question_echo(sentence: str, question_features: set[str]) -> bool:
    normalized = sentence.strip()
    if normalized.endswith(("？", "?")):
        return True
    sentence_features = set(_features(normalized))
    if not sentence_features or not question_features:
        return False
    coverage = len(question_features & sentence_features) / len(question_features)
    return coverage >= 0.8 and len(normalized) <= len("".join(question_features)) * 3


def _normalize_content(text: str) -> str:
    normalized = " ".join(text.split())
    normalized = re.sub(r"(?<=[，。！？；：、])\s+", "", normalized)
    return re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])", "", normalized)
