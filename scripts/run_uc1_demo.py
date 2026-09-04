"""Manual demo runner for UC1: Application Degradation scenario.

Run this script when the GreenNode environment is properly configured:

    python scripts/run_uc1_demo.py
"""

import os
import sys

# Ensure the project root is on sys.path so `agent` (and `tools`, `knowledge`)
# can be imported when running this script directly from the scripts/ folder.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force UTF-8 output so Vietnamese characters print correctly on Windows (cp1252).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from agent.orchestrator import IOOperationsOrchestrator


def main():
    user_question = (
        "Internet Banking đang chậm từ khoảng 14:00 ngày 2026-08-25. "
        "Kiểm tra giúp tôi nguyên nhân có thể nằm ở đâu?"
    )

    print("=" * 70)
    print("UC1: Application Degradation — Demo Runner")
    print("=" * 70)
    print()
    print("User Question:")
    print(user_question)
    print()
    print("-" * 70)
    print()

    result = IOOperationsOrchestrator().run(user_question)

    if result.get("status") == "ok":
        print("GreenNode Response:")
        print()
        print(result.get("response", ""))
    else:
        print(f"Orchestration failed: {result.get('message', 'Unknown error')}")

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()