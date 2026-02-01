"""Tests for trace_loader."""
import json
import tempfile
from pathlib import Path

import pytest

from src.trace_loader import load_traces, iter_traces


def test_load_traces_empty_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write("")
    try:
        assert load_traces(f.name) == []
    finally:
        Path(f.name).unlink()


def test_load_traces_single():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write('{"trace_id": "tr_1", "request": "hello"}\n')
    try:
        traces = load_traces(f.name)
        assert len(traces) == 1
        assert traces[0]["trace_id"] == "tr_1"
        assert traces[0]["request"] == "hello"
    finally:
        Path(f.name).unlink()


def test_load_traces_multiple():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write('{"trace_id": "tr_1"}\n')
        f.write('{"trace_id": "tr_2"}\n')
        f.write("\n")
    try:
        traces = load_traces(f.name)
        assert len(traces) == 2
        assert traces[0]["trace_id"] == "tr_1"
        assert traces[1]["trace_id"] == "tr_2"
    finally:
        Path(f.name).unlink()


def test_iter_traces():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write('{"trace_id": "a"}\n{"trace_id": "b"}\n')
    try:
        it = iter_traces(f.name)
        first = next(it)
        assert first["trace_id"] == "a"
        second = next(it)
        assert second["trace_id"] == "b"
        with pytest.raises(StopIteration):
            next(it)
    finally:
        Path(f.name).unlink()
