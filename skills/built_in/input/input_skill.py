"""
Omnix V5 Input Skill Base

Base class for mouse and keyboard related skills.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from abc import ABC

from skills.core.base_skill import BaseSkill
from skills.core.skill_context import SkillContext


class InputSkill(BaseSkill, ABC):
    """
    Base class for all input-related skills.

    All input operations are delegated to the
    InputManager through SkillContext.
    """

    # =====================================================
    # Mouse Helpers
    # =====================================================

    async def move_mouse(
        self,
        context: SkillContext,
        x: int,
        y: int,
    ) -> bool:
        """
        Move mouse cursor.
        """

        return await context.input.move_mouse(
            x=x,
            y=y,
        )

    async def click(
        self,
        context: SkillContext,
        x: int,
        y: int,
        button: str = "left",
    ) -> bool:
        """
        Click mouse button.
        """

        return await context.input.click(
            x=x,
            y=y,
            button=button,
        )

    async def double_click(
        self,
        context: SkillContext,
        x: int,
        y: int,
    ) -> bool:
        """
        Double click.
        """

        return await context.input.double_click(
            x=x,
            y=y,
        )

    async def right_click(
        self,
        context: SkillContext,
        x: int,
        y: int,
    ) -> bool:
        """
        Right click.
        """

        return await context.input.click(
            x=x,
            y=y,
            button="right",
        )

    async def drag(
        self,
        context: SkillContext,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
    ) -> bool:
        """
        Drag mouse.
        """

        return await context.input.drag(
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
        )

    # =====================================================
    # Keyboard Helpers
    # =====================================================

    async def type_text(
        self,
        context: SkillContext,
        text: str,
    ) -> bool:
        """
        Type text.
        """

        return await context.input.type_text(text)

    async def press_key(
        self,
        context: SkillContext,
        key: str,
    ) -> bool:
        """
        Press keyboard key.
        """

        return await context.input.press_key(key)

    async def hotkey(
        self,
        context: SkillContext,
        *keys: str,
    ) -> bool:
        """
        Execute keyboard shortcut.
        """

        return await context.input.hotkey(*keys)

    # =====================================================
    # Scroll
    # =====================================================

    async def scroll(
        self,
        context: SkillContext,
        amount: int,
    ) -> bool:
        """
        Scroll page.
        """

        return await context.input.scroll(amount)
