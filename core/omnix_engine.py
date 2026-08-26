"""
Omnix V5 - Central Engine

The OmnixEngine is the single main entry point for Omnix.

Execution flow:

    TEXT INPUT
        |
        v
    OmnixEngine.execute()
        |
        +----------------------+
        |                      |
        v                      v
    Conversation           Automation
        |                      |
        v                      v
    AIService          AgentController
        |                      |
        v                      v
      AIResult             AgentResult


Voice uses the same execution pipeline:

    WakeListener
        |
        v
    SpeechRecognizer
        |
        v
    OmnixEngine.execute()
        |
        v
    AI / Agent pipeline
        |
        v
    VoiceManager / TTS


The engine coordinates components but does not duplicate the
responsibilities of services, managers, skills, vision, voice,
automation, or memory systems.
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import logging
import time

from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# OMNIX ENGINE
# ============================================================================


class OmnixEngine:
    """
    Central V5 integration and execution engine.

    Main responsibilities:

        - Initialize core services
        - Connect services to their real V5 managers
        - Initialize planning and agent systems
        - Inject shared dependencies
        - Provide one execute() entry point
        - Route requests to AI or automation
        - Manage lifecycle and shutdown
        - Provide health and status information
    """

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        auto_start: bool = False,
        **kwargs: Any,
    ) -> None:

        # --------------------------------------------------------------------
        # CONFIGURATION
        # --------------------------------------------------------------------

        self.config: Dict[str, Any] = {}

        if isinstance(config, dict):

            self.config.update(config)

        self.config.update(kwargs)

        # --------------------------------------------------------------------
        # ENGINE STATE
        # --------------------------------------------------------------------

        self._started = False

        self._initializing = False

        self._shutting_down = False

        self._started_at: Optional[float] = None

        self._startup_errors: Dict[
            str,
            str,
        ] = {}

        self._components: Dict[
            str,
            Any,
        ] = {}

        # --------------------------------------------------------------------
        # OPTIONAL SYSTEM REFERENCES
        # --------------------------------------------------------------------

        self.system: Any = self.config.get("system")

        self.event_bus: Any = self.config.get("event_bus") or self.config.get("events")

        # --------------------------------------------------------------------
        # INFRASTRUCTURE
        # --------------------------------------------------------------------

        self.service_registry: Any = None

        self.dependency_manager: Any = None

        self.lifecycle_manager: Any = None

        self.engine_manager: Any = None

        self.health_monitor: Any = None

        # --------------------------------------------------------------------
        # CORE SERVICES
        # --------------------------------------------------------------------

        self.context_service: Any = None

        self.memory_service: Any = None

        self.ai_service: Any = None

        self.skills_service: Any = None

        self.automation_service: Any = None

        self.vision_service: Any = None

        self.voice_service: Any = None

        self.ui_service: Any = None

        # --------------------------------------------------------------------
        # REAL V5 MANAGERS / BACKENDS
        # --------------------------------------------------------------------

        self.brain_manager: Any = None

        self.skills_manager: Any = None

        self.automation_engine: Any = None

        self.vision_manager: Any = None

        self.voice_manager: Any = None

        self.memory_coordinator: Any = None

        # --------------------------------------------------------------------
        # COMMAND / PLANNING
        # --------------------------------------------------------------------

        self.command_processor: Any = None

        self.intent_classifier: Any = None

        self.task_planner: Any = None

        self.target_resolver: Any = None

        self.workflow_planner: Any = None

        # --------------------------------------------------------------------
        # AGENT EXECUTION
        # --------------------------------------------------------------------

        self.goal_executor: Any = None

        self.agent_controller: Any = None

        # --------------------------------------------------------------------
        # ENGINE INITIALIZATION
        # --------------------------------------------------------------------

        self._initialize()

        if auto_start:

            self.start()

    # ========================================================================
    # MAIN INITIALIZATION
    # ========================================================================

    def _initialize(
        self,
    ) -> bool:
        """
        Initialize Omnix components.

        Initialization is intentionally fault-tolerant.

        One optional subsystem failing should not prevent Omnix
        from starting completely.
        """

        if self._initializing:

            return False

        self._initializing = True

        logger.info("Initializing Omnix V5 engine...")

        try:

            # --------------------------------------------------------------
            # INFRASTRUCTURE
            # --------------------------------------------------------------

            self._initialize_infrastructure()

            # --------------------------------------------------------------
            # CORE SERVICES
            # --------------------------------------------------------------

            self._initialize_core_services()

            # --------------------------------------------------------------
            # REAL V5 MANAGERS
            # --------------------------------------------------------------

            self._initialize_real_backends()

            # --------------------------------------------------------------
            # CONNECT SERVICES
            # --------------------------------------------------------------

            self._connect_service_backends()

            # --------------------------------------------------------------
            # PLANNING / AGENT
            # --------------------------------------------------------------

            self._initialize_planning_system()

            # --------------------------------------------------------------
            # DEPENDENCY INJECTION
            # --------------------------------------------------------------

            self._inject_all_dependencies()

            # --------------------------------------------------------------
            # COMPONENT REGISTRATION
            # --------------------------------------------------------------

            self._register_all_components()

            logger.info("Omnix V5 engine initialization complete.")

            return True

        except Exception as exc:

            logger.exception(
                "Omnix engine initialization failed: %s",
                exc,
            )

            self._startup_errors["engine_initialization"] = (
                f"{type(exc).__name__}: {exc}"
            )

            return False

        finally:

            self._initializing = False

    # ========================================================================
    # IMPORT HELPER
    # ========================================================================

    @staticmethod
    def _import_component(
        module_path: str,
        class_name: str,
    ) -> Optional[Any]:
        """
        Safely import a component.

        Returns None instead of crashing the complete engine
        when an optional component is unavailable.
        """

        try:

            module = importlib.import_module(module_path)

            return getattr(
                module,
                class_name,
            )

        except Exception as exc:

            logger.debug(
                "Could not import %s.%s: %s",
                module_path,
                class_name,
                exc,
            )

            return None

    # ========================================================================
    # SAFE INITIALIZATION
    # ========================================================================

    def _safe_initialize(
        self,
        component_name: str,
        component_class: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Optional[Any]:
        """
        Safely initialize a component.

        The component is automatically tracked when successful.
        """

        if component_class is None:

            return None

        try:

            component = component_class(
                *args,
                **kwargs,
            )

            self._components[component_name] = component

            logger.info(
                "Initialized component: %s",
                component_name,
            )

            return component

        except Exception as exc:

            logger.warning(
                "Failed to initialize '%s': %s",
                component_name,
                exc,
            )

            self._startup_errors[component_name] = f"{type(exc).__name__}: {exc}"

            return None

    # ========================================================================
    # INFRASTRUCTURE INITIALIZATION
    # ========================================================================

    def _initialize_infrastructure(
        self,
    ) -> None:
        """
        Initialize optional Omnix core infrastructure.
        """

        infrastructure = (
            (
                "service_registry",
                "core.service_registry",
                "ServiceRegistry",
            ),
            (
                "dependency_manager",
                "core.dependency_manager",
                "DependencyManager",
            ),
            (
                "lifecycle_manager",
                "core.lifecycle_manager",
                "LifecycleManager",
            ),
            (
                "engine_manager",
                "core.engine_manager",
                "EngineManager",
            ),
            (
                "health_monitor",
                "core.health_monitor",
                "HealthMonitor",
            ),
        )

        for (
            attribute_name,
            module_path,
            class_name,
        ) in infrastructure:

            component_class = self._import_component(
                module_path,
                class_name,
            )

            if component_class is None:

                continue

            component = self._safe_initialize(
                attribute_name,
                component_class,
            )

            setattr(
                self,
                attribute_name,
                component,
            )

    # ========================================================================
    # CORE SERVICES INITIALIZATION
    # ========================================================================

    def _initialize_core_services(
        self,
    ) -> None:
        """
        Initialize all Core service bridges.

        These services are the stable interfaces used by
        OmnixEngine. Their actual implementations are connected
        later to the real V5 managers/backends.
        """

        services = (
            (
                "context_service",
                "core.services.context_service",
                "ContextService",
            ),
            (
                "memory_service",
                "core.services.memory_service",
                "MemoryService",
            ),
            (
                "ai_service",
                "core.services.ai_service",
                "AIService",
            ),
            (
                "skills_service",
                "core.services.skills_service",
                "SkillsService",
            ),
            (
                "automation_service",
                "core.services.automation_service",
                "AutomationService",
            ),
            (
                "vision_service",
                "core.services.vision_service",
                "VisionService",
            ),
            (
                "voice_service",
                "core.services.voice_service",
                "VoiceService",
            ),
        )

        for (
            attribute_name,
            module_path,
            class_name,
        ) in services:

            service_class = self._import_component(
                module_path,
                class_name,
            )

            if service_class is None:
                continue

            service = self._safe_initialize(
                attribute_name,
                service_class,
            )

            setattr(
                self,
                attribute_name,
                service,
            )

    # ========================================================================
    # REAL V5 BACKENDS
    # ========================================================================

    def _initialize_real_backends(
        self,
    ) -> None:
        """
        Initialize the actual V5 managers and backend systems.

        Services are bridges.

        These components perform the real work.
        """

        # --------------------------------------------------------------------
        # MEMORY
        # --------------------------------------------------------------------

        if self.memory_service is not None:

            try:

                self.memory_coordinator = getattr(
                    self.memory_service,
                    "memory",
                    None,
                )

                if self.memory_coordinator is not None:

                    self._components["memory_coordinator"] = self.memory_coordinator

                    logger.info("Using MemoryCoordinator from " "MemoryService.")

            except Exception as exc:

                logger.warning(
                    "Could not obtain MemoryCoordinator: %s",
                    exc,
                )

        # --------------------------------------------------------------------
        # SKILLS
        # --------------------------------------------------------------------

        self.skills_manager = self._get_service_backend(
            self.skills_service,
            (
                "skills_manager",
                "manager",
                "backend",
                "provider",
            ),
        )

        # --------------------------------------------------------------------
        # AUTOMATION
        # --------------------------------------------------------------------

        self.automation_engine = self._get_service_backend(
            self.automation_service,
            (
                "automation_manager",
                "automation_engine",
                "manager",
                "engine",
                "backend",
                "provider",
            ),
        )

        # --------------------------------------------------------------------
        # VISION
        # --------------------------------------------------------------------

        self.vision_manager = self._get_service_backend(
            self.vision_service,
            (
                "vision_manager",
                "manager",
                "backend",
                "provider",
            ),
        )

        # --------------------------------------------------------------------
        # VOICE
        # --------------------------------------------------------------------

        self.voice_manager = self._get_service_backend(
            self.voice_service,
            (
                "voice_manager",
                "manager",
                "backend",
                "provider",
            ),
        )

        # --------------------------------------------------------------------
        # AI / BRAIN
        # --------------------------------------------------------------------

        self.brain_manager = self._get_service_backend(
            self.ai_service,
            (
                "brain_manager",
                "ai_manager",
                "manager",
                "backend",
                "provider",
            ),
        )

        # --------------------------------------------------------------------
        # REGISTER FOUND BACKENDS
        # --------------------------------------------------------------------

        backend_components = {
            "memory_coordinator": self.memory_coordinator,
            "skills_manager": self.skills_manager,
            "automation_engine": self.automation_engine,
            "vision_manager": self.vision_manager,
            "voice_manager": self.voice_manager,
            "brain_manager": self.brain_manager,
        }

        for name, component in backend_components.items():

            if component is not None:

                self._components[name] = component

                logger.info(
                    "Connected V5 backend: %s",
                    name,
                )

    # ========================================================================
    # SERVICE BACKEND HELPER
    # ========================================================================

    @staticmethod
    def _get_service_backend(
        service: Any,
        attribute_names: tuple,
    ) -> Optional[Any]:
        """
        Find the real manager/backend owned by a service.

        Different V5 services may expose their backend using
        slightly different names. This allows the engine to remain
        compatible without duplicating those systems.
        """

        if service is None:
            return None

        for attribute_name in attribute_names:

            try:

                backend = getattr(
                    service,
                    attribute_name,
                    None,
                )

                if backend is not None:
                    return backend

            except Exception:
                continue

        # Some services expose get_provider().
        get_provider = getattr(
            service,
            "get_provider",
            None,
        )

        if callable(get_provider):

            try:

                backend = get_provider()

                if backend is not None:
                    return backend

            except Exception:
                pass

        return None

    # ========================================================================
    # CONNECT SERVICES TO REAL BACKENDS
    # ========================================================================

    def _connect_service_backends(
        self,
    ) -> None:
        """
        Connect and synchronize the service layer with the actual
        V5 backend systems.

        Important:
        We do not create duplicate managers here.

        If a service already created and owns its manager,
        OmnixEngine simply uses that same instance.
        """

        # --------------------------------------------------------------------
        # MEMORY
        # --------------------------------------------------------------------

        if self.memory_service is not None and self.memory_coordinator is not None:

            self._ensure_service_reference(
                self.memory_service,
                "memory",
                self.memory_coordinator,
            )

        # --------------------------------------------------------------------
        # SKILLS
        # --------------------------------------------------------------------

        if self.skills_service is not None and self.skills_manager is not None:

            self._connect_backend_to_service(
                service=self.skills_service,
                backend=self.skills_manager,
                possible_attributes=(
                    "skills_manager",
                    "manager",
                    "backend",
                ),
                provider_name="omnix_skills",
            )

        # --------------------------------------------------------------------
        # AUTOMATION
        # --------------------------------------------------------------------

        if self.automation_service is not None and self.automation_engine is not None:

            self._connect_backend_to_service(
                service=self.automation_service,
                backend=self.automation_engine,
                possible_attributes=(
                    "automation_manager",
                    "automation_engine",
                    "manager",
                    "engine",
                    "backend",
                ),
                provider_name="omnix_automation",
            )

        # --------------------------------------------------------------------
        # VISION
        # --------------------------------------------------------------------

        if self.vision_service is not None and self.vision_manager is not None:

            self._connect_backend_to_service(
                service=self.vision_service,
                backend=self.vision_manager,
                possible_attributes=(
                    "vision_manager",
                    "manager",
                    "backend",
                ),
                provider_name="omnix_vision",
            )

        # --------------------------------------------------------------------
        # VOICE
        # --------------------------------------------------------------------

        if self.voice_service is not None and self.voice_manager is not None:

            self._connect_backend_to_service(
                service=self.voice_service,
                backend=self.voice_manager,
                possible_attributes=(
                    "voice_manager",
                    "manager",
                    "backend",
                ),
                provider_name="omnix_voice",
            )

        # --------------------------------------------------------------------
        # AI
        # --------------------------------------------------------------------

        if self.ai_service is not None and self.brain_manager is not None:

            self._connect_backend_to_service(
                service=self.ai_service,
                backend=self.brain_manager,
                possible_attributes=(
                    "brain_manager",
                    "ai_manager",
                    "manager",
                    "backend",
                ),
                provider_name="omnix_ai",
            )

    # ========================================================================
    # CONNECT BACKEND HELPER
    # ========================================================================

    def _connect_backend_to_service(
        self,
        service: Any,
        backend: Any,
        possible_attributes: tuple,
        provider_name: str,
    ) -> None:
        """
        Connect an existing backend to a service.

        This method intentionally tries multiple integration styles
        because the service files may expose different APIs.
        """

        if service is None or backend is None:
            return

        # --------------------------------------------------------------
        # 1. Ensure a direct attribute points to the backend.
        # --------------------------------------------------------------

        for attribute_name in possible_attributes:

            try:

                current_value = getattr(
                    service,
                    attribute_name,
                    None,
                )

                if current_value is None:

                    setattr(
                        service,
                        attribute_name,
                        backend,
                    )

                    break

            except Exception:
                continue

        # --------------------------------------------------------------
        # 2. Register provider if supported.
        # --------------------------------------------------------------

        register_provider = getattr(
            service,
            "register_provider",
            None,
        )

        if callable(register_provider):

            try:

                register_provider(
                    provider_name,
                    backend,
                    replace=True,
                )

                return

            except TypeError:

                try:

                    register_provider(
                        provider_name,
                        backend,
                    )

                    return

                except Exception:
                    pass

            except Exception:
                pass

        # --------------------------------------------------------------
        # 3. Add provider if supported.
        # --------------------------------------------------------------

        add_provider = getattr(
            service,
            "add_provider",
            None,
        )

        if callable(add_provider):

            try:

                add_provider(
                    provider_name,
                    backend,
                )

                return

            except Exception:
                pass

        logger.debug(
            "Backend connected directly to service: %s",
            type(service).__name__,
        )

    # ========================================================================
    # DIRECT REFERENCE HELPER
    # ========================================================================

    @staticmethod
    def _ensure_service_reference(
        service: Any,
        attribute_name: str,
        backend: Any,
    ) -> None:
        """
        Ensure that a service points at the expected backend.
        """

        if service is None or backend is None:
            return

        try:

            current_value = getattr(
                service,
                attribute_name,
                None,
            )

            if current_value is None:

                setattr(
                    service,
                    attribute_name,
                    backend,
                )

        except Exception:
            pass

    # ========================================================================
    # PLANNING / COMMAND SYSTEM INITIALIZATION
    # ========================================================================

    def _initialize_planning_system(
        self,
    ) -> None:
        """
        Initialize the command understanding, planning, and agent
        execution components.

        These components are initialized after the core services so
        they can receive shared Omnix dependencies.
        """

        # --------------------------------------------------------------------
        # INTENT CLASSIFIER
        # --------------------------------------------------------------------

        intent_classifier_class = self._import_component(
            "core.planning.intent_classifier",
            "IntentClassifier",
        )

        if intent_classifier_class is not None:

            self.intent_classifier = self._safe_initialize(
                "intent_classifier",
                intent_classifier_class,
            )

        # --------------------------------------------------------------------
        # COMMAND PROCESSOR
        # --------------------------------------------------------------------

        command_processor_class = self._import_component(
            "core.planning.command_processor",
            "CommandProcessor",
        )

        if command_processor_class is not None:

            self.command_processor = self._safe_initialize(
                "command_processor",
                command_processor_class,
            )

        # --------------------------------------------------------------------
        # TARGET RESOLVER
        # --------------------------------------------------------------------

        target_resolver_class = self._import_component(
            "core.planning.target_resolver",
            "TargetResolver",
        )

        if target_resolver_class is not None:

            self.target_resolver = self._safe_initialize(
                "target_resolver",
                target_resolver_class,
            )

        # --------------------------------------------------------------------
        # TASK PLANNER
        # --------------------------------------------------------------------

        task_planner_class = self._import_component(
            "core.planning.task_planner",
            "TaskPlanner",
        )

        if task_planner_class is not None:

            self.task_planner = self._safe_initialize(
                "task_planner",
                task_planner_class,
            )

        # --------------------------------------------------------------------
        # WORKFLOW PLANNER
        # --------------------------------------------------------------------

        workflow_planner_class = self._import_component(
            "core.agent.workflow_planner",
            "WorkflowPlanner",
        )

        if workflow_planner_class is not None:

            self.workflow_planner = self._safe_initialize(
                "workflow_planner",
                workflow_planner_class,
            )

        # --------------------------------------------------------------------
        # GOAL EXECUTOR
        # --------------------------------------------------------------------

        goal_executor_class = self._import_component(
            "core.agent.goal_executor",
            "GoalExecutor",
        )

        if goal_executor_class is not None:

            self.goal_executor = self._safe_initialize(
                "goal_executor",
                goal_executor_class,
            )

        # --------------------------------------------------------------------
        # AGENT CONTROLLER
        # --------------------------------------------------------------------

        agent_controller_class = self._import_component(
            "core.agent.agent_controller",
            "AgentController",
        )

        if agent_controller_class is not None:

            self.agent_controller = self._safe_initialize(
                "agent_controller",
                agent_controller_class,
            )

        logger.info("Planning and agent system initialization complete.")

    # ========================================================================
    # DEPENDENCY INJECTION
    # ========================================================================

    def _inject_all_dependencies(
        self,
    ) -> None:
        """
        Inject shared Omnix dependencies into components.

        We do this after all services, backends, planners, and
        agent components have been created.

        The method uses safe attribute injection because the
        existing Omnix components may expose different constructor
        signatures and dependency APIs.
        """

        dependencies = {
            # --------------------------------------------------------------
            # ENGINE
            # --------------------------------------------------------------
            "engine": self,
            "omnix_engine": self,
            # --------------------------------------------------------------
            # CORE SERVICES
            # --------------------------------------------------------------
            "context_service": self.context_service,
            "memory_service": self.memory_service,
            "ai_service": self.ai_service,
            "skills_service": self.skills_service,
            "automation_service": self.automation_service,
            "vision_service": self.vision_service,
            "voice_service": self.voice_service,
            # --------------------------------------------------------------
            # REAL BACKENDS
            # --------------------------------------------------------------
            "memory": self.memory_coordinator,
            "memory_coordinator": self.memory_coordinator,
            "brain_manager": self.brain_manager,
            "skills_manager": self.skills_manager,
            "automation_engine": self.automation_engine,
            "vision_manager": self.vision_manager,
            "voice_manager": self.voice_manager,
            # --------------------------------------------------------------
            # PLANNING
            # --------------------------------------------------------------
            "intent_classifier": self.intent_classifier,
            "command_processor": self.command_processor,
            "target_resolver": self.target_resolver,
            "task_planner": self.task_planner,
            "workflow_planner": self.workflow_planner,
            # --------------------------------------------------------------
            # AGENT
            # --------------------------------------------------------------
            "goal_executor": self.goal_executor,
            "agent_controller": self.agent_controller,
            # --------------------------------------------------------------
            # INFRASTRUCTURE
            # --------------------------------------------------------------
            "event_bus": self.event_bus,
            "system": self.system,
        }

        components = list(self._components.items())

        for component_name, component in components:

            if component is None:
                continue

            self._inject_dependencies_into_component(
                component_name,
                component,
                dependencies,
            )

    def _inject_dependencies_into_component(
        self,
        component_name: str,
        component: Any,
        dependencies: Dict[str, Any],
    ) -> None:
        """
        Inject dependencies into one component.

        Supported patterns:

            component.set_dependencies({...})

            component.inject_dependencies({...})

            component.configure(...)

            component.<dependency> = value
        """

        # --------------------------------------------------------------------
        # FILTER AVAILABLE DEPENDENCIES
        # --------------------------------------------------------------------

        available_dependencies = {
            name: value for name, value in dependencies.items() if value is not None
        }

        if not available_dependencies:
            return

        # --------------------------------------------------------------------
        # 1. BULK DEPENDENCY INJECTION
        # --------------------------------------------------------------------

        for method_name in (
            "set_dependencies",
            "inject_dependencies",
            "set_services",
            "set_context",
        ):

            method = getattr(
                component,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:

                result = method(available_dependencies)

                self._handle_possible_awaitable(
                    result,
                    component_name,
                    method_name,
                )

                return

            except TypeError:
                pass

            except Exception as exc:

                logger.debug(
                    "Dependency injection failed for " "%s using %s: %s",
                    component_name,
                    method_name,
                    exc,
                )

        # --------------------------------------------------------------------
        # 2. INDIVIDUAL ATTRIBUTE INJECTION
        # --------------------------------------------------------------------

        for (
            dependency_name,
            dependency,
        ) in available_dependencies.items():

            try:

                current_value = getattr(
                    component,
                    dependency_name,
                    None,
                )

                if current_value is None:

                    setattr(
                        component,
                        dependency_name,
                        dependency,
                    )

            except Exception:
                continue

    # ========================================================================
    # OPTIONAL ASYNC RESULT HANDLER
    # ========================================================================

    @staticmethod
    def _handle_possible_awaitable(
        result: Any,
        component_name: str,
        method_name: str,
    ) -> None:
        """
        Detect an async dependency method.

        Engine construction must not silently discard a coroutine.
        """

        if not inspect.isawaitable(result):
            return

        logger.warning(
            "Async dependency method returned by "
            "%s.%s during synchronous initialization. "
            "It was not awaited.",
            component_name,
            method_name,
        )

        try:

            result.close()

        except Exception:
            pass

    # ========================================================================
    # COMPONENT REGISTRATION
    # ========================================================================

    def _register_all_components(
        self,
    ) -> None:
        """
        Register initialized components with optional infrastructure.
        """

        registry = self.service_registry

        if registry is None:
            return

        register_methods = (
            "register",
            "add",
            "register_service",
        )

        for (
            component_name,
            component,
        ) in self._components.items():

            if component is None:
                continue

            for method_name in register_methods:

                method = getattr(
                    registry,
                    method_name,
                    None,
                )

                if not callable(method):
                    continue

                try:

                    method(
                        component_name,
                        component,
                    )

                    break

                except TypeError:

                    try:

                        method(component)

                        break

                    except Exception:
                        continue

                except Exception:
                    continue

    # ========================================================================
    # ENGINE START
    # ========================================================================

    def start(
        self,
    ) -> bool:
        """
        Start Omnix and its initialized components.
        """

        if self._started:

            return True

        if self._shutting_down:

            logger.warning("Cannot start Omnix while shutdown " "is in progress.")

            return False

        logger.info("Starting Omnix V5...")

        started_components: List[str] = []

        startup_order = (
            "context_service",
            "memory_service",
            "ai_service",
            "skills_service",
            "automation_service",
            "vision_service",
            "voice_service",
            "command_processor",
            "intent_classifier",
            "target_resolver",
            "task_planner",
            "workflow_planner",
            "goal_executor",
            "agent_controller",
        )

        for component_name in startup_order:

            component = getattr(
                self,
                component_name,
                None,
            )

            if component is None:
                continue

            if self._start_component(
                component_name,
                component,
            ):

                started_components.append(component_name)

        self._started = True

        self._started_at = time.time()

        logger.info(
            "Omnix V5 started. Components started: %s",
            ", ".join(started_components) if started_components else "none",
        )

        return True

    def _start_component(
        self,
        component_name: str,
        component: Any,
    ) -> bool:
        """
        Start one component using its available lifecycle method.
        """

        for method_name in (
            "start",
            "initialize",
            "run",
        ):

            method = getattr(
                component,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:

                result = method()

                if inspect.isawaitable(result):

                    self._run_awaitable_safely(
                        result,
                        component_name,
                        method_name,
                    )

                return True

            except Exception as exc:

                logger.warning(
                    "Failed to start %s using %s: %s",
                    component_name,
                    method_name,
                    exc,
                )

                self._startup_errors[f"{component_name}.start"] = (
                    f"{type(exc).__name__}: {exc}"
                )

                return False

        return True

    def _run_awaitable_safely(
        self,
        awaitable: Any,
        component_name: str,
        method_name: str,
    ) -> None:
        """
        Execute an awaitable only when no event loop is currently
        running.

        If Omnix is embedded inside an async application, the
        component should instead be started by that application's
        lifecycle.
        """

        try:

            asyncio.get_running_loop()

            logger.warning(
                "Cannot synchronously await %s.%s because "
                "an event loop is already running.",
                component_name,
                method_name,
            )

            return

        except RuntimeError:
            pass

        try:

            asyncio.run(awaitable)

        except Exception as exc:

            logger.warning(
                "Async startup failed for %s.%s: %s",
                component_name,
                method_name,
                exc,
            )

    # ========================================================================
    # MAIN EXECUTION PIPELINE
    # ========================================================================

    def execute(
        self,
        command: Any,
        context: Optional[Any] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Main synchronous Omnix execution entry point.

        Both text and voice should eventually reach this method.

        Example:

            engine.execute("Open Chrome")

            engine.execute(
                "What is artificial intelligence?"
            )
        """

        if command is None:

            return self._create_error_result("No command was provided.")

        command_text = str(command).strip()

        if not command_text:

            return self._create_error_result("Command cannot be empty.")

        # --------------------------------------------------------------
        # START ENGINE IF NEEDED
        # --------------------------------------------------------------

        if not self._started:

            self.start()

        # --------------------------------------------------------------
        # BUILD EXECUTION CONTEXT
        # --------------------------------------------------------------

        execution_context = self._build_execution_context(
            command_text,
            context=context,
            **kwargs,
        )

        logger.info("Omnix executing: %s", command_text)

        try:

            # ----------------------------------------------------------
            # 1. MEMORY / CONTEXT ENRICHMENT
            # ----------------------------------------------------------

            self._prepare_execution_context(
                command_text,
                execution_context,
            )

            # ----------------------------------------------------------
            # 2. DETERMINE REQUEST TYPE
            # ----------------------------------------------------------

            request_type = self._determine_request_type(
                command_text,
                execution_context,
            )

            execution_context["request_type"] = request_type

            # ----------------------------------------------------------
            # 3. ROUTE REQUEST
            # ----------------------------------------------------------

            if request_type == "conversation":

                result = self._execute_conversation(
                    command_text,
                    execution_context,
                )

            else:

                result = self._execute_action(
                    command_text,
                    execution_context,
                )

            # ----------------------------------------------------------
            # 4. NORMALIZE RESULT
            # ----------------------------------------------------------

            normalized_result = self._normalize_execution_result(
                result,
                command_text,
                execution_context,
            )

            # ----------------------------------------------------------
            # 5. UPDATE MEMORY / CONTEXT
            # ----------------------------------------------------------

            self._finalize_execution(
                command_text,
                normalized_result,
                execution_context,
            )

            return normalized_result

        except Exception as exc:

            logger.exception(
                "Omnix execution failed: %s",
                exc,
            )

            error_result = self._create_error_result(
                str(exc),
                command=command_text,
            )

            self._finalize_execution(
                command_text,
                error_result,
                execution_context,
            )

            return error_result

    # ========================================================================
    # ASYNC EXECUTION
    # ========================================================================

    async def execute_async(
        self,
        command: Any,
        context: Optional[Any] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Async-compatible execution entry point.

        If the current components provide true async methods,
        they can be integrated here later.

        For now, the synchronous engine pipeline is executed in a
        worker thread so voice/UI async loops are not blocked.
        """

        return await asyncio.to_thread(
            self.execute,
            command,
            context,
            **kwargs,
        )

    # ========================================================================
    # BUILD EXECUTION CONTEXT
    # ========================================================================

    def _build_execution_context(
        self,
        command: str,
        context: Optional[Any] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Build a normalized context dictionary for one execution.
        """

        execution_context: Dict[
            str,
            Any,
        ] = {
            "command": command,
            "timestamp": time.time(),
            "engine": self,
        }

        if isinstance(
            context,
            dict,
        ):

            execution_context.update(context)

        elif context is not None:

            execution_context["context"] = context

        execution_context.update(kwargs)

        return execution_context

    # ========================================================================
    # PREPARE CONTEXT
    # ========================================================================

    def _prepare_execution_context(
        self,
        command: str,
        execution_context: Dict[str, Any],
    ) -> None:
        """
        Enrich the execution context using the context and memory
        systems.

        Failure here must never stop the main command execution.
        """

        # --------------------------------------------------------------
        # CONTEXT SERVICE
        # --------------------------------------------------------------

        if self.context_service is not None:

            for method_name in (
                "get_context",
                "build_context",
                "prepare_context",
            ):

                method = getattr(
                    self.context_service,
                    method_name,
                    None,
                )

                if not callable(method):
                    continue

                try:

                    result = method(command)

                    result = self._resolve_sync_result(result)

                    if isinstance(
                        result,
                        dict,
                    ):

                        execution_context.update(result)

                    elif result is not None:

                        execution_context["context_data"] = result

                    break

                except Exception as exc:

                    logger.debug(
                        "Context preparation failed: %s",
                        exc,
                    )

        # --------------------------------------------------------------
        # MEMORY SERVICE
        # --------------------------------------------------------------

        if self.memory_service is not None:

            try:

                result = self._call_first_available(
                    self.memory_service,
                    (
                        "recall",
                        "search",
                        "retrieve",
                    ),
                    command,
                    limit=5,
                )

                result = self._resolve_sync_result(result)

                memory_value = self._extract_result_value(result)

                if memory_value is not None:

                    execution_context["relevant_memory"] = memory_value

            except Exception as exc:

                logger.debug(
                    "Memory recall failed: %s",
                    exc,
                )

    # ========================================================================
    # REQUEST TYPE DETECTION
    # ========================================================================

    def _determine_request_type(
        self,
        command: str,
        execution_context: Dict[str, Any],
    ) -> str:
        """
        Decide whether a request is primarily:

            conversation
            action

        The IntentClassifier is used first when available.

        If classification fails, a conservative fallback heuristic is
        used so normal conversation does not accidentally trigger
        automation.
        """

        # --------------------------------------------------------------
        # INTENT CLASSIFIER
        # --------------------------------------------------------------

        if self.intent_classifier is not None:

            try:

                result = self._call_first_available(
                    self.intent_classifier,
                    (
                        "classify",
                        "classify_intent",
                        "detect_intent",
                        "analyze",
                    ),
                    command,
                )

                result = self._resolve_sync_result(result)

                detected_type = self._extract_request_type(result)

                if detected_type is not None:

                    return detected_type

            except Exception as exc:

                logger.debug(
                    "Intent classification failed: %s",
                    exc,
                )

        # --------------------------------------------------------------
        # COMMAND PROCESSOR
        # --------------------------------------------------------------

        if self.command_processor is not None:

            try:

                result = self._call_first_available(
                    self.command_processor,
                    (
                        "classify",
                        "analyze",
                        "parse",
                    ),
                    command,
                )

                result = self._resolve_sync_result(result)

                detected_type = self._extract_request_type(result)

                if detected_type is not None:

                    return detected_type

            except Exception as exc:

                logger.debug(
                    "Command analysis failed: %s",
                    exc,
                )

        # --------------------------------------------------------------
        # FALLBACK HEURISTIC
        # --------------------------------------------------------------

        normalized = command.lower().strip()

        action_prefixes = (
            "open ",
            "close ",
            "search ",
            "find ",
            "play ",
            "pause ",
            "stop ",
            "click ",
            "type ",
            "write ",
            "create ",
            "delete ",
            "move ",
            "copy ",
            "rename ",
            "download ",
            "launch ",
            "start ",
            "go to ",
            "navigate ",
            "show me ",
            "take ",
        )

        if normalized.startswith(action_prefixes):

            return "action"

        return "conversation"

    # ========================================================================
    # CONVERSATION EXECUTION
    # ========================================================================

    def _execute_conversation(
        self,
        command: str,
        execution_context: Dict[str, Any],
    ) -> Any:
        """
        Execute a normal conversational request.

        Primary route:

            OmnixEngine
                ↓
            AIService
                ↓
            Brain / AI backend
        """

        if self.ai_service is None:

            return self._create_error_result(
                "AI service is unavailable.",
                command=command,
            )

        methods = (
            "chat",
            "ask",
            "generate",
            "respond",
            "execute",
            "process",
        )

        try:

            result = self._call_first_available(
                self.ai_service,
                methods,
                command,
                context=execution_context,
            )

            return self._resolve_sync_result(result)

        except Exception as exc:

            logger.exception(
                "Conversation execution failed: %s",
                exc,
            )

            return self._create_error_result(
                str(exc),
                command=command,
            )

    # ========================================================================
    # ACTION EXECUTION
    # ========================================================================

    def _execute_action(
        self,
        command: str,
        execution_context: Dict[str, Any],
    ) -> Any:
        """
        Execute an actionable request.

        Preferred route:

            OmnixEngine
                ↓
            AgentController
                ↓
            GoalExecutor / TaskPlanner
                ↓
            AutomationService
                ↓
            Skills / Vision / System

        Fallback route:

            AutomationService
        """

        # --------------------------------------------------------------
        # AGENT CONTROLLER
        # --------------------------------------------------------------

        if self.agent_controller is not None:

            try:

                result = self._call_first_available(
                    self.agent_controller,
                    (
                        "execute",
                        "run",
                        "process",
                        "process_command",
                        "handle_command",
                    ),
                    command,
                    context=execution_context,
                )

                result = self._resolve_sync_result(result)

                if result is not None:

                    return result

            except Exception as exc:

                logger.warning(
                    "AgentController execution failed: %s",
                    exc,
                )

        # --------------------------------------------------------------
        # GOAL EXECUTOR
        # --------------------------------------------------------------

        if self.goal_executor is not None:

            try:

                result = self._call_first_available(
                    self.goal_executor,
                    (
                        "execute",
                        "run",
                        "execute_goal",
                    ),
                    command,
                    context=execution_context,
                )

                result = self._resolve_sync_result(result)

                if result is not None:

                    return result

            except Exception as exc:

                logger.warning(
                    "GoalExecutor execution failed: %s",
                    exc,
                )

        # --------------------------------------------------------------
        # AUTOMATION SERVICE
        # --------------------------------------------------------------

        if self.automation_service is not None:

            try:

                result = self._call_first_available(
                    self.automation_service,
                    (
                        "execute",
                        "run",
                        "process",
                        "execute_command",
                        "handle_command",
                    ),
                    command,
                    context=execution_context,
                )

                return self._resolve_sync_result(result)

            except Exception as exc:

                logger.exception(
                    "Automation execution failed: %s",
                    exc,
                )

                return self._create_error_result(
                    str(exc),
                    command=command,
                )

        return self._create_error_result(
            "No action execution system is available.",
            command=command,
        )

    # ========================================================================
    # RESULT NORMALIZATION
    # ========================================================================

    def _normalize_execution_result(
        self,
        result: Any,
        command: str,
        execution_context: Dict[str, Any],
    ) -> Any:
        """
        Normalize results without destroying the original result type.

        If a result object already provides success/status/text fields,
        it is preserved.

        Raw strings, dictionaries, booleans, and None values are
        converted into a consistent dictionary.
        """

        if result is None:

            return {
                "success": False,
                "command": command,
                "response": ("Omnix could not complete " "the request."),
                "error": "Empty execution result.",
                "request_type": (execution_context.get("request_type")),
            }

        if isinstance(
            result,
            str,
        ):

            return {
                "success": True,
                "command": command,
                "response": result,
                "request_type": (execution_context.get("request_type")),
            }

        if isinstance(
            result,
            bool,
        ):

            return {
                "success": result,
                "command": command,
                "response": ("Task completed." if result else "Task failed."),
                "request_type": (execution_context.get("request_type")),
            }

        if isinstance(
            result,
            dict,
        ):

            normalized = dict(result)

            normalized.setdefault(
                "success",
                normalized.get(
                    "ok",
                    True,
                ),
            )

            normalized.setdefault(
                "command",
                command,
            )

            normalized.setdefault(
                "request_type",
                execution_context.get("request_type"),
            )

            if "response" not in normalized:

                for key in (
                    "message",
                    "text",
                    "result",
                    "output",
                ):

                    if key in normalized:

                        normalized["response"] = normalized[key]

                        break

            return normalized

        # --------------------------------------------------------------
        # RESULT OBJECT
        # --------------------------------------------------------------

        return result

    # ========================================================================
    # FINALIZE EXECUTION
    # ========================================================================

    def _finalize_execution(
        self,
        command: str,
        result: Any,
        execution_context: Dict[str, Any],
    ) -> None:
        """
        Update context and memory after execution.

        These updates are best-effort only and must never change
        the already-produced execution result.
        """

        # --------------------------------------------------------------
        # CONTEXT
        # --------------------------------------------------------------

        if self.context_service is not None:

            try:

                self._call_first_available(
                    self.context_service,
                    (
                        "add_interaction",
                        "update",
                        "record",
                        "remember",
                    ),
                    command,
                    result,
                )

            except Exception:
                pass

        # --------------------------------------------------------------
        # MEMORY
        # --------------------------------------------------------------

        if self.memory_service is not None:

            try:

                response_text = self._extract_response_text(result)

                memory_text = (
                    f"User command: {command}\n" f"Omnix result: {response_text}"
                )

                self._call_first_available(
                    self.memory_service,
                    (
                        "remember",
                        "store",
                        "add_memory",
                    ),
                    memory_text,
                )

            except Exception as exc:

                logger.debug(
                    "Memory update failed: %s",
                    exc,
                )

    # ========================================================================
    # GENERIC METHOD CALLER
    # ========================================================================

    @staticmethod
    def _call_first_available(
        component: Any,
        method_names: tuple,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Call the first compatible method available on a component.
        """

        if component is None:

            raise RuntimeError("Component is unavailable.")

        last_error: Optional[Exception] = None

        for method_name in method_names:

            method = getattr(
                component,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:

                return method(
                    *args,
                    **kwargs,
                )

            except TypeError as exc:

                last_error = exc

                try:

                    return method(*args)

                except TypeError as retry_error:

                    last_error = retry_error

                    continue

        if last_error is not None:

            raise last_error

        raise AttributeError(
            "No supported method found. " f"Tried: {', '.join(method_names)}"
        )

    # ========================================================================
    # RESULT HELPERS
    # ========================================================================

    @staticmethod
    def _extract_result_value(
        result: Any,
    ) -> Any:

        if result is None:
            return None

        if isinstance(
            result,
            dict,
        ):

            for key in (
                "value",
                "result",
                "data",
                "memories",
            ):

                if key in result:

                    return result[key]

            return result

        for attribute_name in (
            "value",
            "result",
            "data",
        ):

            try:

                value = getattr(
                    result,
                    attribute_name,
                    None,
                )

                if value is not None:
                    return value

            except Exception:
                continue

        return result

    @staticmethod
    def _extract_response_text(
        result: Any,
    ) -> str:

        if result is None:
            return ""

        if isinstance(
            result,
            str,
        ):

            return result

        if isinstance(
            result,
            dict,
        ):

            for key in (
                "response",
                "message",
                "text",
                "output",
                "result",
            ):

                value = result.get(key)

                if value is not None:

                    return str(value)

            return str(result)

        for attribute_name in (
            "response",
            "message",
            "text",
            "output",
            "result",
        ):

            try:

                value = getattr(
                    result,
                    attribute_name,
                    None,
                )

                if value is not None:

                    return str(value)

            except Exception:
                continue

        return str(result)

    @staticmethod
    def _extract_request_type(
        result: Any,
    ) -> Optional[str]:
        """
        Convert different classifier outputs into:

            conversation
            action
        """

        if result is None:
            return None

        value = None

        if isinstance(
            result,
            str,
        ):

            value = result

        elif isinstance(
            result,
            dict,
        ):

            for key in (
                "request_type",
                "intent",
                "type",
                "category",
            ):

                if key in result:

                    value = result[key]

                    break

        else:

            for attribute_name in (
                "request_type",
                "intent",
                "type",
                "category",
            ):

                try:

                    value = getattr(
                        result,
                        attribute_name,
                        None,
                    )

                    if value is not None:
                        break

                except Exception:
                    continue

        if value is None:
            return None

        normalized = str(value).strip().lower()

        conversation_values = (
            "conversation",
            "chat",
            "question",
            "qa",
            "ai",
            "general",
            "knowledge",
        )

        action_values = (
            "action",
            "command",
            "automation",
            "task",
            "agent",
            "execution",
        )

        if normalized in conversation_values:

            return "conversation"

        if normalized in action_values:

            return "action"

        return None

    @staticmethod
    def _resolve_sync_result(
        result: Any,
    ) -> Any:
        """
        Resolve an awaitable when execute() is called from normal
        synchronous code.

        If an event loop is already running, the awaitable cannot be
        safely blocked here.
        """

        if not inspect.isawaitable(result):

            return result

        try:

            asyncio.get_running_loop()

        except RuntimeError:

            return asyncio.run(result)

        raise RuntimeError(
            "An async component returned an awaitable while "
            "OmnixEngine.execute() was called from an active "
            "event loop. Use execute_async() instead."
        )

    # ========================================================================
    # ERROR RESULT
    # ========================================================================

    @staticmethod
    def _create_error_result(
        error: str,
        command: Optional[str] = None,
    ) -> Dict[str, Any]:

        return {
            "success": False,
            "command": command,
            "response": ("I couldn't complete that request."),
            "error": str(error),
        }

    # ========================================================================
    # SERVICE / COMPONENT LOOKUP
    # ========================================================================

    def get_service(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Get a core service or registered component by name.

        Examples:

            engine.get_service("memory")
            engine.get_service("voice")
            engine.get_service("vision_service")
        """

        if not name:
            return default

        normalized = str(name).strip().lower()

        aliases = {
            "context": "context_service",
            "memory": "memory_service",
            "ai": "ai_service",
            "brain": "ai_service",
            "skills": "skills_service",
            "automation": "automation_service",
            "vision": "vision_service",
            "voice": "voice_service",
            "memory_manager": "memory_coordinator",
            "memory_coordinator": "memory_coordinator",
            "skills_manager": "skills_manager",
            "automation_engine": "automation_engine",
            "vision_manager": "vision_manager",
            "voice_manager": "voice_manager",
            "brain_manager": "brain_manager",
            "agent": "agent_controller",
            "agent_controller": "agent_controller",
            "planner": "task_planner",
            "task_planner": "task_planner",
        }

        attribute_name = aliases.get(
            normalized,
            normalized,
        )

        component = getattr(
            self,
            attribute_name,
            None,
        )

        if component is not None:
            return component

        return self._components.get(
            attribute_name,
            default,
        )

    def get_component(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Compatibility alias for component lookup.
        """

        return self.get_service(
            name,
            default,
        )

    def has_component(
        self,
        name: str,
    ) -> bool:

        return (
            self.get_service(
                name,
                None,
            )
            is not None
        )

    # ========================================================================
    # COMPONENT STATUS
    # ========================================================================

    def _get_component_health(
        self,
        component: Any,
    ) -> bool:
        """
        Determine whether a component appears healthy.
        """

        if component is None:
            return False

        for method_name in (
            "health",
            "health_check",
            "is_healthy",
            "status",
        ):

            method = getattr(
                component,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:

                result = method()

                if inspect.isawaitable(result):

                    logger.warning(
                        "Async health method detected for %s.",
                        type(component).__name__,
                    )

                    return True

                if isinstance(result, bool):
                    return result

                if isinstance(result, dict):

                    for key in (
                        "healthy",
                        "success",
                        "ok",
                        "running",
                    ):

                        if key in result:
                            return bool(result[key])

                    return True

                if result is None:
                    continue

                return bool(result)

            except Exception:
                return False

        # If the object exists and has no explicit health method,
        # consider it available.
        return True

    def health_status(
        self,
    ) -> Dict[str, Any]:
        """
        Return Omnix compatibility health information.

        This method keeps the structure simple so existing startup
        tests and main.py code can continue using:

            engine.health_status()
        """

        system_health = (
            self._get_component_health(self.system) if self.system is not None else True
        )

        context_health = self._get_component_health(self.context_service)

        memory_health = self._get_component_health(self.memory_service)

        brain_health = self._get_component_health(self.ai_service)

        vision_health = self._get_component_health(self.vision_service)

        voice_health = self._get_component_health(self.voice_service)

        agent_component = (
            self.agent_controller or self.goal_executor or self.automation_service
        )

        agent_health = self._get_component_health(agent_component)

        return {
            "system": system_health,
            "context": context_health,
            "memory": memory_health,
            "brain": brain_health,
            "vision": vision_health,
            "agent": agent_health,
            "voice": voice_health,
            "running": self._started,
        }

    def status(
        self,
    ) -> Dict[str, Any]:
        """
        Return detailed engine status.
        """

        health = self.health_status()

        components = {}

        for name, component in self._components.items():

            components[name] = {
                "available": component is not None,
                "healthy": (self._get_component_health(component)),
                "type": (type(component).__name__ if component is not None else None),
            }

        uptime = None

        if self._started_at is not None:

            uptime = max(
                0.0,
                time.time() - self._started_at,
            )

        return {
            "running": self._started,
            "initializing": self._initializing,
            "shutting_down": self._shutting_down,
            "uptime_seconds": uptime,
            "health": health,
            "components": components,
            "startup_errors": dict(self._startup_errors),
        }

    def health(
        self,
    ) -> Dict[str, Any]:
        """
        Generic health interface.
        """

        status = self.health_status()

        important_components = (
            "context",
            "memory",
            "brain",
            "agent",
        )

        healthy = all(
            status.get(
                name,
                False,
            )
            for name in important_components
        )

        return {
            "healthy": healthy,
            "running": self._started,
            "components": status,
        }

    # ========================================================================
    # SHUTDOWN
    # ========================================================================

    def shutdown(
        self,
    ) -> bool:
        """
        Gracefully shut down Omnix.

        Shutdown is performed in reverse dependency order so high-level
        execution systems stop before the services and backends they use.
        """

        if self._shutting_down:
            return False

        if not self._started and not self._components:
            return True

        self._shutting_down = True

        logger.info("Shutting down Omnix V5...")

        shutdown_success = True

        try:

            shutdown_order = (
                "agent_controller",
                "goal_executor",
                "workflow_planner",
                "task_planner",
                "target_resolver",
                "intent_classifier",
                "command_processor",
                "voice_service",
                "vision_service",
                "automation_service",
                "skills_service",
                "ai_service",
                "memory_service",
                "context_service",
            )

            stopped_components = set()

            for component_name in shutdown_order:

                component = getattr(
                    self,
                    component_name,
                    None,
                )

                if component is None:
                    continue

                stopped_components.add(id(component))

                if not self._shutdown_component(
                    component_name,
                    component,
                ):

                    shutdown_success = False

            # Stop any remaining components that were not covered
            # by the main shutdown order.

            for (
                component_name,
                component,
            ) in list(self._components.items()):

                if component is None:
                    continue

                if id(component) in stopped_components:
                    continue

                if not self._shutdown_component(
                    component_name,
                    component,
                ):

                    shutdown_success = False

            self._started = False

            self._started_at = None

            logger.info("Omnix V5 shutdown complete.")

            return shutdown_success

        finally:

            self._shutting_down = False

    def stop(
        self,
    ) -> bool:
        """
        Compatibility alias.
        """

        return self.shutdown()

    def close(
        self,
    ) -> bool:
        """
        Compatibility alias.
        """

        return self.shutdown()

    def _shutdown_component(
        self,
        component_name: str,
        component: Any,
    ) -> bool:
        """
        Shut down one component safely.
        """

        for method_name in (
            "shutdown",
            "stop",
            "close",
        ):

            method = getattr(
                component,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:

                result = method()

                if inspect.isawaitable(result):

                    try:

                        asyncio.get_running_loop()

                        logger.warning(
                            "Cannot synchronously await shutdown "
                            "for %s.%s because an event loop is "
                            "already running.",
                            component_name,
                            method_name,
                        )

                    except RuntimeError:

                        asyncio.run(result)

                logger.debug(
                    "Stopped component: %s",
                    component_name,
                )

                return True

            except Exception as exc:

                logger.warning(
                    "Failed to stop %s: %s",
                    component_name,
                    exc,
                )

                return False

        return True

    # ========================================================================
    # CONTEXT MANAGER SUPPORT
    # ========================================================================

    def __enter__(
        self,
    ) -> "OmnixEngine":

        self.start()

        return self

    def __exit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> None:

        self.shutdown()

    # ========================================================================
    # REPRESENTATION
    # ========================================================================

    def __repr__(
        self,
    ) -> str:

        return (
            f"<OmnixEngine "
            f"running={self._started} "
            f"components={len(self._components)}>"
        )


# ============================================================================
# ENGINE FACTORY
# ============================================================================


def create_engine(
    config: Optional[Dict[str, Any]] = None,
    auto_start: bool = False,
    **kwargs: Any,
) -> OmnixEngine:
    """
    Create and return the main Omnix V5 engine.

    Example:

        engine = create_engine(
            auto_start=True
        )

        result = engine.execute(
            "Open Chrome"
        )
    """

    return OmnixEngine(
        config=config,
        auto_start=auto_start,
        **kwargs,
    )


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    "OmnixEngine",
    "create_engine",
]
