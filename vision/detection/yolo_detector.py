"""
Omnix V5 - YOLO Detector

Runs YOLO11 inference and converts detections into VisionObjects.

Responsibilities
----------------
- Load YOLO model
- Run inference
- Convert results to VisionObjects
- Measure inference time

Does NOT:
- Remove duplicates
- Build UI hierarchy
- Merge OCR
- Generate summaries
"""

from __future__ import annotations

import time
from pathlib import Path

import torch
from loguru import logger
from ultralytics import YOLO

from vision.detection.bbox_normalizer import BoundingBoxNormalizer
from vision.models.vision_object import VisionObject


class YOLODetector:

    def __init__(
        self,
        model_path: str | Path = "vision/models/yolo11n.pt",
        confidence: float = 0.40,
        iou: float = 0.45,
        max_detections: int = 300,
    ):

        self.model_path = Path(model_path)
        self.confidence = confidence
        self.iou = iou
        self.max_detections = max_detections

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(f"[YOLO] Loading model: {self.model_path}")
        logger.info(f"[YOLO] Device: {self.device}")

        self.model = YOLO(self.model_path)

        self.normalizer = BoundingBoxNormalizer()

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def detect(
        self,
        frame,
        *,
        frame_id: int = 0,
        timestamp: float | None = None,
    ) -> tuple[list[VisionObject], float]:

        if timestamp is None:
            timestamp = time.time()

        start = time.perf_counter()

        height, width = frame.shape[:2]

        results = self.model.predict(
            source=frame,
            conf=self.confidence,
            iou=self.iou,
            max_det=self.max_detections,
            verbose=False,
            device=self.device,
        )

        detections: list[VisionObject] = []

        for result in results:

            if result.boxes is None:
                continue

            for box in result.boxes:

                class_id = int(box.cls.item())

                confidence = float(box.conf.item())

                label = self.model.names[class_id]

                bbox = box.xyxy[0].tolist()

                obj = self.normalizer.normalize(
                    label=label,
                    confidence=confidence,
                    bbox=bbox,
                    frame_width=width,
                    frame_height=height,
                    source="yolo",
                    model=self.model_path.name,
                    frame_id=frame_id,
                    timestamp=timestamp,
                )

                # Optional debug information
                obj.set_attribute(
                    "class_id",
                    class_id,
                )

                obj.set_attribute(
                    "raw_data",
                    {
                        "bbox": bbox,
                        "confidence": confidence,
                    },
                )

                detections.append(obj)

        elapsed_ms = (time.perf_counter() - start) * 1000

        logger.debug(f"[YOLO] {len(detections)} detections " f"in {elapsed_ms:.1f} ms")

        return detections, elapsed_ms
