"""
Flora AI Brain Package — Flora Platform
========================================
AI brain modules for the Flora chatbot assistant.

Modules:
    flora.py    — Flora AI personality and response system
    context.py  — Conversation context management
    intents.py  — Intent classification system
    prompts.py  — LLM prompt templates
    tools.py    — AI tools (calculator, search, etc.)
    main.py     — Standalone bot entry point
"""

from .flora import FloraBrain
from .context import ConversationContext, ContextManager
from .intents import IntentClassifier, IntentType
from .prompts import PromptManager
from .tools import CalculatorTool, DateTimeTool, ToolRegistry

__version__ = "1.0.0"

__all__ = [
    "FloraBrain",
    "ConversationContext",
    "ContextManager",
    "IntentClassifier",
    "IntentType",
    "PromptManager",
    "CalculatorTool",
    "DateTimeTool",
    "ToolRegistry",
]
