import unittest
from unittest.mock import patch

from core.execution_context import ExecutionContext
from core.goal_executor import GoalExecutor
from skills.built_in.browser_skill import BrowserSkill


class FakeSkillManager:
    def __init__(self, result):
        self.result = result
        self.executed_steps = []

    def normalize_step(self, step):
        return step

    def execute_skill(self, step):
        self.executed_steps.append(step)
        return self.result


class RuntimeArchitectureTests(unittest.TestCase):
    @patch("skills.built_in.browser_skill.KeyboardMouseController.press_key")
    @patch("skills.built_in.browser_skill.KeyboardMouseController.type_text")
    @patch("skills.built_in.browser_skill.KeyboardMouseController.hotkey")
    @patch("skills.built_in.browser_skill.AppController.open_app", return_value="success")
    def test_browser_skill_does_not_mutate_execution_context(
        self,
        _open_app,
        _hotkey,
        _type_text,
        _press_key,
    ):
        context = ExecutionContext()
        skill = BrowserSkill(execution_context=context)

        result = skill.run(
            {
                "action": "open_url",
                "browser": "chrome",
                "url": "example.com",
            }
        )

        self.assertEqual("success", result)
        self.assertIsNone(context.current_browser)
        self.assertIsNone(context.current_url)
        self.assertIsNone(context.current_website)

    def test_goal_executor_updates_browser_context_after_success(self):
        context = ExecutionContext()
        executor = GoalExecutor(
            skill_manager=FakeSkillManager("success"),
            execution_context=context,
        )

        result = executor.execute_step(
            {
                "skill": "browser_action",
                "parameters": {
                    "action": "open_url",
                    "browser": "edge",
                    "url": "example.com",
                },
            }
        )

        self.assertEqual("success", result)
        self.assertEqual("edge", context.current_browser)
        self.assertEqual("https://example.com", context.current_url)
        self.assertEqual("example.com", context.current_website)

    def test_goal_executor_does_not_update_context_after_error(self):
        context = ExecutionContext()
        executor = GoalExecutor(
            skill_manager=FakeSkillManager("error"),
            execution_context=context,
        )

        result = executor.execute_step(
            {
                "skill": "browser_action",
                "parameters": {
                    "action": "open_url",
                    "browser": "chrome",
                    "url": "example.com",
                },
            }
        )

        self.assertEqual("error", result)
        self.assertIsNone(context.current_browser)
        self.assertIsNone(context.current_url)


if __name__ == "__main__":
    unittest.main()
