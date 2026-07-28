from loguru import logger
import time
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

    def initialize(self):

        logger.info("[OmnixEngine] Initializing")

        warnings.filterwarnings("ignore")

        try:
            transformers.logging.set_verbosity_error()
        except Exception:
            pass

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
            self.observer,
            execution_context=self.execution_context,
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
        )

        logger.success("[OmnixEngine] Agent Controller initialized")

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

    def start(self):

        logger.info("[OmnixEngine] Starting")

        self.running = True

        try:

            if self.vision:
                self.vision.start()
                logger.success("[OmnixEngine] Vision started")

            time.sleep(2)

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

    # ==========================================================
    # Shutdown
    # ==========================================================

    def shutdown(self):

        logger.info("[OmnixEngine] Stopping")

        self.running = False

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
