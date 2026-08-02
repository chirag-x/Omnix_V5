"""
Omnix V5 - OCR Text Detector

Uses EasyOCR and converts every OCR result into a VisionObject.

Responsibilities
----------------
- Run OCR
- Convert OCR → VisionObject
- Normalize Bounding Boxes
- Return typed objects
"""

from __future__ import annotations

import time

import easyocr
import torch
from loguru import logger

from vision.detection.bbox_normalizer import BoundingBoxNormalizer
from vision.models.vision_object import VisionObject


class TextDetector:

    def __init__(self):

        gpu = torch.cuda.is_available()

        logger.info(f"OCR GPU: {gpu}")

        self.reader = easyocr.Reader(
            ["en"],
            gpu=gpu,
        )

        self.normalizer = BoundingBoxNormalizer()

    # ---------------------------------------------------------

    def detect(
        self,
        frame,
        *,
        frame_id: int = 0,
        timestamp: float | None = None,
    ) -> tuple[list[VisionObject], float]:

        if frame is None:
            return [], 0.0

        if timestamp is None:
            timestamp = time.time()

        start = time.perf_counter()

        height, width = frame.shape[:2]

        results = self.reader.readtext(frame)

        texts: list[VisionObject] = []

        for bbox, text, confidence in results:

            xs = [p[0] for p in bbox]
            ys = [p[1] for p in bbox]

            x1 = min(xs)
            y1 = min(ys)
            x2 = max(xs)
            y2 = max(ys)

            obj = self.normalizer.normalize(
                label=text,
                confidence=float(confidence),
                bbox=[x1, y1, x2, y2],
                frame_width=width,
                frame_height=height,
                source="ocr",
                model="easyocr",
                frame_id=frame_id,
                timestamp=timestamp,
            )

            obj.category = "text"

            obj.add_tag("ocr")

            obj.add_tag("text")

            obj.set_attribute(
                "ocr_confidence",
                confidence,
            )

            obj.set_attribute(
                "raw_text",
                text,
            )

            texts.append(obj)

        elapsed = (time.perf_counter() - start) * 1000

        logger.debug(f"[OCR] {len(texts)} text regions " f"in {elapsed:.1f} ms")

        return texts, elapsed
