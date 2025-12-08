"""Basic OCR block dataclasses and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class BlockType(str, Enum):
    TEXT = "text"
    INLINE_EQUATION = "inline_equation"
    DISPLAY_EQUATION = "display_equation"
    IMAGE = "image"


@dataclass(slots=True)
class Block:
    block_type: BlockType
    content: Optional[str] = None
    latex: Optional[str] = None
    image_path: Optional[str] = None


@dataclass(slots=True)
class PageBlocks:
    page_index: int
    blocks: List[Block]

