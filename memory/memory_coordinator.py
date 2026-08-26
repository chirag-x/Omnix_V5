"""
Omnix V5 - Memory Coordinator

Central coordinator for Omnix memory systems.

Architecture:

    MemoryCoordinator
        |
        +--> MemoryManager
        |      Semantic / long-term memory
        |
        +--> BehaviorMemory
        |      Successful command -> plan learning
        |
        +--> SystemMemory
               Persistent operational memory

Important:
    UIPatternMemory is intentionally NOT managed here.

    It remains owned by VisionManager because it represents
    visual/UI learning rather than general Omnix memory.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger


class MemoryCoordinator:
    """
    Unified V5 coordinator for Omnix memory.

    This class provides one stable entry point while preserving
    the existing memory implementations and their APIs.

    Managed systems:

        semantic_memory -> memory.memory_manager.MemoryManager
        behavior_memory -> memory.behavior_memory.BehaviorMemory
        system_memory   -> system.memory.system_memory.SystemMemory
    """

    def __init__(
        self,
        semantic_memory: Optional[Any] = None,
        behavior_memory: Optional[Any] = None,
        system_memory: Optional[Any] = None,
        auto_initialize: bool = True,
    ) -> None:

        self.semantic_memory = semantic_memory
        self.behavior_memory = behavior_memory
        self.system_memory = system_memory

        self._initialized = False
        self._errors: List[str] = []

        if auto_initialize:
            self.initialize()

    # ==================================================================
    # INITIALIZATION
    # ==================================================================

    def initialize(self) -> bool:
        """
        Initialize all available memory backends.

        Failure of one backend should not destroy the entire
        Omnix memory system.
        """

        if self._initialized:
            return True

        self._errors.clear()

        self._initialize_semantic_memory()
        self._initialize_behavior_memory()
        self._initialize_system_memory()

        self._initialized = True

        available = sum(
            backend is not None
            for backend in (
                self.semantic_memory,
                self.behavior_memory,
                self.system_memory,
            )
        )

        logger.info(
            "MemoryCoordinator initialized with " f"{available}/3 memory backends."
        )

        if self._errors:
            for error in self._errors:
                logger.warning(error)

        return available > 0

    def _initialize_semantic_memory(self) -> None:

        if self.semantic_memory is not None:
            return

        try:

            from memory.memory_manager import MemoryManager

            self.semantic_memory = MemoryManager()

            logger.info("Semantic MemoryManager connected.")

        except Exception as error:

            self._record_error(
                "Semantic memory initialization failed",
                error,
            )

    def _initialize_behavior_memory(self) -> None:

        if self.behavior_memory is not None:
            return

        try:

            from memory.behavior_memory import BehaviorMemory

            self.behavior_memory = BehaviorMemory()

            logger.info("BehaviorMemory connected.")

        except Exception as error:

            self._record_error(
                "Behavior memory initialization failed",
                error,
            )

    def _initialize_system_memory(self) -> None:

        if self.system_memory is not None:
            return

        try:

            from system.memory.system_memory import SystemMemory

            self.system_memory = SystemMemory()

            logger.info("SystemMemory connected.")

        except Exception as error:

            self._record_error(
                "System memory initialization failed",
                error,
            )

    def _record_error(
        self,
        message: str,
        error: Exception,
    ) -> None:

        full_message = f"{message}: {error}"

        self._errors.append(full_message)

        logger.warning(full_message)

    # ==================================================================
    # GENERAL MEMORY
    # ==================================================================

    def remember(
        self,
        memory: Any,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Store information in semantic memory.

        Supports the existing MemoryManager API while allowing
        metadata for future memory implementations.
        """

        self._ensure_initialized()

        backend = self.semantic_memory

        if backend is None:

            logger.warning("Semantic memory is unavailable.")

            return False

        text = self._normalize_memory_text(memory)

        if not text:
            return False

        try:

            result = self._call_first(
                backend,
                (
                    "remember",
                    "add_memory",
                    "add",
                    "store",
                ),
                text,
                metadata=metadata,
                **kwargs,
            )

            return self._normalize_success(result)

        except Exception as error:

            logger.exception(f"Failed to remember information: {error}")

            return False

    def add_memory(
        self,
        memory: Any,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Compatibility alias for existing Omnix code.
        """

        return self.remember(
            memory,
            metadata=metadata,
            **kwargs,
        )

    def recall(
        self,
        query: Any,
        limit: int = 5,
        **kwargs: Any,
    ) -> List[Any]:
        """
        Recall semantically relevant memories.
        """

        self._ensure_initialized()

        backend = self.semantic_memory

        if backend is None:
            return []

        query = self._normalize_memory_text(query)

        if not query:
            return []

        try:

            result = self._call_search(
                backend,
                query,
                limit=limit,
                **kwargs,
            )

            return self._normalize_list(result)

        except Exception as error:

            logger.exception(f"Failed to recall memory: {error}")

            return []

    def search(
        self,
        query: Any,
        limit: int = 5,
        **kwargs: Any,
    ) -> List[Any]:
        """
        Alias for semantic memory search.
        """

        return self.recall(
            query,
            limit=limit,
            **kwargs,
        )

    def search_memory(
        self,
        query: Any,
        top_k: int = 5,
        **kwargs: Any,
    ) -> List[Any]:
        """
        Compatibility method for code expecting:

            MemoryManager.search_memory(...)
        """

        return self.recall(
            query,
            limit=top_k,
            **kwargs,
        )

    # ==================================================================
    # BEHAVIOR MEMORY
    # ==================================================================

    def remember_behavior(
        self,
        command: str,
        plan: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Store a successful command -> plan relationship.
        """

        self._ensure_initialized()

        backend = self.behavior_memory

        if backend is None:

            logger.warning("Behavior memory is unavailable.")

            return False

        command = str(command or "").strip()

        if not command:
            return False

        try:

            result = self._call_first(
                backend,
                (
                    "remember_behavior",
                    "remember",
                    "store",
                    "learn",
                    "add",
                ),
                command,
                plan,
                **kwargs,
            )

            return self._normalize_success(result)

        except Exception as error:

            logger.exception(f"Failed to remember behavior: {error}")

            return False

    def recall_behavior(
        self,
        command: str,
        **kwargs: Any,
    ) -> Any:
        """
        Retrieve a previously successful plan for a command.
        """

        self._ensure_initialized()

        backend = self.behavior_memory

        if backend is None:
            return None

        command = str(command or "").strip()

        if not command:
            return None

        try:

            return self._call_first(
                backend,
                (
                    "recall_behavior",
                    "recall",
                    "get",
                    "find",
                    "search",
                ),
                command,
                **kwargs,
            )

        except Exception as error:

            logger.exception(f"Failed to recall behavior: {error}")

            return None

    # Compatibility aliases

    def learn_behavior(
        self,
        command: str,
        plan: Any,
        **kwargs: Any,
    ) -> bool:

        return self.remember_behavior(
            command,
            plan,
            **kwargs,
        )

    def get_learned_behavior(
        self,
        command: str,
        **kwargs: Any,
    ) -> Any:

        return self.recall_behavior(
            command,
            **kwargs,
        )

    # ==================================================================
    # SYSTEM MEMORY
    # ==================================================================

    def remember_system(
        self,
        key: str,
        value: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Store operational/system information.

        The exact storage method is delegated to SystemMemory.
        """

        self._ensure_initialized()

        backend = self.system_memory

        if backend is None:
            return False

        try:

            result = self._call_first(
                backend,
                (
                    "remember",
                    "set",
                    "store",
                    "add",
                ),
                key,
                value,
                **kwargs,
            )

            return self._normalize_success(result)

        except AttributeError:

            logger.debug("SystemMemory does not expose a generic " "storage method.")

            return False

        except Exception as error:

            logger.exception(f"Failed to store system memory: {error}")

            return False

    def recall_system(
        self,
        key: str,
        default: Any = None,
        **kwargs: Any,
    ) -> Any:
        """
        Retrieve generic operational/system information.
        """

        self._ensure_initialized()

        backend = self.system_memory

        if backend is None:
            return default

        try:

            result = self._call_first(
                backend,
                (
                    "recall",
                    "get",
                    "retrieve",
                    "find",
                ),
                key,
                **kwargs,
            )

            if result is None:
                return default

            return result

        except AttributeError:
            return default

        except Exception as error:

            logger.exception(f"Failed to recall system memory: {error}")

            return default

    # ==================================================================
    # SYSTEM MEMORY PASSTHROUGH
    # ==================================================================

    def add_recent_app(
        self,
        app_name: str,
        **kwargs: Any,
    ) -> Any:

        return self._call_system_method(
            (
                "add_recent_app",
                "remember_recent_app",
            ),
            app_name,
            **kwargs,
        )

    def get_recent_apps(
        self,
        **kwargs: Any,
    ) -> Any:

        return self._call_system_method(
            (
                "get_recent_apps",
                "recent_apps",
            ),
            **kwargs,
        )

    def remember_alias(
        self,
        alias: str,
        target: str,
        **kwargs: Any,
    ) -> Any:

        return self._call_system_method(
            (
                "remember_alias",
                "add_alias",
                "set_alias",
            ),
            alias,
            target,
            **kwargs,
        )

    def resolve_alias(
        self,
        alias: str,
        default: Any = None,
        **kwargs: Any,
    ) -> Any:

        result = self._call_system_method(
            (
                "resolve_alias",
                "get_alias",
                "find_alias",
            ),
            alias,
            **kwargs,
        )

        if result is None:
            return default

        return result

    def record_failure(
        self,
        failure: Any,
        **kwargs: Any,
    ) -> Any:

        return self._call_system_method(
            (
                "record_failure",
                "add_failure",
                "remember_failure",
            ),
            failure,
            **kwargs,
        )

    def record_statistic(
        self,
        name: str,
        value: Any,
        **kwargs: Any,
    ) -> Any:

        return self._call_system_method(
            (
                "record_statistic",
                "update_statistic",
                "set_statistic",
            ),
            name,
            value,
            **kwargs,
        )

    def _call_system_method(
        self,
        method_names,
        *args: Any,
        **kwargs: Any,
    ) -> Any:

        self._ensure_initialized()

        backend = self.system_memory

        if backend is None:
            return None

        try:

            return self._call_first(
                backend,
                tuple(method_names),
                *args,
                **kwargs,
            )

        except AttributeError:

            logger.debug("SystemMemory does not expose any of: " f"{method_names}")

            return None

        except Exception as error:

            logger.exception(f"System memory operation failed: {error}")

            return None

    # ==================================================================
    # CLEAR
    # ==================================================================

    def clear(
        self,
        memory_type: Optional[str] = None,
    ) -> bool:
        """
        Clear one or more memory backends.

        memory_type:
            semantic
            behavior
            system
            all / None
        """

        self._ensure_initialized()

        target = str(memory_type or "all").lower().strip()

        targets = []

        if target in (
            "all",
            "*",
        ):

            targets = [
                self.semantic_memory,
                self.behavior_memory,
                self.system_memory,
            ]

        elif target in (
            "semantic",
            "memory",
        ):

            targets = [self.semantic_memory]

        elif target in (
            "behavior",
            "behaviour",
        ):

            targets = [self.behavior_memory]

        elif target == "system":

            targets = [self.system_memory]

        else:

            raise ValueError(f"Unknown memory type: {memory_type}")

        success = False

        for backend in targets:

            if backend is None:
                continue

            try:

                result = self._call_first(
                    backend,
                    (
                        "clear",
                        "reset",
                        "delete_all",
                    ),
                )

                success = self._normalize_success(result) or success

            except AttributeError:

                logger.debug(
                    f"{type(backend).__name__} " "does not expose a clear method."
                )

            except Exception as error:

                logger.exception(f"Failed to clear memory backend: " f"{error}")

        return success

    # ==================================================================
    # STATUS
    # ==================================================================

    def status(self) -> Dict[str, Any]:
        """
        Return the current memory system health/status.
        """

        self._ensure_initialized()

        return {
            "initialized": self._initialized,
            "semantic_memory": {
                "available": (self.semantic_memory is not None),
                "type": self._backend_name(self.semantic_memory),
            },
            "behavior_memory": {
                "available": (self.behavior_memory is not None),
                "type": self._backend_name(self.behavior_memory),
            },
            "system_memory": {
                "available": (self.system_memory is not None),
                "type": self._backend_name(self.system_memory),
            },
            "errors": list(self._errors),
        }

    def health(self) -> Dict[str, Any]:

        status = self.status()

        available = sum(
            (
                status["semantic_memory"]["available"],
                status["behavior_memory"]["available"],
                status["system_memory"]["available"],
            )
        )

        return {
            "healthy": available > 0,
            "available_backends": available,
            "total_backends": 3,
            "status": status,
        }

    # ==================================================================
    # INTERNAL HELPERS
    # ==================================================================

    def _ensure_initialized(self) -> None:

        if not self._initialized:
            self.initialize()

    @staticmethod
    def _backend_name(
        backend: Any,
    ) -> Optional[str]:

        if backend is None:
            return None

        return type(backend).__name__

    @staticmethod
    def _normalize_memory_text(
        value: Any,
    ) -> str:

        if value is None:
            return ""

        if isinstance(
            value,
            str,
        ):
            return value.strip()

        return str(value).strip()

    @staticmethod
    def _normalize_success(
        result: Any,
    ) -> bool:

        if result is None:
            return True

        if isinstance(
            result,
            bool,
        ):
            return result

        if hasattr(
            result,
            "success",
        ):

            return bool(result.success)

        if isinstance(
            result,
            dict,
        ):

            return bool(
                result.get(
                    "success",
                    True,
                )
            )

        return True

    @staticmethod
    def _normalize_list(
        result: Any,
    ) -> List[Any]:

        if result is None:
            return []

        if isinstance(
            result,
            list,
        ):
            return result

        if isinstance(
            result,
            tuple,
        ):
            return list(result)

        return [result]

    @staticmethod
    def _call_search(
        backend: Any,
        query: str,
        *,
        limit: int,
        **kwargs: Any,
    ) -> Any:

        search_methods = (
            "recall",
            "search",
            "search_memory",
            "find",
            "query",
        )

        last_error = None

        for method_name in search_methods:

            method = getattr(
                backend,
                method_name,
                None,
            )

            if not callable(method):
                continue

            attempts = (
                lambda: method(
                    query,
                    limit=limit,
                    **kwargs,
                ),
                lambda: method(
                    query,
                    top_k=limit,
                    **kwargs,
                ),
                lambda: method(
                    query,
                    k=limit,
                    **kwargs,
                ),
                lambda: method(
                    query,
                    **kwargs,
                ),
            )

            for attempt in attempts:

                try:

                    result = attempt()

                    if inspect.isawaitable(result):

                        raise RuntimeError(
                            "Async memory backend methods "
                            "are not supported by this "
                            "synchronous coordinator."
                        )

                    return result

                except TypeError as error:

                    last_error = error

                    continue

        if last_error is not None:
            raise last_error

        raise AttributeError(
            "No supported search method found " f"on {type(backend).__name__}."
        )

    @staticmethod
    def _call_first(
        backend: Any,
        method_names,
        *args: Any,
        **kwargs: Any,
    ) -> Any:

        last_error = None

        for method_name in method_names:

            method = getattr(
                backend,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:

                result = method(
                    *args,
                    **kwargs,
                )

                if inspect.isawaitable(result):

                    raise RuntimeError(
                        "Async memory backend methods "
                        "are not supported by this "
                        "synchronous coordinator."
                    )

                return result

            except TypeError as error:

                last_error = error

                # Retry without optional keyword arguments.
                if kwargs:

                    try:

                        result = method(*args)

                        if inspect.isawaitable(result):

                            raise RuntimeError(
                                "Async memory backend " "methods are not supported."
                            )

                        return result

                    except TypeError as retry_error:

                        last_error = retry_error

                continue

        if last_error is not None:
            raise last_error

        raise AttributeError(
            f"No supported method found on "
            f"{type(backend).__name__}: "
            f"{method_names}"
        )


__all__ = [
    "MemoryCoordinator",
]
