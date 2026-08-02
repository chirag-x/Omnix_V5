"""
Omnix V5 - Vision Pipeline

Main orchestration pipeline for the Vision Engine.

Pipeline:

Frame
    ↓
YOLO Detector
    ↓
OCR Detector
    ↓
Duplicate Filter
    ↓
Metadata Builder
    ↓
Detection Fusion
    ↓
Screen Region Analyzer
    ↓
UI Hierarchy Builder
    ↓
Screen State Builder
    ↓
Semantic Summary Builder
    ↓
VisionFrame
"""

from __future__ import annotations

import time

from loguru import logger

from vision.detection.yolo_detector import YOLODetector
from vision.text_detector import TextDetector

from vision.detection.duplicate_filter import DuplicateFilter
from vision.detection.metadata_builder import MetadataBuilder
from vision.detection.detection_fuser import DetectionFuser

from vision.hierarchy.screen_regions import ScreenRegionAnalyzer
from vision.hierarchy.ui_hierarchy import UIHierarchyBuilder

from vision.summary.screen_state import ScreenStateBuilder
from vision.summary.semantic_summary import SemanticSummaryBuilder

from vision.models.vision_frame import VisionFrame


class VisionPipeline:
    """
    Central vision orchestration pipeline.

    Every frame passes through every stage in order and
    produces one VisionFrame.
    """

    def __init__(self):

        logger.info("Initializing Omnix V5 Vision Pipeline")

        # --------------------------------------------------
        # Detection
        # --------------------------------------------------

        self.detector = YOLODetector()
        self.text_detector = TextDetector()

        # --------------------------------------------------
        # Detection Processing
        # --------------------------------------------------

        self.duplicate_filter = DuplicateFilter()
        self.metadata_builder = MetadataBuilder()
        self.fuser = DetectionFuser()

        # --------------------------------------------------
        # Hierarchy
        # --------------------------------------------------

        self.region_builder = ScreenRegionAnalyzer()
        self.ui_builder = UIHierarchyBuilder()

        # --------------------------------------------------
        # Summary
        # --------------------------------------------------

        self.state_builder = ScreenStateBuilder()
        self.summary_builder = SemanticSummaryBuilder()

        logger.success("Vision Pipeline Ready")

    def analyze_frame(
        self,
        frame,
        active_app: str = "",
        active_window: str = "",
    ) -> VisionFrame:
        """
        Analyze one screen frame and return a structured VisionFrame.
        """

        start_time = time.perf_counter()
        # --------------------------------------------------
        # Metadata Enrichment
        # --------------------------------------------------

        timestamp = time.time()

        objects, detector_time = self.detector.detect(
            frame,
            timestamp=timestamp,
        )

        texts, ocr_time = self.text_detector.detect(
            frame,
            timestamp=timestamp,
        )

        # --------------------------------------------------
        # Remove duplicate detections
        # --------------------------------------------------

        objects = self.duplicate_filter.filter(objects)

        texts = self.duplicate_filter.filter(texts)

        # --------------------------------------------------
        # Fuse OCR + Object detections
        # --------------------------------------------------

        objects, remaining_text = self.fuser.fuse(
            objects,
            texts,
        )

        logger.debug(
            f"Fusion complete: "
            f"{len(objects)} objects, "
            f"{len(remaining_text)} standalone text regions."
        )

        # --------------------------------------------------
        # Build VisionFrame
        # --------------------------------------------------

        height, width = frame.shape[:2]

        vision_frame = VisionFrame(
            timestamp=timestamp,
            frame_width=width,
            frame_height=height,
            active_app=active_app,
            active_window=active_window,
            objects=objects,
            texts=remaining_text,
        )

        vision_frame.metadata["detector_time_ms"] = detector_time
        vision_frame.metadata["ocr_time_ms"] = ocr_time
        vision_frame.metadata["pipeline_start"] = start_time

        return self._build_hierarchy(vision_frame)

    def _build_hierarchy(
        self,
        frame: VisionFrame,
    ) -> VisionFrame:
        """
        Build the high-level understanding of the screen.
        """

        # --------------------------------------------------
        # Assign Screen Regions
        # --------------------------------------------------

        self.region_builder.assign_regions(
            frame.objects,
            frame.frame_width,
            frame.frame_height,
        )

        self.region_builder.assign_regions(
            frame.texts,
            frame.frame_width,
            frame.frame_height,
        )
        # --------------------------------------------------
        # Build UI Tree
        # --------------------------------------------------

        ui_objects = frame.objects + frame.texts

        ui_tree = self.ui_builder.build(
            ui_objects,
        )

        frame.ui_tree = ui_tree

        # --------------------------------------------------
        # Screen State
        # --------------------------------------------------

        screen_state = self.state_builder.build(
            frame,
            ui_tree,
        )

        frame.screen_state = screen_state

        # --------------------------------------------------
        # Semantic Summary
        # --------------------------------------------------

        frame.summary = self.summary_builder.build(
            screen_state,
            ui_tree,
        )

        # --------------------------------------------------
        # Statistics
        # --------------------------------------------------

        frame.metadata["object_count"] = len(frame.objects)

        frame.metadata["text_count"] = len(frame.texts)

        frame.metadata["ui_element_count"] = len(ui_tree.elements)

        frame.metadata["clickable_count"] = screen_state.clickable_elements

        frame.metadata["editable_count"] = screen_state.editable_elements

        frame.metadata["visible_count"] = screen_state.visible_elements

        frame.metadata["has_dialog"] = screen_state.has_dialog

        frame.metadata["has_popup"] = screen_state.has_popup

        frame.metadata["loading"] = screen_state.loading

        frame.metadata["error"] = screen_state.error

        logger.debug(
            f"Vision complete: "
            f"{len(frame.objects)} objects | "
            f"{len(ui_tree.elements)} UI elements"
        )

        return frame
