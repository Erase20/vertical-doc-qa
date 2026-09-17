import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

HERE = Path(__file__).resolve().parent
DEFAULT_QUESTIONS = HERE / "questions.jsonl"


async def run_case(
    client: httpx.AsyncClient,
    base_url: str,
    case: dict[str, Any],
) -> dict[str, Any]:
    answer_parts: list[str] = []
    sources: list[dict[str, Any]] = []
    safety_level: str | None = None
    finish_reason: str | None = None

    payload = {
        "question": case["question"],
        "knowledge_base_id": "psychology",
        "mode": case["mode"],
        "filters": {},
    }
    async with client.stream("POST", f"{base_url}/chat/stream", json=payload) as response:
        response.raise_for_status()
        event_name: str | None = None
        async for line in response.aiter_lines():
            if line.startswith("event: "):
                event_name = line.removeprefix("event: ").strip()
                continue
            if not line.startswith("data: ") or event_name is None:
                continue

            data = json.loads(line.removeprefix("data: "))
            if event_name == "sources":
                sources = data["sources"]
            elif event_name == "token":
                answer_parts.append(data["delta"])
            elif event_name == "safety":
                safety_level = data["level"]
            elif event_name == "done":
                finish_reason = data["finish_reason"]
            event_name = None

    answer = "".join(answer_parts)
    source_names = {source["name"] for source in sources}
    expected_sources = set(case["expected_sources"])
    must_include = case.get("must_include", [])
    included = [value for value in must_include if value.casefold() in answer.casefold()]
    expected_safety = case.get("expected_safety", "normal")

    source_hit = (
        not expected_sources
        if expected_safety == "crisis"
        else bool(source_names & expected_sources)
    )
    safety_ok = (
        safety_level == "crisis" and finish_reason == "crisis_support"
        if expected_safety == "crisis"
        else safety_level is None
    )

    return {
        "id": case["id"],
        "mode": case["mode"],
        "source_hit": source_hit,
        "safety_ok": safety_ok,
        "must_include_coverage": len(included) / max(1, len(must_include)),
        "citation_present": expected_safety == "crisis" or "[S1]" in answer,
        "answer": answer,
    }


async def evaluate(base_url: str, questions_path: Path) -> list[dict[str, Any]]:
    cases = [
        json.loads(line)
        for line in questions_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        return [await run_case(client, base_url, case) for case in cases]


def print_summary(results: list[dict[str, Any]]) -> None:
    total = len(results)
    source_hits = sum(result["source_hit"] for result in results)
    safety_ok = sum(result["safety_ok"] for result in results)
    citation_ok = sum(result["citation_present"] for result in results)
    coverage = sum(result["must_include_coverage"] for result in results) / max(1, total)

    print(f"Cases: {total}")
    print(f"Source hit: {source_hits}/{total} ({source_hits / max(1, total):.1%})")
    print(f"Safety routing: {safety_ok}/{total} ({safety_ok / max(1, total):.1%})")
    print(f"Citation present: {citation_ok}/{total} ({citation_ok / max(1, total):.1%})")
    print(f"Must-include coverage: {coverage:.1%}")
    print()

    for result in results:
        markers = [
            "source=ok" if result["source_hit"] else "source=miss",
            "safety=ok" if result["safety_ok"] else "safety=miss",
            "citation=ok" if result["citation_present"] else "citation=miss",
            f"coverage={result['must_include_coverage']:.0%}",
        ]
        print(f"{result['id']}: {', '.join(markers)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the psychology-domain evaluation set.")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8100/api/v1",
        help="FastAPI base URL including /api/v1.",
    )
    parser.add_argument(
        "--questions",
        type=Path,
        default=DEFAULT_QUESTIONS,
        help="Path to the JSONL question set.",
    )
    args = parser.parse_args()

    results = asyncio.run(evaluate(args.base_url.rstrip("/"), args.questions))
    print_summary(results)


if __name__ == "__main__":
    main()
