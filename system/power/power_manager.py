"""
Omnix V5
Power Manager

High-level power operations.
"""

from __future__ import annotations

import logging

from .power_state import PowerAction, PowerStatus

from system.services.power_controller import PowerController


logger = logging.getLogger(__name__)


class PowerManager:
    """
    High-level power management.
    """

    def __init__(
        self,
        controller: PowerController | None = None,
    ) -> None:

        self._controller = (
            controller
            or PowerController()
        )

        self._status = PowerStatus.AVAILABLE


    # ---------------------------------------------------------
    # Actions
    # ---------------------------------------------------------

    def execute(
        self,
        action: PowerAction,
    ) -> bool:

        self._status = PowerStatus.EXECUTING

        try:

            if action == PowerAction.SHUTDOWN:

                result = self._controller.shutdown()


            elif action == PowerAction.RESTART:

                result = self._controller.restart()


            elif action == PowerAction.SLEEP:

                result = self._controller.sleep()


            elif action == PowerAction.HIBERNATE:

                result = self._controller.hibernate()


            elif action == PowerAction.LOCK:

                result = self._controller.lock()


            elif action == PowerAction.LOGOFF:

                result = self._controller.logoff()


            else:

                result = False


            self._status = (
                PowerStatus.AVAILABLE
                if result
                else PowerStatus.FAILED
            )


            return result


        except Exception as exc:

            logger.error(
                "Power action failed: %s",
                exc,
            )

            self._status = PowerStatus.FAILED

            return False


    # ---------------------------------------------------------
    # Convenience Methods
    # ---------------------------------------------------------

    def shutdown(self) -> bool:

        return self.execute(
            PowerAction.SHUTDOWN
        )


    def restart(self) -> bool:

        return self.execute(
            PowerAction.RESTART
        )


    def sleep(self) -> bool:

        return self.execute(
            PowerAction.SLEEP
        )


    def lock(self) -> bool:

        return self.execute(
            PowerAction.LOCK
        )


    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    @property
    def status(
        self,
    ) -> PowerStatus:

        return self._status


    def statistics(
        self,
    ) -> dict:

        return {

            "status": self._status.value,

        }