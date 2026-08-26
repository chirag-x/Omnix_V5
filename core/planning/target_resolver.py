from __future__ import annotations

from typing import Any, Dict, List, Optional

from loguru import logger


class TargetResolver:
    """
    Omnix V5 Target Resolver.

    Resolves targets for planned actions using the real Vision subsystem.

    This class does NOT create:

        - VisionManager
        - ScreenObserver
        - YOLODetector
        - VisionPipeline
        - ElementLocator

    The real VisionManager is injected by OmnixEngine and must be
    the same instance used everywhere else in Omnix.
    """

    def __init__(
        self,
        vision_manager: Optional[Any] = None,
        vision_service: Optional[Any] = None,
        context_service: Optional[Any] = None,
    ) -> None:

        self.vision_manager = vision_manager
        self.vision_service = vision_service
        self.context_service = context_service

        logger.debug(
            "TargetResolver initialized. "
            f"vision_manager="
            f"{type(vision_manager).__name__ if vision_manager else None}, "
            f"vision_service="
            f"{type(vision_service).__name__ if vision_service else None}"
        )

    # ============================================================
    # DEPENDENCY INJECTION
    # ============================================================

    def set_vision_manager(
        self,
        vision_manager: Any,
    ) -> None:

        self.vision_manager = vision_manager

        logger.debug("TargetResolver VisionManager updated.")

    def set_vision_service(
        self,
        vision_service: Any,
    ) -> None:

        self.vision_service = vision_service

        logger.debug("TargetResolver VisionService updated.")

    def set_context_service(
        self,
        context_service: Any,
    ) -> None:

        self.context_service = context_service

    # ============================================================
    # MAIN TARGET RESOLUTION
    # ============================================================

    def resolve(
        self,
        target: Any,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """
        Resolve a target using the real VisionManager.

        Examples:

            "Chrome icon"
            "Search button"
            "Settings"
            "Login"
            {"text": "Submit"}
        """

        if target is None:
            return None

        context = context or {}

        # --------------------------------------------------------
        # Already resolved.
        # --------------------------------------------------------

        if self._is_resolved_target(target):
            return target

        # --------------------------------------------------------
        # Normalize query.
        # --------------------------------------------------------

        query = self._extract_query(target)

        if not query:
            return None

        logger.debug(f"Resolving target: {query}")

        # --------------------------------------------------------
        # 1. Try the real VisionManager directly.
        # --------------------------------------------------------

        result = self._resolve_with_manager(
            query,
            context,
        )

        if result is not None:
            return result

        # --------------------------------------------------------
        # 2. Fall back to VisionService.
        # --------------------------------------------------------

        result = self._resolve_with_service(
            query,
            context,
        )

        if result is not None:
            return result

        logger.debug(f"Target not resolved: {query}")

        return None

    # Compatibility aliases.
    resolve_target = resolve
    find = resolve

    # ============================================================
    # VISION MANAGER
    # ============================================================

    def _resolve_with_manager(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> Optional[Any]:

        manager = self.vision_manager

        if manager is None:
            return None

        methods = (
            "find_element",
            "find_target",
            "locate_element",
            "locate",
            "find",
        )

        for method_name in methods:

            method = getattr(
                manager,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:

                result = self._call_method(
                    method,
                    query,
                    context,
                )

                result = self._normalize_result(result)

                if result is not None:

                    logger.debug(
                        f"Target resolved through " f"VisionManager.{method_name}()"
                    )

                    return result

            except Exception as error:

                logger.debug(f"VisionManager.{method_name} " f"failed: {error}")

        return None

    # ============================================================
    # VISION SERVICE
    # ============================================================

    def _resolve_with_service(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> Optional[Any]:

        service = self.vision_service

        if service is None:
            return None

        methods = (
            "find_element",
            "find_target",
            "locate_element",
            "locate",
            "find",
            "resolve",
        )

        for method_name in methods:

            method = getattr(
                service,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:

                result = self._call_method(
                    method,
                    query,
                    context,
                )

                result = self._normalize_result(result)

                if result is not None:

                    logger.debug(
                        f"Target resolved through " f"VisionService.{method_name}()"
                    )

                    return result

            except Exception as error:

                logger.debug(f"VisionService.{method_name} " f"failed: {error}")

        return None

    # ============================================================
    # METHOD CALLING
    # ============================================================

    @staticmethod
    def _call_method(
        method: Any,
        query: str,
        context: Dict[str, Any],
    ) -> Any:

        attempts = (
            lambda: method(
                query,
                context=context,
            ),
            lambda: method(query),
            lambda: method(target=query),
            lambda: method(text=query),
        )

        last_error = None

        for attempt in attempts:

            try:
                return attempt()

            except TypeError as error:
                last_error = error
                continue

        if last_error is not None:
            raise last_error

        return None

    # ============================================================
    # RESULT NORMALIZATION
    # ============================================================

    @staticmethod
    def _normalize_result(
        result: Any,
    ) -> Optional[Any]:

        if result is None:
            return None

        if result is False:
            return None

        if (
            isinstance(
                result,
                (list, tuple),
            )
            and len(result) == 0
        ):
            return None

        if isinstance(
            result,
            dict,
        ):

            if result.get("success") is False:
                return None

            for key in (
                "target",
                "element",
                "result",
                "value",
                "data",
            ):

                if key in result and result[key] is not None:
                    return result[key]

        return result

    # ============================================================
    # TARGET HELPERS
    # ============================================================

    @staticmethod
    def _extract_query(
        target: Any,
    ) -> str:

        if isinstance(
            target,
            str,
        ):
            return target.strip()

        if isinstance(
            target,
            dict,
        ):

            for key in (
                "query",
                "target",
                "text",
                "name",
                "label",
                "description",
            ):

                value = target.get(key)

                if value:
                    return str(value).strip()

        for attribute in (
            "query",
            "target",
            "text",
            "name",
            "label",
            "description",
        ):

            value = getattr(
                target,
                attribute,
                None,
            )

            if value:
                return str(value).strip()

        return str(target).strip()

    @staticmethod
    def _is_resolved_target(
        target: Any,
    ) -> bool:

        if isinstance(
            target,
            dict,
        ):

            coordinate_keys = (
                "x",
                "y",
                "bbox",
                "bounds",
                "coordinates",
            )

            return any(key in target for key in coordinate_keys)

        for attribute in (
            "bbox",
            "bounds",
            "coordinates",
        ):

            if (
                getattr(
                    target,
                    attribute,
                    None,
                )
                is not None
            ):
                return True

        return False

    # ============================================================
    # STATUS
    # ============================================================

    def status(
        self,
    ) -> Dict[str, Any]:

        return {
            "available": True,
            "vision_manager": (
                type(self.vision_manager).__name__
                if self.vision_manager is not None
                else None
            ),
            "vision_service": (
                type(self.vision_service).__name__
                if self.vision_service is not None
                else None
            ),
        }

    def health_check(
        self,
    ) -> bool:

        return True
