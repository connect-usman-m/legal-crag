import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.pipelines.naive_rag import answer_question

QUESTIONS = [
    "Within how many hours must a controller notify a personal data breach?",
    "What are the lawful bases for processing personal data?",
    "What is the maximum administrative fine under the GDPR?",
    "When must a controller designate a data protection officer?",
    "What is the right to erasure?",
]


def main() -> None:
    for question in QUESTIONS:
        result = answer_question(question)
        print(question)
        print(f"  sources: {[s['metadata']['citation_label'] for s in result['sources']]}")
        print(f"  answer: {result['answer'][:240]}")
        print()


if __name__ == "__main__":
    raise SystemExit(main())
