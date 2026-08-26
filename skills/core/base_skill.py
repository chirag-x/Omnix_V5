"""
Omnix V5 Base Skill

Every skill inside Omnix inherits from this class.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

import asyncio
import random
from abc import ABC, abstractmethod
from time import perf_counter
from typing import Any, Awaitable, Callable

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult


class BaseSkill(ABC):
    """
    Base class for every Omnix skill.

    This class provides:

    - Lifecycle management
    - Validation
    - Execution pipeline
    - Retry helpers
    - Timeout helpers
    - Logging helpers
    - Context shortcuts
    - Metrics
    """

    metadata: SkillMetadata

    def __init__(self) -> None:

        if not hasattr(self, "metadata"):
            raise ValueError(f"{self.__class__.__name__} " "must define metadata")

        # --------------------------------------------------
        # Runtime State
        # --------------------------------------------------

        self.enabled = True

        # --------------------------------------------------
        # Metrics
        # --------------------------------------------------

        self.execution_count = 0

        self.success_count = 0

        self.failure_count = 0

        self.last_execution_time = 0.0

        self.last_error: str | None = None

    # ==================================================
    # Context Shortcuts
    # ==================================================

    def entity(
        self,
        context: SkillContext,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Get an extracted entity.
        """
        return context.entity(name, default)

    def parameter(
        self,
        context: SkillContext,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Get a runtime parameter.
        """
        return context.parameter(name, default)

    def require_entity(
        self,
        context: SkillContext,
        name: str,
    ) -> Any:
        """
        Return a required entity.

        Raises:
            ValueError
        """

        value = context.entity(name)

        if value is None:
            raise ValueError(f"Missing required entity '{name}'.")

        return value

    def require_parameter(
        self,
        context: SkillContext,
        name: str,
    ) -> Any:

        value = context.parameter(name)

        if value is None:
            raise ValueError(f"Missing required parameter '{name}'.")

        return value

    # ==================================================
    # Service Shortcuts
    # ==================================================

    def browser(self, context: SkillContext):
        return context.browser

    def automation(self, context: SkillContext):
        return context.automation

    def vision(self, context: SkillContext):
        return context.vision

    def memory(self, context: SkillContext):
        return context.memory

    def planner(self, context: SkillContext):
        return context.planner

    def input(self, context: SkillContext):
        return context.input

    def system(self, context: SkillContext):
        return context.system

    def ai(self, context: SkillContext):
        return context.ai

    def config(self, context: SkillContext):
        return context.config

    # ==================================================
    # Logging Helpers
    # ==================================================

    def log_debug(
        self,
        context: SkillContext,
        message: str,
    ) -> None:

        if context.logger:
            context.logger.debug(message)

    def log_info(
        self,
        context: SkillContext,
        message: str,
    ) -> None:

        if context.logger:
            context.logger.info(message)

    def log_warning(
        self,
        context: SkillContext,
        message: str,
    ) -> None:

        if context.logger:
            context.logger.warning(message)

    def log_error(
        self,
        context: SkillContext,
        message: str,
    ) -> None:

        if context.logger:
            context.logger.error(message)

    # ==================================================
    # Result Helpers
    # ==================================================

    def success(
        self,
        message: str = "",
        data: Any = None,
        **kwargs,
    ) -> SkillResult:

        return SkillResult.success_result(
            message=message,
            data=data,
            **kwargs,
        )

    def failure(
        self,
        message: str,
        **kwargs,
    ) -> SkillResult:

        return SkillResult.failure(
            message=message,
            **kwargs,
        )

        # ==================================================

    # Lifecycle
    # ==================================================

    async def initialize(self) -> None:
        """
        Called once when the skill is loaded.
        """
        return

    async def cleanup(self) -> None:
        """
        Called once when Omnix shuts down.
        """
        return

    # ==================================================
    # Validation
    # ==================================================

    async def can_execute(
        self,
        context: SkillContext,
    ) -> bool:
        """
        Determines whether this skill can execute.

        Override in child classes when required.
        """
        return True

    async def validate(
        self,
        context: SkillContext,
    ) -> None:
        """
        Validate the execution context.

        Raise an exception if validation fails.
        """
        return

    # ==================================================
    # Hooks
    # ==================================================

    async def before_execute(
        self,
        context: SkillContext,
    ) -> None:
        """
        Executed before execute().
        """
        return

    async def after_execute(
        self,
        context: SkillContext,
        result: SkillResult,
    ) -> None:
        """
        Executed after execute().
        """
        return

    # ==================================================
    # Timing Helpers
    # ==================================================

    async def delay(
        self,
        seconds: float,
    ) -> None:
        """
        Delay execution.
        """

        if seconds > 0:
            await asyncio.sleep(seconds)

    async def human_delay(
        self,
        minimum: float = 0.05,
        maximum: float = 0.20,
    ) -> None:
        """
        Simulate a human reaction delay.
        """

        await asyncio.sleep(
            random.uniform(
                minimum,
                maximum,
            )
        )

    # ==================================================
    # Timeout Helper
    # ==================================================

    async def with_timeout(
        self,
        coroutine: Awaitable[Any],
        timeout: float,
    ) -> Any:
        """
        Execute a coroutine with a timeout.
        """

        return await asyncio.wait_for(
            coroutine,
            timeout=timeout,
        )

    # ==================================================
    # Retry Helper
    # ==================================================

    async def retry(
        self,
        function: Callable[..., Awaitable[Any]],
        *args,
        attempts: int = 3,
        delay: float = 0.0,
        exceptions: tuple[type[Exception], ...] = (Exception,),
        **kwargs,
    ) -> Any:
        """
        Retry an async operation.

        Example:

            await self.retry(
                self.input(context).click,
                x=100,
                y=200,
                attempts=5,
            )
        """

        last_error = None

        for attempt in range(1, attempts + 1):

            try:

                return await function(
                    *args,
                    **kwargs,
                )

            except exceptions as error:

                last_error = error

                if attempt >= attempts:
                    break

                if delay > 0:
                    await asyncio.sleep(delay)

        if last_error:
            raise last_error

        raise RuntimeError("Retry failed without exception.")

    # ==================================================
    # Random Helpers
    # ==================================================

    def random_offset(
        self,
        radius: int = 5,
    ) -> tuple[int, int]:
        """
        Generate a random offset.

        Useful for human-like mouse movement.
        """

        return (
            random.randint(
                -radius,
                radius,
            ),
            random.randint(
                -radius,
                radius,
            ),
        )

    def random_float(
        self,
        minimum: float,
        maximum: float,
    ) -> float:
        """
        Random float helper.
        """

        return random.uniform(
            minimum,
            maximum,
        )

    # ==================================================
    # Main Skill
    # ==================================================

    @abstractmethod
    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:
        """
        Main skill implementation.
        """
        raise NotImplementedError

    # ==================================================
    # Runner
    # ==================================================

    async def run(
        self,
        context: SkillContext,
    ) -> SkillResult:
        """
        Internal execution pipeline.

        Handles:

        - Skill enable/disable
        - Validation
        - Lifecycle hooks
        - Metrics
        - Timing
        - Exception handling
        """

        start_time = perf_counter()

        self.execution_count += 1

        self.last_error = None

        result: SkillResult | None = None

        try:

            # ------------------------------------------
            # Enabled
            # ------------------------------------------

            if not self.enabled:

                result = self.failure(
                    message="Skill is disabled.",
                )

                return result

            # ------------------------------------------
            # Can Execute
            # ------------------------------------------

            can_execute = await self.can_execute(
                context,
            )

            if not can_execute:

                result = self.failure(
                    message="Skill cannot execute.",
                )

                return result

            # ------------------------------------------
            # Validation
            # ------------------------------------------

            await self.validate(
                context,
            )

            # ------------------------------------------
            # Before Hook
            # ------------------------------------------

            await self.before_execute(
                context,
            )

            # ------------------------------------------
            # Execute
            # ------------------------------------------

            result = await self.execute(
                context,
            )

            if result is None:

                raise RuntimeError(f"{self.__class__.__name__} returned None.")

            # ------------------------------------------
            # After Hook
            # ------------------------------------------

            await self.after_execute(
                context,
                result,
            )

            self.success_count += 1

        except asyncio.CancelledError:

            raise

        except Exception as error:

            self.failure_count += 1

            self.last_error = str(error)

            self.log_error(
                context,
                str(error),
            )

            result = self.failure(
                message=str(error),
                error=str(error),
                exception=error,
            )

        # ------------------------------------------
        # Metrics
        # ------------------------------------------

        execution_time = perf_counter() - start_time

        self.last_execution_time = execution_time

        if result is not None:

            result.execution_time = execution_time

        self.log_info(
            context,
            (f"{self.__class__.__name__} " f"finished in " f"{execution_time:.3f}s"),
        )

        return result

    # ==================================================
    # Statistics
    # ==================================================

    @property
    def success_rate(
        self,
    ) -> float:

        if self.execution_count == 0:
            return 0.0

        return (self.success_count / self.execution_count) * 100

    def reset_metrics(
        self,
    ) -> None:

        self.execution_count = 0

        self.success_count = 0

        self.failure_count = 0

        self.last_execution_time = 0.0

        self.last_error = None
