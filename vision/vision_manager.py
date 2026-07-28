import threading
import time

from loguru import logger

from core.execution_context import ExecutionContext
from memory.ui_pattern_memory import UIPatternMemory
from system.window_controller import WindowController
from vision.vision_pipeline import VisionPipeline


class VisionManager:
    def __init__(
        self,
        observer,
        execution_context: ExecutionContext | None = None,
    ):
        logger.info("[Vision] Initializing manager")

        self.observer = observer
        self.execution_context = execution_context
        self.pipeline = VisionPipeline(self.observer)
        self.ui_memory = UIPatternMemory()

        self.latest_analysis = None
        self.last_ui_snapshot = None
        self.last_system_snapshot = None

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
            self.thread.join()

        self.observer.stop()

    def _loop(self):
        logger.info("[Vision] Manager loop started")

        while self.running:
            try:
                frame = self.observer.get_latest_frame()

                if frame is None:
                    time.sleep(0.1)
                    continue

                analysis = self.pipeline.analyze_frame(frame)

                if not analysis:
                    continue

                active_info = self._sync_execution_context()
                ui_elements = analysis.get("ui_elements", [])

                if ui_elements != self.last_ui_snapshot:
                    self._store_ui_pattern(active_info, ui_elements)
                    self.last_ui_snapshot = ui_elements
                    logger.debug("[Vision] UI change detected; pattern stored")

                self.latest_analysis = dict(analysis)

            except Exception as e:
                logger.error(f"[Vision] Loop error: {e}")

            time.sleep(0.25)

    def _sync_execution_context(self):
        info = WindowController.get_active_window_info()
        snapshot = (info["window"], info["app"])

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

    def get_latest_analysis(self):
        return self.latest_analysis
