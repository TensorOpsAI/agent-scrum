"""Tests for the agent swarm and executor."""
import pytest
from datetime import datetime, timedelta

from app.agents.swarm.graph import is_stuck, STUCK_THRESHOLD
from app.agents.executor import executor, AGENT_CAPACITY


def test_is_stuck_returns_true_for_old_items():
    """Test that is_stuck returns True for items older than threshold."""
    old_time = datetime.utcnow() - timedelta(seconds=STUCK_THRESHOLD + 10)
    assert is_stuck(old_time) is True


def test_is_stuck_returns_false_for_recent_items():
    """Test that is_stuck returns False for recently updated items."""
    recent_time = datetime.utcnow() - timedelta(seconds=1)
    assert is_stuck(recent_time) is False


def test_is_stuck_returns_true_for_none():
    """Test that is_stuck returns True when updated_at is None."""
    assert is_stuck(None) is True


def test_is_stuck_boundary():
    """Test stuck detection at the boundary."""
    just_under = datetime.utcnow() - timedelta(seconds=STUCK_THRESHOLD - 1)
    assert is_stuck(just_under) is False

    just_over = datetime.utcnow() - timedelta(seconds=STUCK_THRESHOLD + 1)
    assert is_stuck(just_over) is True


def test_executor_has_capacity():
    """Test executor capacity checking."""
    # All defined agents should have capacity
    for agent_id in AGENT_CAPACITY.keys():
        assert executor.has_capacity(agent_id) is True


def test_executor_capacity_limits():
    """Test that agent capacity limits are defined for all core agents."""
    expected_agents = ["product_owner", "tech_lead", "developer", "code_reviewer", "qa", "scrum_master"]
    for agent_id in expected_agents:
        assert agent_id in AGENT_CAPACITY
        assert AGENT_CAPACITY[agent_id] >= 1


def test_executor_is_working_on_returns_false_initially():
    """Test that executor reports no work initially."""
    for agent_id in AGENT_CAPACITY.keys():
        assert executor.is_working_on(agent_id, "some_work_key") is False
