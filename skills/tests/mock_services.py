"""
Omnix V5 Skill Test Mock Services

Provides fake services for testing skills
without controlling the real computer.
"""


class MockLogger:

    def info(self, message):
        print("[INFO]", message)

    def error(self, message):
        print("[ERROR]", message)

    def warning(self, message):
        print("[WARNING]", message)

    def debug(self, message):
        print("[DEBUG]", message)


class MockSystem:

    async def get_information(self):

        return {
            "os": "Windows",
            "cpu": "Mock CPU",
            "memory": "Mock Memory",
            "status": "online",
        }

    async def lock(self):

        return True

    async def sleep(self):

        return True

    async def restart(self):

        return True

    async def shutdown(self):

        return True


class MockInput:

    async def move_mouse(
        self,
        x,
        y,
    ):

        return True

    async def click(
        self,
        x=None,
        y=None,
        button="left",
        clicks=1,
        interval=0.1,
    ):

        return True

    async def double_click(
        self,
        x,
        y,
    ):

        return True

    async def drag(
        self,
        start_x,
        start_y,
        end_x,
        end_y,
    ):

        return True

    async def type_text(
        self,
        text,
    ):

        return True

    async def press_key(
        self,
        key,
    ):

        return True

    async def hotkey(
        self,
        *keys,
    ):

        return True

    async def scroll(
        self,
        amount,
    ):

        return True


class MockFiles:

    async def create_file(
        self,
        path,
        content="",
    ):

        return {
            "path": path,
            "created": True,
        }

    async def open_file(
        self,
        path,
    ):

        return True

    async def search(
        self,
        query,
        path=None,
    ):

        return [
            {
                "name": "test.txt",
                "path": path or "mock/test.txt",
            }
        ]


class MockApplications:

    async def open(self, application):

        return {
            "application": application,
            "opened": True,
        }

    async def close(self, application):

        return {
            "application": application,
            "closed": True,
        }


class MockBrowser:

    async def is_running(
        self,
        browser="chrome",
    ):

        return True

    async def launch(
        self,
        browser="chrome",
    ):

        return True

    async def focus(
        self,
        browser="chrome",
    ):

        return True

    async def open_url(
        self,
        url,
    ):

        return True

    async def search(
        self,
        query,
        browser="chrome",
    ):

        return True

    async def current_url(self):

        return "https://example.com"

    async def refresh(self):

        return True

    async def back(self):

        return True

    async def forward(self):

        return True

    async def new_tab(self):

        return True

    async def close_tab(self):

        return True

    async def scroll(
        self,
        direction="down",
    ):

        return True


class MockVision:

    async def find_element(
        self,
        name,
    ):

        return {
            "element": name,
            "found": True,
        }

    async def click_element(
        self,
        name,
    ):

        return {
            "element": name,
            "clicked": True,
        }


class MockAutomation:

    async def open_application(
        self,
        application,
    ):

        return True

    async def close_application(
        self,
        application,
    ):

        return True

    async def focus_application(
        self,
        application,
    ):

        return True

    async def is_running(
        self,
        application,
    ):

        return True


def create_mock_context():

    from skills.core.skill_context import SkillContext

    return SkillContext(
        command="test command",
        intent="test",
        logger=MockLogger(),
        system=MockSystem(),
        input=MockInput(),
        files=MockFiles(),
        browser=MockBrowser(),
        vision=MockVision(),
        automation=MockAutomation(),
    )
