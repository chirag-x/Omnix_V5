import asyncio

from skills.manager.skill_manager import SkillManager
from skills.tests.mock_services import create_mock_context


async def main():

    manager = SkillManager()

    await manager.initialize()

    context = create_mock_context()

    tests = [
        ("builtin.system.system_info", {}),
        ("builtin.input.type_text", {"text": "hello omnix"}),
        ("builtin.input.press_key", {"key": "enter"}),
        ("builtin.files.create_file", {"path": "test.txt", "content": "Omnix V5 test"}),
        ("builtin.files.open_file", {"path": "test.txt"}),
        ("builtin.files.search_file", {"query": "test"}),
        ("builtin.vision.find_element", {"element": "chrome"}),
        ("builtin.vision.click_ui", {"element": "chrome"}),
        ("builtin.vision.wait_ui", {"element": "chrome", "timeout": 2}),
        ("builtin.browser.search", {"query": "OpenAI"}),
        ("builtin.browser.open", {"url": "https://example.com"}),
        ("builtin.browser.action", {"action": "back"}),
        ("builtin.applications.open", {"application": "chrome"}),
        ("builtin.applications.close", {"application": "chrome"}),
        ("builtin.applications.switch", {"application": "chrome"}),
        ("builtin.input.click", {"x": 100, "y": 100}),
        ("builtin.input.double_click", {"x": 100, "y": 100}),
        ("builtin.input.right_click", {"x": 100, "y": 100}),
        ("builtin.input.middle_click", {"x": 100, "y": 100}),
        ("builtin.input.move_mouse", {"x": 100, "y": 100}),
        (
            "builtin.input.drag",
            {"start_x": 100, "start_y": 100, "end_x": 200, "end_y": 200},
        ),
        ("builtin.input.hotkey", {"keys": ["ctrl", "c"]}),
        ("builtin.input.copy", {}),
        ("builtin.input.cut", {}),
        ("builtin.input.paste", {}),
        ("builtin.input.undo", {}),
        ("builtin.input.redo", {}),
        ("builtin.input.select_all", {}),
        ("builtin.input.scroll", {"amount": 5}),
        ("builtin.system.lock", {}),
        ("builtin.system.sleep", {}),
        ("builtin.system.restart", {}),
        ("builtin.system.shutdown", {}),
    ]

    print("Total skills:", manager.skill_count())

    for skill_id, params in tests:

        context.parameters = params
        context.entities = params

        print("\nTesting:", skill_id)

        result = await manager.execute(
            skill_id,
            context,
        )

        print("Result:", result)

    await manager.shutdown()


if __name__ == "__main__":

    asyncio.run(main())
