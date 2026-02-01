"""Load agent traces from JSONL files."""

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Union


def load_traces(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load traces from a JSONL file. One JSON object per line."""
    traces = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            traces.append(json.loads(line))
    return traces


def iter_traces(path: Union[str, Path]) -> Iterator[Dict[str, Any]]:
    """Iterate over traces from a JSONL file without loading all into memory."""
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)
