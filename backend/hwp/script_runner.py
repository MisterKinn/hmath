"""
Execute user-defined automation snippets against an active Hancom Hangul session.
"""

from __future__ import annotations

import logging
import textwrap
import traceback
from typing import Callable, Dict

from backend.hwp.hwp_controller import HwpController
from backend.equations.latex_to_hwpeqn import latex_to_hwpeqn

logger = logging.getLogger(__name__)

LogFn = Callable[[str], None]


SAFE_BUILTINS: Dict[str, object] = {
    "range": range,
    "len": len,
    "min": min,
    "max": max,
    "enumerate": enumerate,
    "sum": sum,
    "print": print,
    "abs": abs,
}


class HwpScriptRunner:
    """
    Minimal execution sandbox that exposes the live pyhwpx.Hwp instance
    plus a few safe helper functions.
    """

    def __init__(self, controller: HwpController) -> None:
        self._controller = controller

    def run(self, script: str, log: LogFn | None = None) -> None:
        log_fn = log or (lambda *_: None)
        cleaned = textwrap.dedent(script or "").strip()
        if not cleaned:
            log_fn("빈 스크립트라서 실행하지 않았습니다.")
            return

        hwp_obj = self._controller._ensure_connected()
        if hasattr(hwp_obj, "insert_text") and not hasattr(hwp_obj, "InsertText"):
            setattr(hwp_obj, "InsertText", hwp_obj.insert_text)

        def _insert_equation(
            expr: str,
            *,
            font_size_pt: float = 18.0,
            eq_font_name: str = "HancomEQN",
            treat_as_char: bool = True,
            ensure_newline: bool = False,
            assume_hwpeqn: bool = False,
        ) -> None:
            text = (expr or "").strip()
            if not text:
                return
            hwpeqn = text if assume_hwpeqn else latex_to_hwpeqn(text)
            self._controller.insert_equation(
                hwpeqn,
                font_size_pt=font_size_pt,
                eq_font_name=eq_font_name,
                treat_as_char=treat_as_char,
                ensure_newline=ensure_newline,
            )

        env: Dict[str, object] = {
            "__builtins__": SAFE_BUILTINS,
            "hwp": hwp_obj,
            "controller": self._controller,
            "insert_text": self._controller.insert_text,
            "insert_paragraph": self._controller.insert_paragraph_break,
            "insert_math_text": self._controller.insert_math_text,
            "insert_equation_via_editor": self._controller.insert_equation_via_editor,
            "open_formula_editor": self._controller.open_formula_editor,
            "write_in_formula_editor": self._controller.write_in_formula_editor,
            "type_in_open_formula_editor": self._controller.type_in_open_formula_editor,
            "insert_image": self._controller.insert_image,
            "insert_table": self._controller.insert_table,
            "insert_equation": _insert_equation,
            "insert_hwpeqn": lambda hwpeqn, **kwargs: _insert_equation(
                hwpeqn, assume_hwpeqn=True, **kwargs
            ),
        }

        log_fn("스크립트 실행 시작")
        try:
            exec(cleaned, env, {})
        except Exception as exc:
            tb = traceback.format_exc()
            log_fn(tb)
            logger.exception("Failed to run script: %s", exc)
            raise
        else:
            log_fn("스크립트 실행 완료")

