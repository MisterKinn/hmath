"""
Global configuration helpers for Inline HWP AI.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _env_path(name: str) -> Optional[Path]:
    value = os.getenv(name)
    if value:
        return Path(value).expanduser()
    return None


@dataclass(frozen=True)
class PdfConfig:
    dpi: int = int(os.getenv("INLINE_HWP_PDF_DPI", "300"))
    poppler_path: Optional[Path] = _env_path("POPPLER_PATH")


@dataclass(frozen=True)
class OcrConfig:
    lang: str = os.getenv("INLINE_HWP_OCR_LANG", "kor+eng")
    tesseract_cmd: Optional[Path] = _env_path("TESSERACT_CMD")
    min_text_confidence: int = int(os.getenv("INLINE_HWP_MIN_TEXT_CONF", "60"))
    min_image_area_ratio: float = float(os.getenv("INLINE_HWP_MIN_IMG_RATIO", "0.03"))
    use_pix2tex: bool = os.getenv("INLINE_HWP_USE_PIX2TEX", "0") == "1"


@dataclass(frozen=True)
class PathsConfig:
    output_root: Path = Path(
        os.getenv("INLINE_HWP_WORKDIR", tempfile.gettempdir())
    ) / "inline_hwp_ai"


@dataclass(frozen=True)
class AIConfig:
    """AI model configuration."""
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")
    xai_api_key: Optional[str] = os.getenv("XAI_API_KEY")


PDF = PdfConfig()
OCR = OcrConfig()
PATHS = PathsConfig()
AI = AIConfig()
PATHS.output_root.mkdir(parents=True, exist_ok=True)


def build_temp_dir(prefix: str) -> Path:
    """Create (if needed) and return a temp directory for intermediate files."""
    directory = PATHS.output_root / prefix
    directory.mkdir(parents=True, exist_ok=True)
    return directory
