"""Entry point: load retrieved chunks, pack them, and print a debug report.

Run with:  python main.py
"""

import json

from packer import pack, build_prompt, debug_report, EVIDENCE_BUDGET

SYSTEM = (
    "You answer policy questions using only the retrieved evidence. "
    "Cite the source id for every claim."
)
USER_REQUEST = "What is our current refund window for annual plans?"


def main() -> None:
    with open("sample_chunks.json") as f:
        chunks = json.load(f)

    included, excluded, used = pack(chunks)
    print(debug_report(included, excluded, used))
    print("\n" + build_prompt(included, SYSTEM, USER_REQUEST))


if __name__ == "__main__":
    main()
