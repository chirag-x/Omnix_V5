from loguru import logger
from skills.manager.skill_manager import SkillManager
from core.retry_manager import RetryManager
from core.error_handler import ErrorHandler
from core.execution_context import ExecutionContext
from core.goal_verifier import GoalVerifier
from core.goal_verifier import GoalStatus
from core.observation_loop import ObservationLoop
from core.recovery_engine import RecoveryEngine
from core.step_verifier import StepVerifier
from core.step_verifier import VerificationStatus
from core.wait_engine import WaitEngine


class GoalExecutor:

    def __init__(
        self,
        skill_manager=None,
        dependencies=None,
        execution_context: ExecutionContext | None = None,
    ):

        logger.info("[GoalExecutor] Initializing")

        dependencies = dependencies or {}
        self.execution_context = execution_context or dependencies.get(
            "execution_context"
        )

        if self.execution_context is None:
            raise ValueError("[GoalExecutor] Shared ExecutionContext is required")

        self.skill_manager = skill_manager or SkillManager(
            {
                **dependencies,
                "execution_context": self.execution_context,
            }
        )
        self.retry_manager = RetryManager()
        self.error_handler = ErrorHandler()
        self.vision_manager = dependencies.get("vision_manager")
        self.ui_controller = dependencies.get("ui_controller")
        self.wait_engine = dependencies.get("wait_engine") or WaitEngine(
            vision_manager=self.vision_manager,
            ui_controller=self.ui_controller,
            execution_context=self.execution_context,
        )
        self.observation_loop = dependencies.get("observation_loop") or ObservationLoop(
            vision_manager=self.vision_manager,
            ui_controller=self.ui_controller,
            execution_context=self.execution_context,
        )
        self.step_verifier = dependencies.get("step_verifier") or StepVerifier(
            ui_controller=self.ui_controller,
            execution_context=self.execution_context,
        )
        self.goal_verifier = dependencies.get("goal_verifier") or GoalVerifier(
            ui_controller=self.ui_controller,
            execution_context=self.execution_context,
        )
        self.recovery_engine = dependencies.get("recovery_engine") or RecoveryEngine()

        self.running = True

    # ------------------------------------------------
    # Execute full plan
    # ------------------------------------------------

    def execute_plan(self, plan, goal=None):

        logger.info("[GoalExecutor] Starting goal execution")

        if not plan:

            logger.warning("[GoalExecutor] Empty execution plan")

            return "error"

        observation = self.observe()

        for step_index, step in enumerate(plan):

            if not self.running:
                logger.warning("[GoalExecutor] Goal execution stopped")
                break

            logger.info(f"[GoalExecutor] Executing step {step_index + 1}: {step}")

            result = self.execute_step(step, previous_observation=observation)
            observation = self.observation_loop.last_observation or observation

            if result == "error":

                logger.error("[GoalExecutor] Goal execution failed")

                return "error"

        goal_result = self.verify_goal(goal, observation) if goal else None

        if goal_result:

            if goal_result.status == GoalStatus.FAILED:
                logger.error(f"[GoalExecutor] Goal verification failed: {goal_result}")
                return "error"

            if goal_result.status == GoalStatus.PARTIAL:
                logger.warning(f"[GoalExecutor] Goal partially verified: {goal_result}")
                return "error"

        logger.info("[GoalExecutor] Goal execution finished")

        return "success"

    def _get_skill_name(self, skill):
        """
        Converts V5 skill IDs and legacy names
        into a common name for context updates.
        """

        aliases = {
            "builtin.applications.open": "open_app",
            "builtin.applications.close": "close_app",
            "builtin.applications.switch": "switch_app",
            "builtin.browser.action": "browser_action",
            "builtin.browser.open": "open_browser",
            "builtin.browser.search": "search_web",
            "builtin.input.type_text": "type_text",
            "builtin.vision.click_ui": "click_ui",
            "builtin.input.click": "click_mouse",
            "builtin.input.double_click": "double_click",
            "builtin.input.drag": "drag_mouse",
            "builtin.input.press_key": "press_key",
            "builtin.input.hotkey": "hotkey",
            "builtin.files.open_file": "open_file",
            "builtin.files.create_file": "create_file",
            "builtin.files.search_file": "search_file",
            "builtin.system.shutdown": "shutdown",
            "builtin.system.restart": "restart",
        }

        return aliases.get(skill, skill)

    # ------------------------------------------------
    # Update execution context
    # ------------------------------------------------

    def _update_execution_context(self, step, result):
        """
        Update runtime context after every successfully executed skill.
        """

        if result == "error":
            return

        skill = self._get_skill_name(step.get("skill"))
        params = step.get("parameters", {})

        ctx = self.execution_context

        ctx.last_skill = skill
        ctx.last_result = result
        ctx.last_action = skill

        # -----------------------
        # Applications
        # -----------------------

        if skill == "open_app":

            app = params.get("app")
            browser = ctx.normalize_browser(app)

            ctx.current_app = browser or app
            ctx.set_browser(browser)

        elif skill == "close_app":

            app = params.get("app")
            closed_app = ctx.normalize_browser(app) or app

            if ctx.current_app == closed_app:

                ctx.current_app = None

            if ctx.current_browser == ctx.normalize_browser(app):

                ctx.set_browser(None)

        # -----------------------
        # Browser
        # -----------------------

        elif skill == "browser_action":

            action = str(params.get("action", "open_browser")).lower()
            browser = (
                params.get("browser") or ctx.current_browser or ctx.DEFAULT_BROWSER
            )

            ctx.set_browser(browser)
            ctx.current_app = ctx.current_browser

            if action == "search":

                ctx.last_search = params.get("query") or params.get("text")
                ctx.set_current_url(None)

            elif action in {"open_url", "navigate", "go_to"}:

                url = params.get("url")

                ctx.set_current_url(url)

            elif action in {
                "back",
                "forward",
                "new_tab",
                "close_tab",
                "next_tab",
                "previous_tab",
            }:
                ctx.set_current_url(None)

        # -----------------------
        # UI
        # -----------------------

        elif skill == "click_ui":

            ctx.selected_element = params.get("text")

        elif skill == "type_text":

            ctx.focused_element = "text_input"

    # ------------------------------------------------
    # Execute single step
    # ------------------------------------------------

    def execute_step(self, step, previous_observation=None):

        try:

            step = self._prepare_step(step)
            before = previous_observation or self.observe()
            result = self._execute_skill_once(step)

            if result == "error":
                if self.retry_manager.should_retry(step):
                    logger.warning("[GoalExecutor] Retrying step")
                    result = self._execute_skill_once(step)

            after = self.observe(before)
            verification = self.step_verifier.verify(
                step=step,
                result=result,
                before=before,
                after=after,
            )

            if self._requires_recovery(step, result, verification):
                recovery_result = self._recover_step(step, verification, after)

                if recovery_result != "error":
                    result = recovery_result
                    after = self.observation_loop.last_observation or after
                    verification = self.step_verifier.verify(
                        step=step,
                        result=result,
                        before=before,
                        after=after,
                    )

            if result == "error" or verification.status == VerificationStatus.FAILED:
                logger.error("[GoalExecutor] Step failed permanently")
                return "error"

            self._update_execution_context(step, result)

            return result

        except Exception as e:

            logger.exception("[GoalExecutor] Unexpected execution error")

            self.error_handler.handle(e, step)

            return "error"

    def _execute_skill_once(self, step):

        result = self.skill_manager.execute_skill(step)

        if result is None:
            return "success"

        if hasattr(result, "success"):

            return "success" if bool(result.success) else "error"

        if isinstance(result, bool):

            return "success" if result else "error"

        return result

    def _requires_recovery(self, step, result, verification):

        if result == "error":
            return self.recovery_engine.can_recover(step, verification)

        if verification.status == VerificationStatus.FAILED:
            return self.recovery_engine.can_recover(step, verification)

        if step.get("expected") and verification.status == VerificationStatus.PARTIAL:
            return self.recovery_engine.can_recover(step, verification)

        return False

    def _recover_step(self, step, verification, observation):
        steps = self.recovery_engine.recovery_steps(step, verification)

        if not steps:
            return "error"

        for recovery_step in steps:
            recovery_step = self._prepare_step(recovery_step)
            logger.info(f"[Recovery] Executing recovery step: {recovery_step}")
            result = self._execute_skill_once(recovery_step)
            self.observe(observation)

            if result != "error":
                return result

        return "error"

    def observe(self, previous_observation=None):
        return self.observation_loop.observe(previous_observation)

    def verify_goal(self, goal, observation=None):
        return self.goal_verifier.verify(goal, observation)

    def _prepare_step(self, step):
        if hasattr(self.skill_manager, "normalize_step"):
            step = self.skill_manager.normalize_step(step)

        if step.get("skill") not in (
            "browser_action",
            "builtin.browser.action",
        ):
            return step

        params = dict(step.get("parameters", {}) or {})

        params["browser"] = (
            self.execution_context.normalize_browser(params.get("browser"))
            or self.execution_context.current_browser
            or self.execution_context.DEFAULT_BROWSER
        )

        prepared = dict(step)

        prepared["skill"] = step.get("skill")
        prepared["parameters"] = params

        for key in ("expected", "verify"):
            if key in step:
                prepared[key] = step[key]

        return prepared

    # ------------------------------------------------
    # Execute  skill
    # ------------------------------------------------

    def execute_skill(self, step):

        return self.execute_step(step)

    # ------------------------------------------------
    # Stop execution
    # ------------------------------------------------

    def stop(self):

        logger.warning("[GoalExecutor] Stopping goal execution")

        self.running = False
