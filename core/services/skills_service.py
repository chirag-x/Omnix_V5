"""
Omnix V5 Skills Service

Thin integration gateway between the V5 core and the real
skills subsystem.

The real skill implementation lives in:

    skills/manager/skill_manager.py

This service does NOT load, discover, or implement skills itself.
It provides a stable gateway for OmnixEngine, planners, agents,
and legacy components.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Dict, List, Optional

# ============================================================================
# RESULT TYPES
# ============================================================================


@dataclass
class SkillResult:
    """
    Normalized result returned by SkillsService.

    The underlying skills subsystem may return its own SkillResult,
    dictionaries, booleans, strings, or other objects. This wrapper
    gives the V5 core a predictable result shape.
    """

    success: bool
    skill_name: str = ""
    provider: Optional[str] = None
    data: Any = None
    error: Optional[str] = None
    message: Optional[str] = None
    raw_result: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "skill_name": self.skill_name,
            "provider": self.provider,
            "data": self.data,
            "error": self.error,
            "message": self.message,
        }


@dataclass
class SkillInfo:
    """
    Normalized skill metadata exposed by SkillsService.
    """

    id: str
    name: str = ""
    description: str = ""
    category: str = ""
    aliases: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    priority: int = 0
    provider: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "aliases": list(self.aliases),
            "tags": list(self.tags),
            "priority": self.priority,
            "provider": self.provider,
            "metadata": dict(self.metadata),
        }


# ============================================================================
# SKILLS SERVICE
# ============================================================================


class SkillsService:
    """
    Core gateway for Omnix skills.

    Architecture:

        OmnixEngine
             |
             v
        SkillsService
             |
             v
        SkillManager
             |
             +--> SkillLoader
             +--> SkillRegistry
             +--> Built-in Skills

    This service intentionally does not duplicate SkillManager.
    It registers the real skill provider and delegates execution to it.
    """

    def __init__(self) -> None:

        self._providers: Dict[str, Any] = {}

        self._provider_priorities: Dict[str, int] = {}

        self._provider_metadata: Dict[
            str,
            Dict[str, Any],
        ] = {}

        self._lock = RLock()

    # ====================================================================
    # PROVIDER MANAGEMENT
    # ====================================================================

    def register_provider(
        self,
        name: str,
        provider: Any,
        *,
        replace: bool = False,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Register a real skills provider.

        Expected primary provider:

            SkillManager
        """

        normalized_name = self._normalize_provider_name(name)

        if provider is None:
            raise ValueError("Skill provider cannot be None.")

        try:
            priority = int(priority)
        except (TypeError, ValueError):
            priority = 0

        with self._lock:

            if normalized_name in self._providers and not replace:
                raise ValueError(
                    f"Skills provider already exists: " f"{normalized_name}"
                )

            self._providers[normalized_name] = provider

            self._provider_priorities[normalized_name] = priority

            self._provider_metadata[normalized_name] = dict(metadata or {})

    def unregister_provider(
        self,
        name: str,
    ) -> bool:

        normalized_name = self._normalize_provider_name(name)

        with self._lock:

            if normalized_name not in self._providers:
                return False

            self._providers.pop(
                normalized_name,
                None,
            )

            self._provider_priorities.pop(
                normalized_name,
                None,
            )

            self._provider_metadata.pop(
                normalized_name,
                None,
            )

            return True

    def get_provider(
        self,
        name: str,
    ) -> Any:

        normalized_name = self._normalize_provider_name(name)

        with self._lock:
            return self._providers.get(normalized_name)

    def has_provider(
        self,
        name: str,
    ) -> bool:

        return self.get_provider(name) is not None

    def get_provider_names(self) -> List[str]:

        with self._lock:

            return list(self._providers.keys())

    def get_primary_provider(
        self,
    ) -> Optional[tuple[str, Any]]:

        with self._lock:

            if not self._providers:
                return None

            ordered = sorted(
                self._providers.items(),
                key=lambda item: (
                    self._provider_priorities.get(
                        item[0],
                        0,
                    ),
                    item[0],
                ),
                reverse=True,
            )

            return ordered[0]

    # ====================================================================
    # SKILL DISCOVERY
    # ====================================================================

    async def initialize(self) -> None:
        """
        Initialize registered skill providers.

        For SkillManager this triggers skill discovery and loading.
        """

        providers = self._get_ordered_providers()

        for _, provider in providers:

            method = getattr(
                provider,
                "initialize",
                None,
            )

            if not callable(method):
                continue

            result = method()

            if inspect.isawaitable(result):
                await result

    async def shutdown(self) -> None:
        """
        Shutdown registered skill providers.
        """

        providers = self._get_ordered_providers()

        for _, provider in reversed(providers):

            method = getattr(
                provider,
                "shutdown",
                None,
            )

            if not callable(method):
                continue

            try:

                result = method()

                if inspect.isawaitable(result):
                    await result

            except Exception:
                # One provider failing should not prevent the
                # rest from shutting down.
                continue

    async def list_skills(
        self,
    ) -> List[SkillInfo]:

        results: List[SkillInfo] = []

        for provider_name, provider in self._get_ordered_providers():

            skills = await self._get_provider_skills(provider)

            for skill in skills:

                info = self._normalize_skill_info(
                    skill,
                    provider_name,
                )

                if info is not None:
                    results.append(info)

        return results

    async def has_skill(
        self,
        skill_name: str,
    ) -> bool:

        skill_name = self._normalize_skill_name(skill_name)

        if not skill_name:
            return False

        for _, provider in self._get_ordered_providers():

            method = getattr(
                provider,
                "has_skill",
                None,
            )

            if callable(method):

                try:

                    result = method(skill_name)

                    if inspect.isawaitable(result):
                        result = await result

                    if result:
                        return True

                except Exception:
                    continue

        return False

    # ====================================================================
    # EXECUTION
    # ====================================================================

    async def execute(
        self,
        skill: Any,
        parameters: Optional[Dict[str, Any]] = None,
        context: Optional[Any] = None,
        *,
        provider_name: Optional[str] = None,
        **kwargs: Any,
    ) -> SkillResult:
        """
        Execute a skill through the real SkillManager.

        Supported calls:

            await service.execute(
                "open_app",
                {"app": "chrome"},
            )

            await service.execute(
                {
                    "skill": "open_app",
                    "parameters": {
                        "app": "chrome"
                    }
                }
            )

        The V5 SkillManager receives:

            execute(skill_id, SkillContext)
        """

        skill_name, parameters = self._normalize_execution_request(
            skill,
            parameters,
            kwargs,
        )

        if not skill_name:

            return SkillResult(
                success=False,
                error="Skill name is required.",
            )

        if provider_name:

            provider = self.get_provider(provider_name)

            if provider is None:

                return SkillResult(
                    success=False,
                    skill_name=skill_name,
                    provider=provider_name,
                    error=(f"Skills provider not found: " f"{provider_name}"),
                )

            return await self._execute_with_provider(
                provider_name,
                provider,
                skill_name,
                parameters,
                context,
            )

        last_result: Optional[SkillResult] = None

        for name, provider in self._get_ordered_providers():

            result = await self._execute_with_provider(
                name,
                provider,
                skill_name,
                parameters,
                context,
            )

            if result.success:
                return result

            last_result = result

        if last_result is not None:
            return last_result

        return SkillResult(
            success=False,
            skill_name=skill_name,
            error="No skills provider is registered.",
        )

    async def execute_step(
        self,
        step: Dict[str, Any],
        context: Optional[Any] = None,
    ) -> SkillResult:
        """
        Execute a planner/agent step.

        Example:

            {
                "skill": "open_app",
                "parameters": {
                    "app": "chrome"
                }
            }
        """

        return await self.execute(
            step,
            context=context,
        )

    # ====================================================================
    # PROVIDER EXECUTION
    # ====================================================================

    async def _execute_with_provider(
        self,
        provider_name: str,
        provider: Any,
        skill_name: str,
        parameters: Dict[str, Any],
        context: Optional[Any],
    ) -> SkillResult:

        # --------------------------------------------------------------
        # PRIMARY V5 PATH
        #
        # SkillManager.execute(
        #     skill_id,
        #     context: SkillContext,
        # )
        # --------------------------------------------------------------

        execute = getattr(
            provider,
            "execute",
            None,
        )

        if callable(execute):

            try:

                skill_context = self._build_skill_context(
                    provider,
                    skill_name,
                    parameters,
                    context,
                )

                raw_result = execute(
                    skill_name,
                    skill_context,
                )

                if inspect.isawaitable(raw_result):
                    raw_result = await raw_result

                return self._normalize_result(
                    raw_result,
                    skill_name,
                    provider_name,
                )

            except TypeError:
                # The provider may expose a different execute()
                # signature. Fall through to compatibility APIs.
                pass

            except Exception as error:

                return SkillResult(
                    success=False,
                    skill_name=skill_name,
                    provider=provider_name,
                    error=str(error),
                )

        # --------------------------------------------------------------
        # COMPATIBILITY PATH
        # --------------------------------------------------------------

        for method_name in (
            "execute_skill",
            "run_skill",
            "run",
        ):

            method = getattr(
                provider,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:

                raw_result = self._invoke_compatibility_method(
                    method,
                    skill_name,
                    parameters,
                    context,
                )

                if inspect.isawaitable(raw_result):
                    raw_result = await raw_result

                return self._normalize_result(
                    raw_result,
                    skill_name,
                    provider_name,
                )

            except Exception as error:

                return SkillResult(
                    success=False,
                    skill_name=skill_name,
                    provider=provider_name,
                    error=str(error),
                )

        return SkillResult(
            success=False,
            skill_name=skill_name,
            provider=provider_name,
            error=("Provider does not expose a compatible " "skill execution API."),
        )

    def _build_skill_context(
        self,
        provider: Any,
        skill_name: str,
        parameters: Dict[str, Any],
        supplied_context: Optional[Any],
    ) -> Any:
        """
        Build the real SkillContext expected by SkillManager.

        If the caller already supplied a SkillContext-like object,
        it is preserved.
        """

        if supplied_context is not None:

            if hasattr(
                supplied_context,
                "parameters",
            ) and hasattr(
                supplied_context,
                "command",
            ):
                return supplied_context

        # Import lazily so core/services does not force the
        # skills subsystem to load during engine construction.
        from skills.core.skill_context import SkillContext

        dependencies = getattr(
            provider,
            "dependencies",
            {},
        )

        if not isinstance(
            dependencies,
            dict,
        ):
            dependencies = {}

        supplied = (
            supplied_context
            if isinstance(
                supplied_context,
                dict,
            )
            else {}
        )

        merged_parameters = dict(parameters)

        extra_parameters = supplied.get(
            "parameters",
            {},
        )

        if isinstance(
            extra_parameters,
            dict,
        ):
            merged_parameters.update(extra_parameters)

        return SkillContext(
            command=(
                supplied.get(
                    "command",
                    skill_name,
                )
            ),
            entities=supplied.get(
                "entities",
                merged_parameters,
            ),
            parameters=merged_parameters,
            automation=supplied.get(
                "automation",
                dependencies.get("automation"),
            ),
            browser=supplied.get(
                "browser",
                dependencies.get("browser"),
            ),
            vision=supplied.get(
                "vision",
                dependencies.get("vision_manager"),
            ),
            input=supplied.get(
                "input",
                dependencies.get("input"),
            ),
            memory=supplied.get(
                "memory",
                dependencies.get("memory"),
            ),
            ai=supplied.get(
                "ai",
                dependencies.get("brain"),
            ),
            system=supplied.get(
                "system",
                dependencies.get("system"),
            ),
            planner=supplied.get(
                "planner",
                dependencies.get("planner"),
            ),
            skills=provider,
            ui=supplied.get(
                "ui",
                dependencies.get("ui_controller"),
            ),
            files=supplied.get(
                "files",
                dependencies.get("files"),
            ),
            clipboard=supplied.get(
                "clipboard",
                dependencies.get("clipboard"),
            ),
            events=supplied.get(
                "events",
                dependencies.get("events"),
            ),
            logger=supplied.get(
                "logger",
                dependencies.get("logger"),
            ),
        )

    # ====================================================================
    # COMPATIBILITY INVOCATION
    # ====================================================================

    @staticmethod
    def _invoke_compatibility_method(
        method: Any,
        skill_name: str,
        parameters: Dict[str, Any],
        context: Optional[Any],
    ) -> Any:

        step = {
            "skill": skill_name,
            "parameters": parameters,
        }

        attempts = (
            lambda: method(step),
            lambda: method(
                skill_name,
                parameters,
            ),
            lambda: method(
                skill_name=skill_name,
                parameters=parameters,
                context=context,
            ),
            lambda: method(
                skill_name,
                context,
            ),
        )

        last_error = None

        for attempt in attempts:

            try:
                return attempt()

            except TypeError as error:
                last_error = error

        if last_error is not None:
            raise last_error

        raise RuntimeError("Unable to invoke skill provider.")

    # ====================================================================
    # SKILL DISCOVERY HELPERS
    # ====================================================================

    async def _get_provider_skills(
        self,
        provider: Any,
    ) -> List[Any]:

        for method_name in (
            "list_skills",
            "get_skills",
            "skills",
        ):

            method = getattr(
                provider,
                method_name,
                None,
            )

            if callable(method):

                result = method()

                if inspect.isawaitable(result):
                    result = await result

                return self._normalize_collection(result)

        return []

    # ====================================================================
    # NORMALIZATION
    # ====================================================================

    def _normalize_execution_request(
        self,
        skill: Any,
        parameters: Optional[Dict[str, Any]],
        kwargs: Dict[str, Any],
    ) -> tuple[Optional[str], Dict[str, Any]]:

        if isinstance(
            skill,
            dict,
        ):

            skill_name = (
                skill.get("skill")
                or skill.get("tool")
                or skill.get("name")
                or skill.get("action")
            )

            extracted_parameters = (
                skill.get("parameters")
                or skill.get("params")
                or skill.get("args")
                or {}
            )

            if not isinstance(
                extracted_parameters,
                dict,
            ):
                extracted_parameters = {}

            merged = dict(extracted_parameters)

            for key, value in skill.items():

                if key not in (
                    "skill",
                    "tool",
                    "name",
                    "action",
                    "parameters",
                    "params",
                    "args",
                ):

                    merged.setdefault(
                        key,
                        value,
                    )

        else:

            skill_name = skill

            merged = dict(parameters or {})

        if parameters and isinstance(
            parameters,
            dict,
        ):
            merged.update(parameters)

        merged.update(kwargs)

        return (
            self._normalize_skill_name(skill_name),
            merged,
        )

    @staticmethod
    def _normalize_result(
        raw_result: Any,
        skill_name: str,
        provider_name: str,
    ) -> SkillResult:

        if isinstance(
            raw_result,
            SkillResult,
        ):
            return raw_result

        if raw_result is None:

            return SkillResult(
                success=True,
                skill_name=skill_name,
                provider=provider_name,
                raw_result=None,
            )

        success = getattr(
            raw_result,
            "success",
            None,
        )

        if success is not None:

            return SkillResult(
                success=bool(success),
                skill_name=getattr(
                    raw_result,
                    "skill_name",
                    skill_name,
                ),
                provider=provider_name,
                data=getattr(
                    raw_result,
                    "data",
                    getattr(
                        raw_result,
                        "result",
                        None,
                    ),
                ),
                error=getattr(
                    raw_result,
                    "error",
                    None,
                ),
                message=getattr(
                    raw_result,
                    "message",
                    None,
                ),
                raw_result=raw_result,
            )

        if isinstance(
            raw_result,
            dict,
        ):

            return SkillResult(
                success=bool(
                    raw_result.get(
                        "success",
                        True,
                    )
                ),
                skill_name=raw_result.get(
                    "skill_name",
                    skill_name,
                ),
                provider=provider_name,
                data=raw_result.get(
                    "data",
                    raw_result.get(
                        "result",
                        raw_result,
                    ),
                ),
                error=raw_result.get(
                    "error",
                ),
                message=raw_result.get(
                    "message",
                ),
                raw_result=raw_result,
            )

        if isinstance(
            raw_result,
            bool,
        ):

            return SkillResult(
                success=raw_result,
                skill_name=skill_name,
                provider=provider_name,
                raw_result=raw_result,
            )

        return SkillResult(
            success=True,
            skill_name=skill_name,
            provider=provider_name,
            data=raw_result,
            raw_result=raw_result,
        )

    def _normalize_skill_info(
        self,
        skill: Any,
        provider_name: str,
    ) -> Optional[SkillInfo]:

        if skill is None:
            return None

        metadata = getattr(
            skill,
            "metadata",
            skill,
        )

        skill_id = getattr(
            metadata,
            "id",
            None,
        )

        if skill_id is None and isinstance(
            metadata,
            dict,
        ):
            skill_id = metadata.get("id")

        if not skill_id:
            return None

        def get_value(
            name: str,
            default: Any = None,
        ) -> Any:

            if isinstance(
                metadata,
                dict,
            ):
                return metadata.get(
                    name,
                    default,
                )

            return getattr(
                metadata,
                name,
                default,
            )

        return SkillInfo(
            id=str(skill_id),
            name=str(
                get_value(
                    "name",
                    skill_id,
                )
            ),
            description=str(
                get_value(
                    "description",
                    "",
                )
            ),
            category=str(
                get_value(
                    "category",
                    "",
                )
            ),
            aliases=self._normalize_string_list(
                get_value(
                    "aliases",
                    [],
                )
            ),
            tags=self._normalize_string_list(
                get_value(
                    "tags",
                    [],
                )
            ),
            priority=int(
                get_value(
                    "priority",
                    0,
                )
                or 0
            ),
            provider=provider_name,
            metadata=self._object_to_dict(metadata),
        )

    # ====================================================================
    # PROVIDER ORDER
    # ====================================================================

    def _get_ordered_providers(
        self,
    ) -> List[tuple[str, Any]]:

        with self._lock:

            return sorted(
                self._providers.items(),
                key=lambda item: (
                    self._provider_priorities.get(
                        item[0],
                        0,
                    ),
                    item[0],
                ),
                reverse=True,
            )

    # ====================================================================
    # HELPERS
    # ====================================================================

    @staticmethod
    def _normalize_collection(
        value: Any,
    ) -> List[Any]:

        if value is None:
            return []

        if isinstance(
            value,
            dict,
        ):
            return list(value.values())

        if isinstance(
            value,
            (
                list,
                tuple,
                set,
            ),
        ):
            return list(value)

        return [value]

    @staticmethod
    def _normalize_string_list(
        value: Any,
    ) -> List[str]:

        if value is None:
            return []

        if isinstance(
            value,
            str,
        ):
            value = [value]

        if not isinstance(
            value,
            (
                list,
                tuple,
                set,
            ),
        ):
            return []

        return [str(item).strip() for item in value if str(item).strip()]

    @staticmethod
    def _object_to_dict(
        value: Any,
    ) -> Dict[str, Any]:

        if isinstance(
            value,
            dict,
        ):
            return dict(value)

        if hasattr(
            value,
            "__dict__",
        ):

            try:

                return {
                    key: item
                    for key, item in vars(value).items()
                    if not key.startswith("_")
                }

            except Exception:
                pass

        return {}

    @staticmethod
    def _normalize_provider_name(
        name: Any,
    ) -> str:

        normalized = str(name or "").strip().lower()

        if not normalized:
            raise ValueError("Provider name cannot be empty.")

        return normalized

    @staticmethod
    def _normalize_skill_name(
        name: Any,
    ) -> Optional[str]:

        if name is None:
            return None

        normalized = str(name).strip()

        return normalized or None

    # ====================================================================
    # STATUS
    # ====================================================================

    def status(
        self,
    ) -> Dict[str, Any]:

        with self._lock:

            providers = []

            for name, provider in self._providers.items():

                providers.append(
                    {
                        "name": name,
                        "priority": (
                            self._provider_priorities.get(
                                name,
                                0,
                            )
                        ),
                        "type": type(provider).__name__,
                    }
                )

            return {
                "service": "skills",
                "provider_count": len(self._providers),
                "providers": providers,
            }


__all__ = [
    "SkillResult",
    "SkillInfo",
    "SkillsService",
]
