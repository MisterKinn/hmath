"""
Stub PDF -> image conversion utilities.

TODO: replace with real conversion using pdf2image/poppler.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageDraw

from backend.config import PDF, build_temp_dir

logger = logging.getLogger(__name__)

try:
    from pdf2image import convert_from_path
except ImportError:  # pragma: no cover
    convert_from_path = None


def pdf_to_images(
    pdf_path: str,
    output_dir: Optional[str] = None,
    dpi: Optional[int] = None,
) -> List[Path]:
    """
    Convert a PDF into per-page PNG files using pdf2image if available.

    Falls back to generating a placeholder image when the dependency or Poppler
    binaries are missing. Returns a list of absolute paths.
    """
    target_dir = Path(output_dir) if output_dir else build_temp_dir("pdf_pages")
    target_dir.mkdir(parents=True, exist_ok=True)

    dpi = dpi or PDF.dpi
    pdf_name = Path(pdf_path).stem

    if convert_from_path:
        try:
            paths = convert_from_path(
                pdf_path,
                dpi=dpi,
                fmt="png",
                output_folder=str(target_dir),
                output_file=pdf_name,
                paths_only=True,
                poppler_path=str(PDF.poppler_path) if PDF.poppler_path else None,
            )
            return [Path(p) for p in paths]
        except Exception as exc:  # pragma: no cover
            logger.warning(
                "pdf2image conversion failed (%s). Falling back to placeholder: %s",
                type(exc).__name__,
                exc,
            )

    # Fallback to single placeholder
    image_path = target_dir / f"{pdf_name}_page_001.png"
    if not image_path.exists():
        _create_placeholder_page(image_path, pdf_path)
    return [image_path]


def _create_placeholder_page(path: Path, label: str) -> None:
    img = Image.new("RGB", (1240, 1754), color="white")
    draw = ImageDraw.Draw(img)
    message = f"Placeholder for {Path(label).name}"
    draw.text((50, 50), message, fill="black")
    img.save(path)

