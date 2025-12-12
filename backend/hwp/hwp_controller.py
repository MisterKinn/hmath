"""
Utility wrapper around pyhwpx that hides COM-specific details from the rest
of the application.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any

from backend.hwp.hwp_equation_utils import (
    EquationAutomationError,
    EquationOptions,
    insert_equation_control,
)

try:
    import pyhwpx  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    pyhwpx = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)


class HwpControllerError(RuntimeError):
    """Base exception for HWP automation failures."""


class HwpNotAvailableError(HwpControllerError):
    """Raised when pyhwpx / HWP automation is unavailable on the host OS."""


@dataclass
class HwpConnectionOptions:
    """
    Simple container for configuring how we attach to Hancom Hangul.

    Attributes:
        visible: Whether to show the Hangul window when connecting.
        new_instance: Whether to force a new Hangul instance.
        register_module: Whether to auto-register the security module.
    """

    visible: bool = True
    new_instance: bool = False
    register_module: bool = True


class HwpController:
    """
    High-level automation helper that exposes safe operations to the pipeline.

    Only a subset of pyhwpx is surfaced here so the GUI / pipeline code can
    remain clean and platform-agnostic.
    """

    def __init__(self, options: Optional[HwpConnectionOptions] = None) -> None:
        self._options = options or HwpConnectionOptions()
        self._hwp: Optional[Any] = None

    # ------------------------------------------------------------------ #
    # Connection management
    # ------------------------------------------------------------------ #
    def connect(self) -> None:
        """Attach to (or create) a running Hancom Hangul instance."""
        if pyhwpx is None:  # pragma: no cover
            raise HwpNotAvailableError(
                "pyhwpx is not installed. Install it on Windows with Hancom Hangul."
            )

        if self._hwp is not None:
            return

        try:
            self._hwp = pyhwpx.Hwp(
                new=self._options.new_instance,
                visible=self._options.visible,
                register_module=self._options.register_module,
            )
            logger.info("Connected to Hancom Hangul successfully.")
        except Exception as exc:  # pragma: no cover
            self._hwp = None
            raise HwpControllerError(
                f"Failed to connect to Hancom Hangul: {exc}"
            ) from exc

    @property
    def is_connected(self) -> bool:
        return self._hwp is not None

    def _ensure_connected(self) -> Any:
        if self._hwp is None:
            raise HwpControllerError("HwpController.connect() must be called first.")
        return self._hwp

    # ------------------------------------------------------------------ #
    # Text helpers
    # ------------------------------------------------------------------ #
    def insert_text(self, text: str) -> None:
        """
        Insert raw text at the current caret position.

        The pyhwpx helper already handles the InsertText action, but we keep
        the call centralized here for logging / sanitizing.
        """
        if not text:
            return

        hwp = self._ensure_connected()
        normalized = text.replace("\n", "\r\n")
        try:
            hwp.insert_text(normalized)
        except Exception as exc:
            raise HwpControllerError(f"Failed to insert text: {exc}") from exc

    def insert_paragraph_break(self) -> None:
        """Insert a paragraph break (equivalent to pressing Enter)."""
        hwp = self._ensure_connected()
        try:
            hwp.BreakPara()
        except Exception as exc:
            raise HwpControllerError(f"Failed to break paragraph: {exc}") from exc

    # ------------------------------------------------------------------ #
    # Advanced placeholders (implemented later)
    # ------------------------------------------------------------------ #
    def insert_equation(
        self,
        hwpeqn: str,
        *,
        font_size_pt: float = 18.0,
        eq_font_name: str = "HancomEQN",
        treat_as_char: bool = True,
        ensure_newline: bool = False,
    ) -> None:
        """
        Insert an equation control using Hancom's InsertEquation action.

        The provided string must be HWP equation language (HwpEqn). The GUI /
        pipeline is responsible for converting LaTeX to HwpEqn prior to calling
        this helper.
        """
        content = hwpeqn.strip()
        if not content:
            return

        hwp = self._ensure_connected()
        options = EquationOptions(
            font_size_pt=font_size_pt,
            eq_font_name=eq_font_name,
            treat_as_char=treat_as_char,
            ensure_newline=ensure_newline,
        )
        try:
            insert_equation_control(hwp, content, options=options)
            return
        except EquationAutomationError as exc:
            logger.debug("EquationCreate flow unavailable, falling back: %s", exc)

        try:
            # Preferred path (pyhwpx provides strongly-typed parameter sets)
            action = hwp.HAction
            param = hwp.HParameterSet.HInsertEquation
            action.GetDefault("InsertEquation", param.HSet)
            param.Equation = content
            action.Execute("InsertEquation", param.HSet)
        except AttributeError:
            # Fallback for pyhwpx versions without strongly typed parameter sets.
            action = hwp.HAction
            param_set = hwp.CreateSet("HInsertEquation")
            action.GetDefault("InsertEquation", param_set)
            param_set.SetItem("Equation", content)
            action.Execute("InsertEquation", param_set)
        except Exception as exc:
            raise HwpControllerError(f"Failed to insert equation: {exc}") from exc

    def insert_image(
        self,
        image_path: str,
        treat_as_char: bool = True,
        width_mm: Optional[float] = None,
        height_mm: Optional[float] = None,
    ) -> None:
        """
        Insert an image at the current caret position.
        """
        path = Path(image_path)
        if not path.exists():
            raise HwpControllerError(f"Image file does not exist: {image_path}")

        hwp = self._ensure_connected()
        try:
            hwp.insert_picture(
                str(path.resolve()),
                treat_as_char=treat_as_char,
                width=int(width_mm or 0),
                height=int(height_mm or 0),
            )
        except AttributeError:
            hwp.InsertPicture(
                str(path.resolve()),
                treat_as_char=treat_as_char,
                width=int(width_mm or 0),
                height=int(height_mm or 0),
            )
        except Exception as exc:
            raise HwpControllerError(f"Failed to insert image: {exc}") from exc

    def insert_table(
        self,
        rows: int = 3,
        cols: int = 3,
        treat_as_char: bool = False,
        width_mm: Optional[float] = None,
        cell_data: Optional[list] = None,
    ) -> None:
        """
        Insert a table at the current caret position.
        
        Args:
            rows: Number of rows
            cols: Number of columns
            treat_as_char: Whether to treat table as character
            width_mm: Table width in millimeters
            cell_data: Optional 2D list of cell contents [[row1_col1, row1_col2], [row2_col1, row2_col2]]
        """
        hwp = self._ensure_connected()
        try:
            # Create table using CreateTable action
            action = hwp.HAction
            if hasattr(hwp.HParameterSet, 'HTableCreation'):
                param = hwp.HParameterSet.HTableCreation
                action.GetDefault("TableCreate", param.HSet)
                param.Rows = rows
                param.Cols = cols
                param.TreatAsChar = treat_as_char
                if width_mm:
                    param.Width = int(width_mm * 100)  # Convert to hwp units
                action.Execute("TableCreate", param.HSet)
            else:
                # Fallback for older pyhwpx versions
                param_set = hwp.CreateSet("HTableCreation")
                action.GetDefault("TableCreate", param_set)
                param_set.SetItem("Rows", rows)
                param_set.SetItem("Cols", cols)
                param_set.SetItem("TreatAsChar", treat_as_char)
                if width_mm:
                    param_set.SetItem("Width", int(width_mm * 100))
                action.Execute("TableCreate", param_set)
            
            # Fill table with data if provided
            if cell_data:
                for row_idx, row in enumerate(cell_data):
                    if row_idx >= rows:
                        break
                    for col_idx, cell_value in enumerate(row):
                        if col_idx >= cols:
                            break
                        # Move to cell and insert text
                        hwp.Run("MoveToCell")
                        if cell_value:
                            self.insert_text(str(cell_value))
                        # Move to next cell
                        hwp.Run("MoveToCell")
                        
        except Exception as exc:
            raise HwpControllerError(f"Failed to insert table: {exc}") from exc


