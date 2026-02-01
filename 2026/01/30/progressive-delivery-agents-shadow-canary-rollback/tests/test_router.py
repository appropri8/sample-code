"""Tests for feature-flagged router."""
import pytest

from src.router import RouterConfig, RouterMode, route, rollback_config


def test_rollback_config():
    config = rollback_config()
    assert config.mode == RouterMode.BASELINE
    assert config.canary_percent == 0.0
    assert not config.should_use_new_agent("any_id")
    assert not config.new_agent_can_execute()


def test_baseline_mode():
    config = RouterConfig(mode=RouterMode.BASELINE)
    assert route("req_1", config) == "baseline"
    assert route("req_2", config) == "baseline"


def test_shadow_mode():
    config = RouterConfig(mode=RouterMode.SHADOW)
    # Router returns baseline for "who executes"; caller runs both
    assert route("req_1", config) == "baseline"
    assert config.should_use_new_agent("req_1")
    assert not config.new_agent_can_execute()


def test_canary_mode_deterministic():
    config = RouterConfig(mode=RouterMode.CANARY, canary_percent=50.0)
    # Same request_id always gets same route
    r1 = route("same_id", config)
    r2 = route("same_id", config)
    assert r1 == r2
    assert config.new_agent_can_execute()
