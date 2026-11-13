
"""
HRMS AI Tool Registry
=====================

Purpose:
    Central registry for all available HRMS AI tools.

Responsibilities:
    1. Register tool definitions.
    2. Register executable backend handlers.
    3. Prevent duplicate tool registrations.
    4. Retrieve tools by name.
    5. Filter tools by category.
    6. Expose only implemented tools to Gemini.

Security:
    A tool definition alone does not make a tool executable.
    A backend handler must be registered before the tool
    becomes available to Gemini.
"""

from collections.abc import Callable, Iterable
from typing import Any

from google.genai import types

from app.ai_tools.tool_definitions import (
    TOOL_DEFINITIONS,
    ToolDefinition,
    get_all_tool_definitions,
)


# ============================================================
# REGISTRY EXCEPTIONS
# ============================================================

class ToolRegistryError(Exception):
    """Base exception for tool registry operations."""


class DuplicateToolError(ToolRegistryError):
    """Raised when a tool is registered more than once."""


class UnknownToolError(ToolRegistryError):
    """Raised when a requested tool does not exist."""


class ToolHandlerNotRegisteredError(ToolRegistryError):
    """Raised when a tool has no executable backend handler."""


# ============================================================
# TOOL HANDLER TYPE
# ============================================================

ToolHandler = Callable[..., Any]


# ============================================================
# TOOL REGISTRY
# ============================================================

class ToolRegistry:
    """
    Central catalogue of AI tool definitions and handlers.

    Definitions describe what Gemini can request.

    Handlers implement what the backend can actually execute.
    """

    def __init__(
        self,
        definitions: Iterable[ToolDefinition] | None = None,
    ):

        self._definitions: dict[str, ToolDefinition] = {}

        self._handlers: dict[str, ToolHandler] = {}

        if definitions is not None:

            for definition in definitions:
                self.register_definition(definition)

    # ========================================================
    # REGISTER TOOL DEFINITION
    # ========================================================

    def register_definition(
        self,
        definition: ToolDefinition,
    ) -> None:
        """
        Register a tool definition.

        Duplicate names are rejected.
        """

        if definition.name in self._definitions:

            raise DuplicateToolError(
                f"Tool '{definition.name}' is already registered."
            )

        if not definition.name.strip():

            raise ValueError(
                "Tool name cannot be empty."
            )

        if not definition.required_permissions:

            raise ValueError(
                f"Tool '{definition.name}' must declare "
                "at least one required permission."
            )

        self._definitions[definition.name] = definition

    # ========================================================
    # REGISTER BACKEND HANDLER
    # ========================================================

    def register_handler(
        self,
        tool_name: str,
        handler: ToolHandler,
    ) -> None:
        """
        Register an executable backend handler.

        The corresponding tool definition must exist first.
        """

        if tool_name not in self._definitions:

            raise UnknownToolError(
                f"Cannot register handler for unknown tool: "
                f"{tool_name}"
            )

        if not callable(handler):

            raise TypeError(
                f"Handler for '{tool_name}' must be callable."
            )

        if tool_name in self._handlers:

            raise DuplicateToolError(
                f"A handler for '{tool_name}' "
                "is already registered."
            )

        self._handlers[tool_name] = handler

    # ========================================================
    # RETRIEVE TOOL DEFINITION
    # ========================================================

    def get_definition(
        self,
        tool_name: str,
    ) -> ToolDefinition:

        definition = self._definitions.get(tool_name)

        if definition is None:

            raise UnknownToolError(
                f"Unknown AI tool: {tool_name}"
            )

        return definition

    # ========================================================
    # RETRIEVE BACKEND HANDLER
    # ========================================================

    def get_handler(
        self,
        tool_name: str,
    ) -> ToolHandler:

        self.get_definition(tool_name)

        handler = self._handlers.get(tool_name)

        if handler is None:

            raise ToolHandlerNotRegisteredError(
                f"No executable handler registered for "
                f"'{tool_name}'."
            )

        return handler

    # ========================================================
    # CHECK WHETHER TOOL IS EXECUTABLE
    # ========================================================

    def is_executable(
        self,
        tool_name: str,
    ) -> bool:

        return (
            tool_name in self._definitions
            and tool_name in self._handlers
        )

    # ========================================================
    # LIST ALL TOOL DEFINITIONS
    # ========================================================

    def list_definitions(self) -> list[ToolDefinition]:

        return list(self._definitions.values())

    # ========================================================
    # LIST IMPLEMENTED TOOLS
    # ========================================================

    def list_executable_tools(
        self,
        category: str | None = None,
    ) -> list[ToolDefinition]:
        """
        Return only definitions with registered handlers.

        This method determines which tools can be exposed
        to Gemini.
        """

        tools = [
            definition
            for name, definition in self._definitions.items()
            if name in self._handlers
        ]

        if category is not None:

            tools = [
                tool
                for tool in tools
                if tool.category == category
            ]

        return tools

    # ========================================================
    # LIST REGISTERED TOOL NAMES
    # ========================================================

    def list_executable_tool_names(self) -> list[str]:

        return list(self._handlers.keys())

    # ========================================================
    # TOTAL REGISTERED DEFINITIONS
    # ========================================================

    @property
    def definition_count(self) -> int:

        return len(self._definitions)

    # ========================================================
    # TOTAL EXECUTABLE TOOLS
    # ========================================================

    @property
    def executable_count(self) -> int:

        return len(self._handlers)


# ============================================================
# GLOBAL HRMS TOOL REGISTRY
# ============================================================

tool_registry = ToolRegistry(
    definitions=TOOL_DEFINITIONS.values()
)
# ============================================================
# GEMINI FUNCTION CALLING TOOLS
# ============================================================

def build_gemini_tools(
    definitions: list[ToolDefinition],
) -> list[types.Tool]:
    """
    Convert executable backend tool definitions
    into Gemini function declarations.
    """

    if not definitions:
        return []

    function_declarations = [
        types.FunctionDeclaration(
            name=definition.name,
            description=definition.description,
            parameters_json_schema=definition.parameters,
        )
        for definition in definitions
    ]

    return [
        types.Tool(
            function_declarations=function_declarations
        )
    ]


# ============================================================
# GET GEMINI-AVAILABLE TOOLS
# ============================================================

def get_gemini_tools(
    category: str | None = None,
) -> list[types.Tool]:
    """
    Expose only tools with registered backend handlers.

    Definitions without handlers are never exposed to Gemini.
    """

    executable_definitions = (
        tool_registry.list_executable_tools(
            category=category
        )
    )

    return build_gemini_tools(executable_definitions)