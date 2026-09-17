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


def build_demo_answer(question: str, sources: list[SearchResult]) -> str:
    if not sources:
        return "当前文档中没有找到足够依据回答这个问题。"

    question_features = set(_features(question))
    selected: list[str] = []
    for index, source in enumerate(sources[:3], start=1):
        sentences = [
            sentence.strip()
            for sentence in _SENTENCE_RE.split(source.content)
            if sentence.strip()
        ]
        if not sentences:
            continue

        ranked = sorted(
            sentences,
            key=lambda sentence: (
                len(question_features & set(_features(sentence))),
                -len(sentence),
            ),
            reverse=True,
        )
        excerpt = ranked[0][:320].rstrip()
        if excerpt:
            selected.append(f"{excerpt} [S{index}]")

    if not selected:
        return "当前文档中没有找到足够依据回答这个问题。"

    return "根据检索到的资料：\n\n" + "\n\n".join(selected)
