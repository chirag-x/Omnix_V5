"""
Omnix V5 Click Skill

Performs mouse click operations.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.built_in.input.input_skill import InputSkill
from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult


class ClickSkill(InputSkill):
    """
    Perform mouse click operations.

    Supported targets:

    • Screen coordinates
    • Vision target
    • Browser element
    • Current mouse position

    Supported buttons:

    • left
    • right
    • middle

    Supported click types:

    • single
    • double
    """

    metadata = SkillMetadata(
        id="builtin.input.click",
        name="click",
        description="Click at a screen position using the mouse.",
        category="input",
        aliases=[
            "click",
            "mouse click",
        ],
        tags=[
            "mouse",
            "input",
            "click",
            "automation",
        ],
        priority=20,
    )

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    async def validate(
        self,
        context: SkillContext,
    ) -> None:

        button = self.parameter(
            context,
            "button",
            "left",
        )

        if button not in (
            "left",
            "right",
            "middle",
        ):
            raise ValueError(f"Unsupported mouse button '{button}'.")

        clicks = self.parameter(
            context,
            "clicks",
            1,
        )

        if clicks < 1:
            raise ValueError("Clicks must be greater than zero.")

    # --------------------------------------------------
    # Execute
    # --------------------------------------------------

    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        input_service = self.input(context)

        if input_service is None:
            return self.failure("Input service is unavailable.")

        button = self.parameter(
            context,
            "button",
            "left",
        )

        clicks = self.parameter(
            context,
            "clicks",
            1,
        )

        interval = self.parameter(
            context,
            "interval",
            0.1,
        )

        move_first = self.parameter(
            context,
            "move",
            True,
        )

        x = self.entity(
            context,
            "x",
        )

        y = self.entity(
            context,
            "y",
        )

        target = self.entity(
            context,
            "target",
        )

        browser_element = self.entity(
            context,
            "browser_element",
        )

        self.log_info(
            context,
            "Preparing click operation.",
        )
        # --------------------------------------------------
        # Resolve Click Target
        # --------------------------------------------------

        # Case 1
        # Click explicit screen coordinates.

        if x is not None and y is not None:

            self.log_info(
                context,
                f"Using coordinates ({x}, {y}).",
            )

            if move_first:

                await input_service.move_mouse(
                    x=x,
                    y=y,
                )

                await self.human_delay()

        # --------------------------------------------------
        # Case 2
        # Browser element.
        # --------------------------------------------------

        elif browser_element is not None:

            self.log_info(
                context,
                f"Resolving browser element '{browser_element}'.",
            )

            browser = self.browser(context)

            if browser is None:
                return self.failure("Browser service is unavailable.")

            success = await browser.click(
                browser_element,
                button=button,
                clicks=clicks,
                interval=interval,
            )

            if not success:

                return self.failure(
                    f"Unable to click browser element '{browser_element}'."
                )

            return self.success(
                message="Browser element clicked.",
                data={
                    "button": button,
                    "clicks": clicks,
                    "element": browser_element,
                },
            )

        # --------------------------------------------------
        # Case 3
        # Vision target.
        # --------------------------------------------------

        elif target is not None:

            self.log_info(
                context,
                f"Searching for target '{target}'.",
            )

            vision = self.vision(context)

            if vision is None:

                return self.failure("Vision service is unavailable.")

            location = await vision.find_target(
                target,
            )

            if location is None:

                return self.failure(f"Target '{target}' not found.")

            x = location.x
            y = location.y

            self.log_info(
                context,
                f"Target resolved to ({x}, {y}).",
            )

            if move_first:

                await input_service.move_mouse(
                    x=x,
                    y=y,
                )

                await self.human_delay()

        # --------------------------------------------------
        # Case 4
        # Current cursor position.
        # --------------------------------------------------

        else:

            self.log_info(
                context,
                "Using current mouse position.",
            )
        # --------------------------------------------------
        # Execute Click
        # --------------------------------------------------

        try:

            offset_x = self.parameter(
                context,
                "offset_x",
                0,
            )

            offset_y = self.parameter(
                context,
                "offset_y",
                0,
            )

            humanize = self.parameter(
                context,
                "humanize",
                True,
            )

            if move_first and x is not None and y is not None:

                x += offset_x
                y += offset_y

                if humanize:

                    dx, dy = self.random_offset(2)

                    x += dx
                    y += dy

                await input_service.move_mouse(
                    x=x,
                    y=y,
                )

                await self.human_delay()

            # ------------------------------------------
            # Retry click operation
            # ------------------------------------------

            await self.retry(
                input_service.click,
                button=button,
                clicks=clicks,
                interval=interval,
                attempts=self.parameter(
                    context,
                    "attempts",
                    3,
                ),
                delay=0.15,
            )

            self.log_info(
                context,
                (f"Mouse click completed " f"({button}, {clicks})."),
            )

            result_data = {
                "button": button,
                "clicks": clicks,
                "position": (
                    x,
                    y,
                ),
                "target": target,
                "browser_element": browser_element,
            }

            return self.success(
                message="Click completed successfully.",
                data=result_data,
            )

        except TimeoutError:

            return self.failure(
                "Click operation timed out.",
            )

        except Exception as error:

            return self.failure(
                message=str(error),
            )

    # --------------------------------------------------
    # Execution Conditions
    # --------------------------------------------------

    async def can_execute(
        self,
        context: SkillContext,
    ) -> bool:
        """
        Determine whether the click skill can execute.
        """

        if not self.enabled:
            return False

        if self.input(context) is None:
            return False

        return True

    # --------------------------------------------------
    # Before Execute
    # --------------------------------------------------

    async def before_execute(
        self,
        context: SkillContext,
    ) -> None:

        self.log_info(
            context,
            "Starting ClickSkill.",
        )

    # --------------------------------------------------
    # After Execute
    # --------------------------------------------------

    async def after_execute(
        self,
        context: SkillContext,
        result: SkillResult,
    ) -> None:

        self.log_info(
            context,
            (f"ClickSkill finished " f"({result.success})."),
        )

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    async def cleanup(
        self,
    ) -> None:
        """
        Cleanup resources if required.

        Currently nothing to release.
        """

        return
