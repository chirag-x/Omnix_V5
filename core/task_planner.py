import json

from loguru import logger
from dataclasses import asdict

from core.command_processor import CommandProcessor
from core.execution_context import ExecutionContext


class TaskPlanner:
    """
    Omnix V5 Task Planner

    Responsibilities:
    - Convert user goals into executable skill plans
    - Maintain compatibility with old skill names
    - Use SkillManager as the source of truth
    - Provide context-aware planning
    """

    # --------------------------------------------------
    # Legacy -> V5 Skill Mapping
    #
    # LLMs naturally generate old names.
    # These aliases convert them into real V5 skills.
    # --------------------------------------------------

    SKILL_ALIASES = {
        # Applications
        "open_app": "builtin.applications.open",
        "close_app": "builtin.applications.close",
        "switch_app": "builtin.applications.switch",
        # Browser
        "browser_action": "builtin.browser.action",
        "open_browser": "builtin.browser.open",
        "search_web": "builtin.browser.search",
        "browser_search": "builtin.browser.search",
        # Files
        "create_file": "builtin.files.create_file",
        "open_file": "builtin.files.open_file",
        "search_file": "builtin.files.search_file",
        # Input
        "type_text": "builtin.input.type_text",
        "press_key": "builtin.input.press_key",
        "click_mouse": "builtin.input.click",
        "click": "builtin.input.click",
        "double_click": "builtin.input.double_click",
        "right_click": "builtin.input.right_click",
        "middle_click": "builtin.input.middle_click",
        "move_mouse": "builtin.input.move_mouse",
        "drag_mouse": "builtin.input.drag",
        "hotkey": "builtin.input.hotkey",
        "copy": "builtin.input.copy",
        "cut": "builtin.input.cut",
        "paste": "builtin.input.paste",
        "undo": "builtin.input.undo",
        "redo": "builtin.input.redo",
        "select_all": "builtin.input.select_all",
        "scroll_page": "builtin.input.scroll",
        # Vision
        "click_ui": "builtin.vision.click_ui",
        "find_element": "builtin.vision.find_element",
        "wait_for_ui": "builtin.vision.wait_ui",
        # System
        "system_info": "builtin.system.system_info",
        "lock": "builtin.system.lock",
        "sleep": "builtin.system.sleep",
        "restart": "builtin.system.restart",
        "shutdown": "builtin.system.shutdown",
    }

    # Human readable descriptions.
    # Used only when generating planner prompts.

    SKILL_DESCRIPTIONS = {
        "builtin.applications.open": "Open a desktop application. Parameters: app",
        "builtin.applications.close": "Close a running application. Parameters: app",
        "builtin.browser.search": "Search the web. Parameters: query",
        "builtin.browser.open": "Open browser. Parameters: browser",
        "builtin.files.create_file": "Create a file. Parameters: path, content",
        "builtin.files.open_file": "Open a file. Parameters: path",
        "builtin.input.type_text": "Type text. Parameters: text",
        "builtin.input.click": "Click coordinates. Parameters: x,y",
        "builtin.vision.click_ui": "Click visible UI element. Parameters: target",
        "builtin.vision.find_element": "Find UI element. Parameters: target",
        "builtin.vision.wait_ui": "Wait for UI element. Parameters: target",
    }

    def __init__(
        self,
        brain_manager,
        command_processor=None,
        available_skills=None,
        execution_context=None,
        skill_manager=None,
    ):

        logger.info("[Planner] Initializing")

        self.brain = brain_manager

        self.command_processor = command_processor or CommandProcessor()

        # V5 SkillManager connection

        self.skill_manager = skill_manager

        # Runtime loaded skills

        self.allowed_skills = set(available_skills or [])

        self.execution_context = execution_context

        self.max_plan_steps = 20

    def set_available_skills(
        self,
        skills=None,
    ):
        """
        Update planner skills from SkillManager.

        SkillManager is the source of truth.
        """

        loaded = set()

        # Direct list provided

        if skills:

            loaded.update(skills)

        # Pull from SkillManager

        elif self.skill_manager:

            try:

                loaded.update(self.skill_manager.list_skills())

            except Exception as e:

                logger.warning(f"Could not load skills from SkillManager: {e}")

        self.allowed_skills = loaded
        self.available_skills = self.allowed_skills

        logger.info(f"[Planner] Loaded {len(self.allowed_skills)} skills")

        return self.allowed_skills

    def _available_skills_text(self):
        """
        Creates LLM readable skill list.

        Uses actual V5 loaded skills.
        """

        if not self.allowed_skills:

            return "No skills available."

        lines = []

        skills = []

        for skill in self.allowed_skills:

            if isinstance(skill, str):

                skills.append(skill)

            else:

                try:
                    skills.append(skill.metadata.id)
                except Exception:
                    skills.append(skill.__name__)

        for skill in sorted(skills):

            description = self.SKILL_DESCRIPTIONS.get(
                skill, "No description available."
            )

            lines.append(f"- {skill}: {description}")

        return "\n".join(lines)

    def _normalize_action(
        self,
        action,
    ):
        """
        Convert planner/LLM actions into
        valid V5 skill actions.
        """

        if not isinstance(action, dict):
            return None

        action = dict(action)

        # Support multiple LLM formats

        skill = (
            action.get("skill")
            or action.get("action")
            or action.get("tool")
            or action.get("name")
        )

        if not skill:

            return None

        skill = str(skill).strip()

        # Convert legacy name -> V5 skill

        normalized_skill = self.SKILL_ALIASES.get(skill, skill)

        action["skill"] = normalized_skill

        # Normalize parameters

        if "parameters" not in action:

            if "params" in action:

                action["parameters"] = action.pop("params")

            elif "args" in action:

                action["parameters"] = action.pop("args")

            else:

                action["parameters"] = {}

        # Ensure dictionary

        if not isinstance(action["parameters"], dict):

            action["parameters"] = {}

        return action

    def _normalize_plan(
        self,
        plan,
    ):
        """
        Normalize complete execution plan.
        """

        if not isinstance(plan, list):
            return []

        normalized = []

        for step in plan:

            action = self._normalize_action(step)

            if action:

                normalized.append(action)

        return normalized

    def _ensure_expected(
        self,
        action,
    ):
        """
        Add default verification data
        for V5 skill execution.
        """

        if not isinstance(action, dict):
            return action

        if "expected" in action and action["expected"]:

            return action

        skill = action.get("skill", "")

        parameters = action.get("parameters", {})

        expected = {}

        # -----------------------------
        # Application skills
        # -----------------------------

        if skill == "builtin.applications.open":

            expected = {
                "application_open": (
                    parameters.get("app") or parameters.get("application")
                )
            }

        elif skill == "builtin.applications.close":

            expected = {
                "application_closed": (
                    parameters.get("app") or parameters.get("application")
                )
            }

        # -----------------------------
        # Browser skills
        # -----------------------------

        elif skill in (
            "builtin.browser.search",
            "builtin.browser.action",
        ):

            expected = {"browser_action": "search_completed"}

        elif skill == "builtin.browser.open":

            expected = {"browser_open": True}

        # -----------------------------
        # Files
        # -----------------------------

        elif skill == "builtin.files.create_file":

            expected = {"file_created": (parameters.get("path"))}

        elif skill == "builtin.files.open_file":

            expected = {"file_opened": (parameters.get("path"))}

        # -----------------------------
        # Input
        # -----------------------------

        elif skill == "builtin.input.type_text":

            expected = {"text_typed": True}

        elif skill == "builtin.input.click":

            expected = {"click_completed": True}

        # -----------------------------
        # Vision
        # -----------------------------

        elif skill == "builtin.vision.find_element":

            expected = {
                "element_found": (parameters.get("element") or parameters.get("target"))
            }

        elif skill == "builtin.vision.click_ui":

            expected = {
                "element_clicked": (
                    parameters.get("element") or parameters.get("target")
                )
            }

        # -----------------------------
        # System
        # -----------------------------

        elif skill.startswith("builtin.system."):

            expected = {"system_action_completed": True}

        else:

            expected = {"completed": True}

        action["expected"] = expected

        return action

    def _inject_runtime_context(self, context):

        runtime = {}

        execution_context = getattr(self, "execution_context", None)

        if execution_context:

            runtime = execution_context.to_dict()

        context = dict(context or {})

        context["runtime"] = runtime

        return context

    def _optimize_plan(self, plan):
        """
        Optimize a rule-generated plan using the current execution context.
        """
        plan = [self._ensure_expected(step) for step in plan]
        if not plan:
            return plan

        execution_context = getattr(self, "execution_context", None)

        if not execution_context:
            return plan

        optimized = []

        current_browser = execution_context.current_browser

        for step in plan:

            skill = step.get("skill")
            params = step.get("parameters", {})

            # ---------------------------------
            # Skip reopening the same app
            # ---------------------------------

            if skill == "builtin.applications.open":

                app = params.get("app")

                if execution_context.is_app_active(app):

                    logger.info(
                        f"[Planner] Skipping open_app('{app}') because it is already active"
                    )

                    continue

            # ---------------------------------
            # Browser already exists
            # ---------------------------------

            if skill == "builtin.browser.action":

                if current_browser:

                    logger.info(f"[Planner] Using existing browser: {current_browser}")

            optimized.append(step)

        return optimized

    # ------------------------------------------------
    # Create rule plan
    # ------------------------------------------------

    def _create_rule_plan(self, command):
        """
        Create an execution plan without using the LLM.
        Returns None if the command isn't supported by rule-based planning.
        """

        structured = self.command_processor.process(command)

        plan = self._rule_engine(structured)

        if plan:
            plan = self._normalize_plan(plan)
            plan = self._optimize_plan(plan)

            logger.info("[Planner] Using rule planner")

            return plan

        return None

    # ------------------------------------------------
    # Rule Engine
    # ------------------------------------------------

    def _rule_engine(
        self,
        command,
    ):
        """
        Fast rule-based planner.

        Uses StructuredCommand instead of the old
        CommandProcessor plan generation.
        """

        if command.intent != "automation":
            return None

        plan = []

        if command.action == "open":

            plan.append(
                {
                    "skill": "builtin.applications.open",
                    "parameters": {"app": command.application},
                }
            )

        elif command.action == "click":

            plan.append(
                {
                    "skill": "builtin.vision.click_ui",
                    "parameters": {"target": command.target},
                }
            )

        elif command.action == "search":

            plan.append(
                {
                    "skill": "builtin.browser.search",
                    "parameters": {"query": command.query},
                }
            )

        elif command.action == "type":

            plan.append(
                {
                    "skill": "builtin.input.type_text",
                    "parameters": {"text": command.text},
                }
            )

        return self._normalize_plan(plan)

    # ------------------------------------------------
    # Create full plan
    # ------------------------------------------------

    def create_plan(self, command, context=None):
        context = self._inject_runtime_context(context)
        workflow_plan = self._create_workflow_plan(command)

        if workflow_plan:
            return workflow_plan

        system_context = None
        vision_frame = None

        vision_context = ""
        screen_state = ""

        ui_elements = []
        known_patterns = []

        runtime_context = {}

        if context:

            runtime_context = context.get("runtime", {})

            system_context = context.get("system")

            vision_frame = context.get("vision")

            if vision_frame:

                vision_context = vision_frame.summary or ""

                if vision_frame.screen_state:
                    try:
                        screen_state = json.dumps(
                            asdict(vision_frame.screen_state),
                            indent=2,
                        )
                    except TypeError:
                        screen_state = str(vision_frame.screen_state)

                if vision_frame.ui_tree:
                    raw_ui = vision_frame.ui_tree.elements[:30]

                    ui_elements = [
                        {
                            "text": element.text,
                            "type": element.element_type,
                        }
                        for element in raw_ui
                        if element.text
                    ]

            raw_patterns = (context.get("known_patterns") or [])[-3:]

            for pattern in raw_patterns:

                compressed_pattern = [
                    {
                        "text": e.get("text"),
                        "type": e.get("type"),
                    }
                    for e in pattern
                    if e.get("text")
                ]

                known_patterns.append(compressed_pattern)

        prompt = f"""
                You are the planning brain of an AI desktop assistant called Omnix.

                Convert the user command into a sequence of executable actions.

                System context:
                {system_context}

                Vision Summary:
                {vision_context}

                Screen State:
                {screen_state}

                Runtime context:
                {json.dumps(runtime_context, indent=2)}

                Visible UI elements:
                {json.dumps(ui_elements)}

                Known UI patterns:
                {json.dumps(known_patterns)}

                Available skills loaded from the skills system:
                {self._available_skills_text()}

                Legacy skill reminders:

                open_app(app) → opens any installed desktop application
                close_app(app) → closes a running application
                type_text(text) → types text into the active input field
                press_key(key) → presses a keyboard key
                click_ui(text) → clicks a UI element containing specific text
                click_mouse(x, y) → clicks at screen coordinates
                double_click(x, y) → double clicks at coordinates
                right_click(x, y) → right clicks at coordinates
                drag_mouse(x1, y1, x2, y2) → drags mouse between coordinates
                hotkey(keys) → presses a keyboard shortcut (example: ctrl+c)
                scroll_page(direction) → scrolls up or down

                IMPORTANT:
                Use the existing skills loaded from the skills system.
                Return multiple steps for multi-part commands.
                Prefer ui_control or click_ui with visible text over mouse coordinates.
                Do not guess coordinates unless necessary.
                For browser search, prefer browser_action with action="search" and query.
                For browser navigation, use browser_action instead of raw typing when possible.
                For app-level closing, use close_app. For closing the active window or tab, use window_control or browser_action.
                For app UI workflows, open the app, wait_for_ui when useful, then use ui_control/click_ui/type_text/press_key.
                For play, pause, volume, mute, next, or previous media commands, use media_control.  
                If the user wants to close a website (e.g., "youtube"), use browser_action with action="close_tab", do NOT use close_app.
                For browser search, ALWAYS use browser_action with action="search" and the query parameter. Do NOT use hotkeys (Ctrl+L) for searching.
                For browser navigation, use browser_action instead of raw typing when possible.
                Use the existing skills loaded from the skills system.
                Prefer ui_control or click_ui with visible text over mouse coordinates. Do not guess coordinates.
                Use the Runtime Context before creating a plan.

                If current_app already matches the requested application,
                DO NOT generate another open_app step.

                If current_browser already exists,
                reuse it.

                If the last search was performed in the browser,
                continue using that browser unless the user explicitly asks otherwise.

                Avoid reopening applications that are already active.

                Only generate actions that are actually necessary.

                Rules:
                Return ONLY JSON list.
                Do not explain anything.
                Always include required parameters for each skill.

                Example:
                [
                {{"skill":"open_app","parameters":{{"app":"{ExecutionContext.DEFAULT_BROWSER}"}}}}
                ]

                User command:
                {command}
                """

        try:
            response = self.brain.ask(prompt)
            logger.debug(f"[Planner] AI response: {response}")

            if not response:
                logger.warning("[Planner] AI returned empty response")
                return self._create_rule_plan(command) or []

            response = response.strip()

            # remove markdown formatting
            response = response.replace("```json", "").replace("```", "")

            start = response.find("[")
            end = response.rfind("]")

            if start == -1 or end == -1:
                logger.warning(f"[Planner] Returned invalid JSON: {response}")
                return self._create_rule_plan(command) or []

            json_text = response[start : end + 1]
            plan = json.loads(json_text)

            if not isinstance(plan, list):
                return self._create_rule_plan(command) or []

            normalized_plan = self._normalize_plan(plan)

            normalized_plan = [self._ensure_expected(step) for step in normalized_plan]

            return normalized_plan or self._create_rule_plan(command) or []

        except Exception as e:
            logger.error(f"[Planner] Task planning failed: {e}")
            return self._create_rule_plan(command) or []

    def _create_workflow_plan(
        self,
        command,
    ):
        """
        Workflow planning is now handled directly
        by the Planner (LLM or future workflow engine).
        """

        return []

    # ------------------------------------------------
    # Next action for agent loop
    # ------------------------------------------------

    def next_action(self, goal, context):

        system_context = context.get("system")

        vision_frame = context.get("vision")

        vision_summary = ""
        screen_state = ""

        ui_elements = []

        if vision_frame:

            vision_summary = vision_frame.summary or ""

            if vision_frame.screen_state:
                try:
                    screen_state = json.dumps(
                        asdict(vision_frame.screen_state),
                        indent=2,
                    )
                except TypeError:
                    screen_state = str(vision_frame.screen_state)

            if vision_frame.ui_tree:
                ui_elements = [
                    {
                        "text": element.text,
                        "type": element.element_type,
                    }
                    for element in vision_frame.ui_tree.elements[:30]
                    if element.text
                ]

        known_patterns = context.get("known_patterns", [])

        execution_context = getattr(self, "execution_context", None)

        runtime_context = execution_context.to_dict() if execution_context else {}

        prompt = f"""
You are Omnix, a goal-driven desktop AI agent.

Goal:
{goal}

System state:
{system_context}

Vision Summary:
{vision_summary}

Screen State:
{screen_state}

Runtime context:
{json.dumps(runtime_context, indent=2)}

Visible UI elements:
{json.dumps(ui_elements)}

Known UI patterns:
{json.dumps(known_patterns)}
Available skills:
{self._available_skills_text()}

Rules:
Use only available skills.
Prefer ui_control/click_ui by target text over click_mouse coordinates.
Use browser_action for browser search/navigation.
Use window_control for active or named window operations.
Return one next action. Return null or no action only when the goal is complete.

Previous action:
{context.get("last_action")}

Previous result:
{context.get("last_result")}

Return ONLY JSON:

{{"skill":"skill_name","parameters":{{}}}}
"""

        try:

            response = self.brain.ask(prompt)

            if not response:
                return None

            response = response.strip()

            start = response.find("{")
            end = response.rfind("}")

            if start == -1 or end == -1:
                return None

            action = json.loads(response[start : end + 1])

            return self._normalize_action(action)

        except Exception as e:

            logger.error(f"[Planner] Next action planning failed: {e}")
            return None
