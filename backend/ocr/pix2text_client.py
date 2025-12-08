"""
OCR + layout detection client with a Pix2Text-friendly interface.

Attempts to use pytesseract/OpenCV for text & figure detection while leaving
hooks for heavier Pix2Text/pix2tex integrations.
"""

from __future__ import annotations

import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image

from backend.config import OCR
from backend.ocr import Block, BlockType, PageBlocks

logger = logging.getLogger(__name__)

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

try:
    import pytesseract
    from pytesseract import Output as TesseractOutput
except ImportError:  # pragma: no cover
    pytesseract = None
    TesseractOutput = None


MATH_TOKENS = set("=+-*/×÷∑∫√πθσΔβγλμ_^\\≤≥≈∞≠")


@dataclass(slots=True)
class Pix2TextOptions:
    use_pix2tex_for_equations: bool = OCR.use_pix2tex
    detect_images: bool = True
    lang: str = OCR.lang
    min_confidence: int = OCR.min_text_confidence
    min_image_area_ratio: float = OCR.min_image_area_ratio


class Pix2TextClient:
    def __init__(self, options: Pix2TextOptions | None = None) -> None:
        self._options = options or Pix2TextOptions()
        if OCR.tesseract_cmd and pytesseract:
            pytesseract.pytesseract.tesseract_cmd = str(OCR.tesseract_cmd)

    def extract_blocks(self, image_path: str, page_index: int) -> PageBlocks:
        if pytesseract is None:
            logger.warning("pytesseract not installed; returning stub blocks.")
            return self._stub_blocks(page_index, image_path)

        image = Image.open(image_path).convert("RGB")
        ocr_data = pytesseract.image_to_data(
            image,
            lang=self._options.lang,
            output_type=TesseractOutput.DICT,
        )

        blocks_with_y = self._build_text_blocks(ocr_data)
        if self._options.detect_images and cv2 is not None:
            blocks_with_y.extend(
                self._detect_image_blocks(image, ocr_data, page_index)
            )

        blocks_with_y.sort(key=lambda item: item[0])
        blocks = [block for _, block in blocks_with_y]
        if not blocks:
            blocks = [Block(block_type=BlockType.TEXT, content="[OCR 결과 없음]")]
        return PageBlocks(page_index=page_index, blocks=blocks)

    # ------------------------------------------------------------------ #
    # Text helpers
    # ------------------------------------------------------------------ #
    def _build_text_blocks(self, data: Dict[str, List[str]]) -> List[Tuple[float, Block]]:
        aggregator: Dict[Tuple[int, int, int], Dict[str, List]] = {}
        for idx, text in enumerate(data.get("text", [])):
            text = (text or "").strip()
            if not text:
                continue
            try:
                conf = int(float(data["conf"][idx]))
            except (ValueError, KeyError):
                conf = 0
            if conf < self._options.min_confidence:
                continue
            key = (
                data.get("block_num", [0])[idx],
                data.get("par_num", [0])[idx],
                data.get("line_num", [0])[idx],
            )
            entry = aggregator.setdefault(
                key,
                {"words": [], "tops": [], "heights": [], "lefts": [], "rights": []},
            )
            entry["words"].append(text)
            entry["tops"].append(int(data.get("top", [0])[idx]))
            entry["heights"].append(int(data.get("height", [0])[idx]))
            left = int(data.get("left", [0])[idx])
            width = int(data.get("width", [0])[idx])
            entry["lefts"].append(left)
            entry["rights"].append(left + width)

        output: List[Tuple[float, Block]] = []
        for entry in aggregator.values():
            text_line = " ".join(entry["words"]).strip()
            if not text_line:
                continue
            y_center = np.mean(entry["tops"]) if entry["tops"] else 0
            block_type = self._classify_line(text_line)
            block = Block(
                block_type=block_type,
                content=text_line if block_type == BlockType.TEXT else None,
                latex=text_line if block_type != BlockType.TEXT else None,
            )
            output.append((y_center, block))
        return output

    def _classify_line(self, text: str) -> BlockType:
        score = sum(1 for ch in text if ch in MATH_TOKENS)
        digit_ratio = sum(ch.isdigit() for ch in text) / max(len(text), 1)
        if score >= 2 or digit_ratio > 0.25:
            if len(text) > 20 or "\\" in text:
                return BlockType.DISPLAY_EQUATION
            return BlockType.INLINE_EQUATION
        return BlockType.TEXT

    # ------------------------------------------------------------------ #
    # Image detection
    # ------------------------------------------------------------------ #
    def _detect_image_blocks(
        self,
        image: Image.Image,
        data: Dict[str, List[str]],
        page_index: int,
    ) -> List[Tuple[float, Block]]:
        if cv2 is None:
            return []
        width, height = image.size
        mask = np.zeros((height, width), dtype=np.uint8)
        for idx in range(len(data.get("text", []))):
            try:
                conf = int(float(data["conf"][idx]))
            except (ValueError, KeyError):
                conf = 0
            if conf < self._options.min_confidence:
                continue
            x = int(data.get("left", [0])[idx])
            y = int(data.get("top", [0])[idx])
            w = int(data.get("width", [0])[idx])
            h = int(data.get("height", [0])[idx])
            cv2.rectangle(mask, (x, y), (x + w, y + h), 255, thickness=-1)

        inverted = cv2.bitwise_not(mask)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        dilated = cv2.dilate(inverted, kernel, iterations=2)
        contours, _ = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        blocks: List[Tuple[float, Block]] = []
        for contour in contours or []:
            area = cv2.contourArea(contour)
            if area <= 0:
                continue
            if area / (width * height) < self._options.min_image_area_ratio:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            if w * h == 0:
                continue
            crop = image.crop((x, y, x + w, y + h))
            fd, tmp_path = tempfile.mkstemp(
                suffix=f"_p{page_index}.png", prefix="inline-hwp-fig-"
            )
            os.close(fd)
            crop.save(tmp_path, format="PNG")
            block = Block(block_type=BlockType.IMAGE, image_path=tmp_path)
            blocks.append((y + h / 2.0, block))
        return blocks

    # ------------------------------------------------------------------ #
    # Stub fallback
    # ------------------------------------------------------------------ #
    def _stub_blocks(self, page_index: int, image_path: str) -> PageBlocks:
        blocks: List[Block] = [
            Block(block_type=BlockType.TEXT, content="OCR 엔진이 설치되지 않았습니다."),
            Block(
                block_type=BlockType.TEXT,
                content="pytesseract 설치 후 환경변수 TESSERACT_CMD 를 설정하세요.",
            ),
            Block(block_type=BlockType.IMAGE, image_path=str(image_path)),
        ]
        return PageBlocks(page_index=page_index, blocks=blocks)

