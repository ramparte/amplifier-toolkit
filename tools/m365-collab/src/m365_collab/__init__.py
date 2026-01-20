"""M365 Collaboration Tool module for Amplifier.

Enables AI agent instances to collaborate across sessions via SharePoint.
"""

from .tool import M365CollabTool, execute, get_tool_definition

# Amplifier module convention: export as 'Tool'
Tool = M365CollabTool

__all__ = ["M365CollabTool", "Tool", "execute", "get_tool_definition"]
__version__ = "0.1.0"
