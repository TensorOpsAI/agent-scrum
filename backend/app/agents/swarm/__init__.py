"""
Manager-Worker Agent Swarm - Multi-agent orchestration via A2A communication.

This module provides the swarm orchestration layer that coordinates
all agents using a Manager-Worker topology with visible A2A messages.
"""
from .graph import ScrumSwarm

__all__ = ["ScrumSwarm"]
