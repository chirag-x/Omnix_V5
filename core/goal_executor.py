from loguru import logger
from skills.skill_manager import SkillManager
from core.retry_manager import RetryManager
from core.error_handler import ErrorHandler
from core.execution_context import ExecutionContext


class GoalExecutor:

    def __init__(
        self,
        skill_manager=None,
        dependencies=None,
        execution_context: ExecutionContext | None = None,
    ):

        logger.info("[GoalExecutor] Initializing")

        dependencies = dependencies or {}
        self.execution_context = execution_context or dependencies.get("execution_context")

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

        self.running = True

    # ------------------------------------------------
    # Execute full plan
    # ------------------------------------------------

    def execute_plan(self, plan):

        logger.info("[GoalExecutor] Starting goal execution")

        for step_index, step in enumerate(plan):

            if not self.running:
                logger.warning("[GoalExecutor] Goal execution stopped")
                break

            logger.info(f"[GoalExecutor] Executing step {step_index + 1}: {step}")

            result = self.execute_step(step)

            if result == "error":

                logger.error("[GoalExecutor] Goal execution failed")

                return "error"

        logger.info("[GoalExecutor] Goal execution finished")

        return "success"

    # ------------------------------------------------
    # Update execution context
    # ------------------------------------------------

    def _update_execution_context(self, step, result):
        """
        Update runtime context after every successfully executed skill.
        """

        if result == "error":
            return

        skill = step.get("skill")
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
            browser = params.get("browser") or ctx.current_browser or ctx.DEFAULT_BROWSER

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

    def execute_step(self, step):

        try:

            step = self._prepare_step(step)
            result = self.skill_manager.execute_skill(step)

            if result == "error":
                if self.retry_manager.should_retry(step):
                    logger.warning("[GoalExecutor] Retrying step")
                    result = self.skill_manager.execute_skill(step)

            self._update_execution_context(step, result)

            if result == "error":
                logger.error("[GoalExecutor] Step failed permanently")
                return "error"

            return result

        except Exception as e:

            self.error_handler.handle(e, step)

            return "error"

    def _prepare_step(self, step):
        if hasattr(self.skill_manager, "normalize_step"):
            step = self.skill_manager.normalize_step(step)

        if step.get("skill") != "browser_action":
            return step

        params = dict(step.get("parameters", {}) or {})

        params["browser"] = (
            self.execution_context.normalize_browser(params.get("browser"))
            or self.execution_context.current_browser
            or self.execution_context.DEFAULT_BROWSER
        )

        return {"skill": "browser_action", "parameters": params}

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
