import numpy as np
import pygetwindow as gw
from system.services.keyboard_controller import KeyboardController
from system.services.mouse_controller import MouseController
from loguru import logger


class VisionController:

    def __init__(self, screen_observer):

        logger.info("Initializing Vision Controller")

        self.observer = screen_observer

        self.keyboard = KeyboardController()
        self.mouse = MouseController()

    def click(self, x, y):

        logger.info(f"Clicking at {x}, {y}")

        self.mouse.click(x, y)

    def click_ui_element(self, element):

        x = element["x"]
        y = element["y"]

        self.click(x, y)

    def type_text(self, text):

        logger.info(f"Typing text via vision system: {text}")

        self.keyboard.write(text)

    def press_key(self, key):

        logger.info(f"Pressing key: {key}")

        self.keyboard.press(key)

    def ensure_window_focus(self, window_title):

        windows = gw.getWindowsWithTitle(window_title)

        if windows:

            window = windows[0]

            if not window.isActive:
                logger.info(f"Focusing window: {window_title}")
                window.activate()
