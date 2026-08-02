from loguru import logger
import time
import asyncio
import warnings
import transformers
from core.execution_context import ExecutionContext


class OmnixEngine:
    """
    Omnix V4 Central Lifecycle Manager

    Responsibilities:
    -----------------
    - Initialize all core modules
    - Start required services
    - Keep Omnix alive
    - Shutdown gracefully

    NOTE:
    Business logic DOES NOT belong here.
    This class only manages the application lifecycle.
    """

    def __init__(self):

        self.running = False

        self.system = None
        self.context = None
        self.memory = None
        self.brain = None
        self.conversation = None
        self.observer = None
        self.vision = None
        self.agent = None
        self.voice = None

    # ==========================================================
    # Initialize
    # ==========================================================

    async def initialize(self):

        logger.info("[OmnixEngine] Initializing")

        warnings.filterwarnings("ignore")

        try:
            transformers.logging.set_verbosity_error()
        except Exception:
            pass

        # -----------------------------
        # V5 System Core
        # -----------------------------
        from system.system_manager import SystemManager

        self.system = SystemManager()

        self.system.start()

        logger.success("[OmnixEngine] V5 System Manager initialized")

        # -----------------------------
        # Context
        # -----------------------------
        from context.context_manager import ContextManager

        self.context = ContextManager()

        logger.success("[OmnixEngine] Context Manager initialized")

        # -----------------------------
        # Memory
        # -----------------------------
        from memory.memory_manager import MemoryManager

        self.memory = MemoryManager()

        logger.success("[OmnixEngine] Memory Manager initialized")
        # -----------------------------
        # Brain
        # -----------------------------
        from ai.brain_manager import BrainManager

        self.brain = BrainManager()

        logger.success("[OmnixEngine] Brain Manager initialized")
        # -----------------------------
        # Conversation
        # -----------------------------
        from core.conversation_manager import ConversationManager

        self.conversation = ConversationManager(self.memory)

        logger.success("[OmnixEngine] Conversation Manager initialized")

        # -----------------------------
        # Shared Execution Context
        # -----------------------------
        self.execution_context = ExecutionContext()

        logger.success("[OmnixEngine] ExecutionContext initialized")
        # -----------------------------
        # Vision
        # -----------------------------
        from vision.screen_observer import ScreenObserver
        from vision.vision_manager import VisionManager

        self.observer = ScreenObserver()
        self.vision = VisionManager(
            observer=self.observer,
            execution_context=self.execution_context,
            window_manager=self.system.windows,
        )

        logger.success("[OmnixEngine] Vision Manager initialized")

        # -----------------------------
        # Agent
        # -----------------------------
        from core.agent_controller import AgentController

        self.agent = AgentController(
            vision_manager=self.vision,
            memory_manager=self.memory,
            context_manager=self.context,
            brain_manager=self.brain,
            conversation_manager=self.conversation,
            execution_context=self.execution_context,
            system_manager=self.system,
        )

        logger.success("[OmnixEngine] Agent Controller initialized")
        await self.agent.initialize()
        logger.info(f"[OmnixEngine] Loaded {self.agent.skills.skill_count()} skills")

        logger.success("[OmnixEngine] Agent skills initialized")

        # -----------------------------
        # Voice
        # -----------------------------
        from voice.voice_manager import VoiceManager

        self.voice = VoiceManager(self.agent)

        logger.success("[OmnixEngine] Voice Manager initialized")

        logger.success("[OmnixEngine] Initialization complete")

    # ==========================================================
    # Start
    # ==========================================================

    async def start(self):

        logger.info("[OmnixEngine] Starting")

        self.running = True

        try:

            if self.vision:

                self.vision.start()

                logger.success("[OmnixEngine] Vision started")

            await asyncio.sleep(2)

            if self.voice:
                self.voice.start()
                logger.success("[OmnixEngine] Voice started")

            logger.success("[OmnixEngine] Omnix is online")

        except Exception as e:

            logger.exception(f"[OmnixEngine] Startup failed: {e}")
            self.shutdown()

    # ==========================================================
    # Main Loop
    # ==========================================================

    def run(self):

        try:

            while self.running:
                time.sleep(1)

        except KeyboardInterrupt:

            logger.info("[OmnixEngine] Shutdown requested by user")

            self.shutdown()

    def health_status(self):
        """
        Returns current Omnix subsystem status.
        """

        return {
            "system": self.system is not None,
            "context": self.context is not None,
            "memory": self.memory is not None,
            "brain": self.brain is not None,
            "vision": self.vision is not None,
            "agent": self.agent is not None,
            "voice": self.voice is not None,
            "running": self.running,
        }

    # ==========================================================
    # Shutdown
    # ==========================================================

    def shutdown(self):

        logger.info("[OmnixEngine] Stopping")

        self.running = False

        # -----------------------------
        # Agent
        # -----------------------------
        try:

            if self.agent and hasattr(self.agent, "agent_loop"):

                self.agent.agent_loop.running = False

                logger.success("[OmnixEngine] Agent stopped")

        except Exception as e:

            logger.exception(f"[OmnixEngine] Agent shutdown failed: {e}")

        # -----------------------------
        # Voice
        # -----------------------------
        try:
            if self.voice:
                self.voice.shutdown()
                logger.success("[OmnixEngine] Voice stopped")
        except Exception as e:
            logger.exception(f"[OmnixEngine] Voice shutdown failed: {e}")

        # -----------------------------
        # Vision
        # -----------------------------
        try:
            if self.vision and hasattr(self.vision, "stop"):
                self.vision.stop()
                logger.success("[OmnixEngine] Vision stopped")
        except Exception as e:
            logger.exception(f"[OmnixEngine] Vision shutdown failed: {e}")

        logger.success("[OmnixEngine] Shutdown complete")

        # -----------------------------

        # V5 System Core
        # -----------------------------
        try:
            if self.system:
                self.system.shutdown()
                logger.success("[OmnixEngine] System Manager stopped")
        except Exception as e:
            logger.exception(f"[OmnixEngine] System shutdown failed: {e}")
