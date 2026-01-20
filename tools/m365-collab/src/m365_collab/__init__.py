"""M365 Collaboration Tool for Amplifier.

Enables AI agent instances to collaborate across sessions via SharePoint.
"""

from .tool import M365CollabTool, execute, get_tool_definition

__all__ = ["M365CollabTool", "execute", "get_tool_definition"]
__version__ = "0.1.0"
