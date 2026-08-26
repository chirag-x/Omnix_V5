import threading
import time
import asyncio
import pyautogui

from loguru import logger

from core.planning.execution_context import ExecutionContext
from memory.ui_pattern_memory import UIPatternMemory
from vision.vision_pipeline import VisionPipeline


class VisionManager:

    def __init__(
        self,
        observer,
        execution_context: ExecutionContext | None = None,
        window_manager=None,
    ):
        logger.info("[Vision] Initializing Vision Manager")

        self.observer = observer
        self.execution_context = execution_context

        # Core pipeline
        self.pipeline = VisionPipeline()

        # Memory
        self.ui_memory = UIPatternMemory()

        # Latest processed frame
        self.latest_frame = None

        # Window Manager
        self.window_manager = window_manager

        # Cache
        self.last_ui_snapshot = None
        self.last_system_snapshot = None

        # Thread
        self.running = False
        self.thread = None

    def start(self):
        logger.info("[Vision] Starting manager")

        if self.running:
            return

        self.observer.start()
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        logger.info("[Vision] Stopping manager")

        self.running = False

        if self.thread:
            self.thread.join(timeout=2)

        self.observer.stop()

    def _loop(self):
        logger.info("[Vision] Manager loop started")

        while self.running:
            try:
                frame = self.observer.get_latest_frame()

                if frame is None:
                    time.sleep(0.1)
                    continue

                active_info = self._sync_execution_context()

                vision_frame = self.pipeline.analyze_frame(
                    frame,
                    active_app=active_info["app"],
                    active_window=active_info["window"],
                )

                if vision_frame is not None:
                    self.latest_frame = vision_frame
                    self.latest_summary = vision_frame.summary

                ui_elements = (
                    vision_frame.ui_tree.elements if vision_frame.ui_tree else []
                )

                if ui_elements != self.last_ui_snapshot:

                    self._store_ui_pattern(
                        active_info,
                        ui_elements,
                    )

                    self.last_ui_snapshot = ui_elements

                    logger.debug("[Vision] UI change detected")

                self.latest_summary = vision_frame.summary

            except Exception:
                logger.exception("[Vision] Loop error")

            time.sleep(0.25)

    def _sync_execution_context(self):

        if self.window_manager is None:
            return {
                "window": "unknown",
                "app": "unknown",
            }

        active = self.window_manager.foreground

        if active is None:
            return {
                "window": "unknown",
                "app": "unknown",
            }

        info = {
            "window": active.title,
            "app": active.application or active.title,
        }

        snapshot = (
            info["window"],
            info["app"],
        )

        if self.execution_context and snapshot != self.last_system_snapshot:

            self.execution_context.sync_from_system(
                active_window=info["window"],
                active_app=info["app"],
            )

            self.last_system_snapshot = snapshot

        return info

    def _store_ui_pattern(self, active_info, ui_elements):
        if active_info["window"] == "unknown":
            return

        self.ui_memory.store_pattern(active_info["window"], ui_elements)

    def get_latest_frame(self):
        """
        Returns the newest VisionFrame.
        """
        return self.latest_frame

    def get_latest_analysis(self):
        """
        Backward compatibility.
        """
        return self.latest_frame

    async def find_element(self, target: str):

        # Force a fresh screenshot
        frame = self.observer.get_latest_frame()

        if frame is not None:

            active = self._sync_execution_context()

            vision_frame = self.pipeline.analyze_frame(
                frame,
                active_app=active["app"],
                active_window=active["window"],
            )

            if vision_frame:
                self.latest_frame = vision_frame

        frame = self.latest_frame

        if frame is None:
            return None

        tree = frame.ui_tree

        if tree is None:
            return None

        element = tree.find(target)

        if element:
            return element

        target = target.lower()

        for element in tree.elements:

            if target in (element.name or "").lower():
                return element

            if target in (element.text or "").lower():
                return element

            if target in (element.role or "").lower():
                return element

            if target in (element.element_type or "").lower():
                return element

        return None

    async def wait_for_element(self, target: str, timeout: float = 10):
        start = time.time()

        while time.time() - start < timeout:
            element = await self.find_element(target)

            if element:
                return element

            await asyncio.sleep(0.25)

        return None

    async def click_element(self, target: str):
        element = await self.find_element(target)

        if not element:
            return False

        if element.bbox is None:
            return False

        x = element.bbox.center_x
        y = element.bbox.center_y

        pyautogui.moveTo(x, y, duration=0.15)
        await asyncio.sleep(0.1)
        pyautogui.click()

        return True
