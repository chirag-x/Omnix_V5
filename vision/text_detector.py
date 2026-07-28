import easyocr
import torch
from loguru import logger


class TextDetector:

    def __init__(self):
        # Yeh check karega ki RTX 5060 available hai ya nahi
        gpu_available = torch.cuda.is_available()

        logger.info(f"OCR GPU available: {gpu_available}")
        logger.info("Initializing OCR Text Detector")

        # FIX: gpu=False ko hata kar gpu=gpu_available kar dein
        self.reader = easyocr.Reader(['en'], gpu=gpu_available)

    def detect_text(self, frame):
        if frame is None:
            return []

        results = self.reader.readtext(frame)
        elements = []

        for (bbox, text, confidence) in results:
            width = abs(bbox[2][0] - bbox[0][0])
            height = abs(bbox[2][1] - bbox[0][1])

            x = int((bbox[0][0] + bbox[2][0]) / 2)
            y = int((bbox[0][1] + bbox[2][1]) / 2)

            elements.append({
                "text": text,
                "confidence": confidence,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "box": bbox
            })

        return elements
