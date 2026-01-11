"""
Looper: Supervised work loop for Amplifier.

A pattern that keeps working on a task until a supervisor confirms completion,
with support for user input injection between iterations.
"""

from looper.orchestrator import LoopConfig, LoopResult, SupervisedLoop

__version__ = "0.1.0"
__all__ = ["SupervisedLoop", "LoopConfig", "LoopResult"]
