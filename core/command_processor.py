from __future__ import annotations

import re

from loguru import logger

from core.command_schema import StructuredCommand


class CommandProcessor:
    """
    Omnix V5 Command Processor

    Responsibilities
    ----------------

    • Normalize user text

    • Extract entities

    • Extract parameters

    • Build StructuredCommand

    This class NEVER creates execution plans.
    """

    AUTOMATION_KEYWORDS = {
        "open",
        "close",
        "launch",
        "run",
        "click",
        "press",
        "type",
        "write",
        "scroll",
        "move",
        "drag",
        "copy",
        "paste",
        "delete",
        "rename",
        "search",
        "play",
        "pause",
        "stop",
        "next",
        "previous",
        "switch",
        "focus",
        "maximize",
        "minimize",
        "restore",
        "shutdown",
        "restart",
        "lock",
    }

    CHAT_PREFIXES = (
        "what ",
        "why ",
        "when ",
        "where ",
        "who ",
        "how ",
        "explain ",
        "tell me ",
        "can you tell me ",
        "could you tell me ",
    )

    def __init__(
        self,
    ):

        logger.info("[CommandProcessor] Initialized")

        # =====================================================

    # Public API
    # =====================================================

    def process(
        self,
        text: str,
    ) -> StructuredCommand:

        text = self._clean_command(text)

        command = self.parse_command(text)

        command.original_text = text
        command.normalized_text = text

        command.entities = self.extract_entities(text)
        command.parameters = self.extract_parameters(text)

        return command

    # =====================================================
    # Command Parsing
    # =====================================================

    def parse_command(
        self,
        text: str,
    ) -> StructuredCommand:
        """
        Parse raw text into a StructuredCommand.

        This method NEVER creates execution plans.
        """

        command = StructuredCommand()

        if not text:

            command.intent = "unknown"
            command.confidence = 0.0
            return command

        text = self._clean_command(text)

        command.original_text = text

        # -------------------------------------------------
        # Intent
        # -------------------------------------------------

        if self.looks_like_automation(text):

            command.intent = "automation"
            command.confidence = 0.95

        else:

            command.intent = "chat"
            command.confidence = 0.90

            return command

        # -------------------------------------------------
        # Action
        # -------------------------------------------------

        words = text.split()

        if words:

            command.action = words[0]

        # -------------------------------------------------
        # Target
        # -------------------------------------------------

        command.target = self._extract_target(text)

        # -------------------------------------------------
        # Application
        # -------------------------------------------------

        app = self._extract_application(text)

        if app:

            command.application = app

        # -------------------------------------------------
        # Query
        # -------------------------------------------------

        query = self._extract_query(text)

        if query:

            command.query = query

        # -------------------------------------------------
        # Text
        # -------------------------------------------------

        typed_text = self._extract_text(text)

        if typed_text:

            command.text = typed_text

        # -------------------------------------------------
        # Direction
        # -------------------------------------------------

        direction = self._extract_direction(text)

        if direction:

            command.arguments["direction"] = direction

        # -------------------------------------------------
        # Entities
        # -------------------------------------------------

        command.entities = self.extract_entities(text)

        # -------------------------------------------------
        # Parameters
        # -------------------------------------------------

        command.parameters = self.extract_parameters(text)

        logger.debug(f"[CommandProcessor] Parsed: {command}")

        return command

    # =====================================================
    # Entity Extraction
    # =====================================================

    def extract_entities(
        self,
        text: str,
    ) -> dict:

        entities = {}

        app = self._extract_application(text)

        if app:
            entities["application"] = app

        target = self._extract_target(text)

        if target:
            entities["target"] = target

        recipient = self._extract_recipient(text)

        if recipient:
            entities["recipient"] = recipient

        direction = self._extract_direction(text)

        if direction:
            entities["direction"] = direction

        return entities

    # =====================================================
    # Parameter Extraction
    # =====================================================

    def extract_parameters(
        self,
        text: str,
    ) -> dict:

        parameters = {}

        query = self._extract_query(text)

        if query:
            parameters["query"] = query

        typed = self._extract_text(text)

        if typed:
            parameters["text"] = typed

        return parameters

    # =====================================================
    # Target
    # =====================================================

    def _extract_target(
        self,
        text: str,
    ) -> str | None:

        patterns = [
            r"(?:click|tap)\s+(.+)",
            r"(?:open|launch|run)\s+(.+)",
            r"(?:close|exit)\s+(.+)",
            r"(?:focus|switch to)\s+(.+)",
        ]

        for pattern in patterns:

            match = re.match(
                pattern,
                text,
            )

            if match:

                return self._clean_parameter(match.group(1))

        return None

    # =====================================================
    # Application
    # =====================================================

    def _extract_application(
        self,
        text: str,
    ) -> str | None:

        match = re.match(
            r"(?:open|launch|run|start|close|exit|quit)\s+(.+)",
            text,
        )

        if not match:
            return None

        return self._clean_parameter(match.group(1))

    # =====================================================
    # Query
    # =====================================================

    def _extract_query(
        self,
        text: str,
    ) -> str | None:

        match = re.match(
            r"(?:search|google|look up)\s+(?:for\s+)?(.+)",
            text,
        )

        if not match:
            return None

        return self._clean_parameter(match.group(1))

    # =====================================================
    # Typed Text
    # =====================================================

    def _extract_text(
        self,
        text: str,
    ) -> str | None:

        match = re.match(
            r"(?:type|write)\s+(.+)",
            text,
        )

        if not match:
            return None

        return self._clean_parameter(match.group(1))

    # =====================================================
    # Recipient
    # =====================================================

    def _extract_recipient(
        self,
        text: str,
    ) -> str | None:

        match = re.search(
            r"\bto\s+(.+)$",
            text,
        )

        if not match:
            return None

        return self._clean_parameter(match.group(1))

    # =====================================================
    # Direction
    # =====================================================

    def _extract_direction(
        self,
        text: str,
    ) -> str | None:

        for direction in (
            "up",
            "down",
            "left",
            "right",
        ):

            if direction in text:

                return direction

        return None

    # =====================================================
    # Automation Detection
    # =====================================================

    def looks_like_automation(
        self,
        text: str,
    ) -> bool:
        """
        Determine whether the text is requesting
        Omnix to perform an action.
        """

        text = self._clean_command(text)

        if not text:
            return False

        if text.startswith(self.CHAT_PREFIXES):
            return False

        words = re.findall(
            r"[a-z0-9]+",
            text,
        )

        if not words:
            return False

        return words[0] in self.AUTOMATION_KEYWORDS

    # =====================================================
    # Multi Command
    # =====================================================

    def split_commands(
        self,
        text: str,
    ) -> list[str]:
        """
        Split chained commands into individual commands.
        """

        text = self._clean_command(text)

        if not text:
            return []

        parts = re.split(
            r"\s+(?:and then|then|and)\s+",
            text,
            flags=re.IGNORECASE,
        )

        return [part.strip() for part in parts if part.strip()]

    # =====================================================
    # Validation
    # =====================================================

    def validate(
        self,
        command: StructuredCommand,
    ) -> bool:
        """
        Validate a parsed command.
        """

        if command is None:
            return False

        if not command.is_valid():
            return False

        return True

    # =====================================================
    # Command Cleaning
    # =====================================================

    def _clean_command(
        self,
        text: str,
    ) -> str:
        """
        Normalize user input.
        """

        if text is None:
            return ""

        text = str(text).strip()

        # Lowercase for intent detection
        text = text.lower()

        # Collapse multiple spaces
        text = re.sub(r"\s+", " ", text)

        return text

    # =====================================================
    # Parameter Cleaning
    # =====================================================

    def _clean_parameter(
        self,
        value: str | None,
    ) -> str | None:
        """
        Clean extracted parameter values.
        """

        if value is None:
            return None

        value = str(value).strip()

        value = value.strip("\"'")

        return value or None

    # =====================================================
    # Utilities
    # =====================================================

    def normalize(
        self,
        text: str,
    ) -> str:
        """
        Public normalization helper.
        """

        return self._clean_command(text)

    # =====================================================
    # Legacy Compatibility
    # =====================================================

    def create_simple_plan(
        self,
        text: str,
    ):
        """
        Deprecated.

        Planning now belongs to Planner.

        This method is kept temporarily so older
        V4 components don't immediately break.
        """

        logger.warning(
            "create_simple_plan() is deprecated. " "Use Planner.create_plan()."
        )

        return None

    def create_workflow_plan(
        self,
        text: str,
    ):
        """
        Deprecated.
        """

        logger.warning(
            "create_workflow_plan() is deprecated. "
            "Workflow planning belongs to Planner."
        )

        return None

    # =====================================================
    # Debug
    # =====================================================

    def __repr__(
        self,
    ) -> str:

        return "CommandProcessor()"
