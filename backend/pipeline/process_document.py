"""
High-level orchestration for PDF/image ingestion -> HWP automation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Sequence, Tuple

from backend.equations.latex_to_hwpeqn import latex_to_hwpeqn
from backend.hwp.hwp_controller import HwpController
from backend.ocr import Block, BlockType
from backend.ocr.pdf_to_images import pdf_to_images
from backend.ocr.pix2text_client import Pix2TextClient, Pix2TextOptions

logger = logging.getLogger(__name__)

LogFn = Callable[[str], None]
ProgressFn = Callable[[int, int, str], None]


@dataclass(slots=True)
class ProcessOptions:
    include_text: bool = True
    include_equations: bool = True
    include_images: bool = True
    ocr_mode: str = "Pix2Text (기본)"


def process_inputs(
    paths: Sequence[str],
    options: ProcessOptions,
    hwp: HwpController,
    log: LogFn | None = None,
    progress: ProgressFn | None = None,
) -> None:
    log_fn = log or (lambda *_: None)
    pix_options = Pix2TextOptions(
        use_pix2tex_for_equations="pix2tex" in options.ocr_mode.lower()
    )
    client = Pix2TextClient(pix_options)

    docs: List[Tuple[str, List[Path]]] = []
    total_pages = 0
    for path in paths:
        images = _materialize_images(Path(path), log_fn)
        docs.append((path, images))
        total_pages += len(images)
    processed_pages = 0

    for path, images in docs:
        log_fn(f"파일 처리 시작: {path}")
        for page_index, image_path in enumerate(images):
            processed_pages += 1
            if progress:
                progress(
                    processed_pages,
                    max(total_pages, 1),
                    f"{Path(path).name} {page_index + 1}/{len(images)}",
                )
            log_fn(f"  · 페이지 {page_index + 1} OCR 중...")
            page_blocks = client.extract_blocks(str(image_path), page_index)
            _send_blocks_to_hwp(page_blocks.blocks, options, hwp, log_fn)


def _materialize_images(path: Path, log: LogFn) -> List[Path]:
    if path.suffix.lower() == ".pdf":
        log(f"PDF → 이미지 변환 중: {path}")
        return pdf_to_images(str(path))
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp"}:
        return [path]
    log(f"지원되지 않는 파일 형식: {path.suffix}. 그대로 시도합니다.")
    return [path]


def _send_blocks_to_hwp(
    blocks: Iterable[Block],
    options: ProcessOptions,
    hwp: HwpController,
    log: LogFn,
) -> None:
    for block in blocks:
        if block.block_type == BlockType.TEXT:
            if not options.include_text:
                continue
            text = (block.content or "").strip()
            if not text:
                continue
            hwp.insert_text(text)
            hwp.insert_paragraph_break()
            log(f"    · 텍스트 문단 삽입 ({len(text)}자)")
        elif block.block_type in (
            BlockType.INLINE_EQUATION,
            BlockType.DISPLAY_EQUATION,
        ):
            if not options.include_equations:
                continue
            _handle_equation_block(block, hwp, log)
        elif block.block_type == BlockType.IMAGE:
            if not options.include_images or not block.image_path:
                continue
            _handle_image_block(block, hwp, log)
        else:
            log(f"    · 알 수 없는 블록 타입: {block.block_type}")


def _handle_equation_block(block: Block, hwp: HwpController, log: LogFn) -> None:
    latex = (block.latex or "").strip()
    if not latex:
        return

    hwpeqn = latex_to_hwpeqn(latex)
    try:
        hwp.insert_equation(hwpeqn)
        log("    · 수식 삽입 완료")
    except NotImplementedError:
        # TODO: replace fallback once HwpController.insert_equation is implemented.
        hwp.insert_text(f"[수식: {latex}]")
        log("    · (TODO) 수식 텍스트로 대체")
    finally:
        if block.block_type == BlockType.DISPLAY_EQUATION:
            hwp.insert_paragraph_break()


def _handle_image_block(block: Block, hwp: HwpController, log: LogFn) -> None:
    assert block.image_path
    try:
        hwp.insert_image(block.image_path)
        log("    · 이미지 삽입 완료")
    except NotImplementedError:
        placeholder = Path(block.image_path).name
        hwp.insert_text(f"[이미지: {placeholder}]")
        hwp.insert_paragraph_break()
        log("    · (TODO) 이미지를 경로 텍스트로 대체")

