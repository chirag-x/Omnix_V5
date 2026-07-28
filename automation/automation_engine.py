from loguru import logger


class AutomationEngine:
    def __init__(self, executor):
        logger.info("[Automation] Initializing engine")

        self.executor = executor
        self.running = True

    def execute_plan(self, plan):
        logger.info("[Automation] Starting plan")

        for step in plan:
            if not self.running:
                logger.warning("[Automation] Stopped")
                break

            normalized_step = self._normalize_step(step)
            skill_name = normalized_step.get("skill")

            logger.info(f"[Automation] Executing step: {skill_name}")

            result = self._execute_step(normalized_step)

            if result == "error":
                logger.error(f"[Automation] Step failed: {skill_name}")

        logger.info("[Automation] Plan finished")

    def _normalize_step(self, step):
        params = step.get("parameters", step.get("params", {})) if isinstance(step, dict) else {}

        return {
            "skill": step.get("skill") if isinstance(step, dict) else None,
            "parameters": params if isinstance(params, dict) else {},
        }

    def _execute_step(self, step):
        if hasattr(self.executor, "execute_step"):
            return self.executor.execute_step(step)

        if hasattr(self.executor, "execute_skill"):
            return self.executor.execute_skill(step)

        skill = self.executor.get_skill(step.get("skill"))

        if not skill:
            logger.error(f"[Automation] Skill not found: {step.get('skill')}")
            return "error"

        params = step.get("parameters", {})

        if hasattr(skill, "run"):
            return skill.run(params) or "success"

        if hasattr(skill, "execute"):
            return skill.execute(**params) or "success"

        logger.error(f"[Automation] Skill has no executable entry point: {step.get('skill')}")
        return "error"

    def stop(self):
        logger.warning("[Automation] Stopping")
        self.running = False
