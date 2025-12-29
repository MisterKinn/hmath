"""
Low-level helpers for inserting Hancom Hangul equation controls via COM.

This mirrors the manual automation flow provided by the user:
1. Run ``EquationCreate`` with the desired HwpEqn string and font metrics.
2. Re-open the property dialog to ensure the newest equation engine is used.
3. Treat the control as an inline character so subsequent text flows naturally.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EquationOptions:
    """Display options applied right after creating the equation control."""

    font_size_pt: float = 18.0
    eq_font_name: str = "HancomEQN"
    treat_as_char: bool = True
    ensure_newline: bool = False


class EquationAutomationError(RuntimeError):
    """Raised when low-level equation actions cannot be executed."""


def insert_equation_control(
    hwp: Any,
    hwpeqn: str,
    *,
    options: EquationOptions | None = None,
) -> None:
    """
    Insert a Hancom equation control using the same flow as the native UI.

    The caller must pass a connected HWP COM object (``pyhwpx.Hwp`` or
    ``win32com.client.Dispatch``). ``hwpeqn`` must already be encoded in the
    HwpEqn mini-language.
    """
    text = (hwpeqn or "").strip()
    if not text:
        return

    opts = options or EquationOptions()

    try:
        action = hwp.HAction
        param_sets = hwp.HParameterSet
    except AttributeError as exc:  # pragma: no cover - unsupported runtime
        raise EquationAutomationError("HAction interface is missing on this HWP session.") from exc

    try:
        # 1) Create the equation with precise font size settings.
        eq_param = param_sets.HEqEdit
        action.GetDefault("EquationCreate", eq_param.HSet)
        eq_param.EqFontName = opts.eq_font_name
        eq_param.string = text
        base_unit = _point_to_hwp_unit(hwp, opts.font_size_pt)
        eq_param.BaseUnit = base_unit
        action.Execute("EquationCreate", eq_param.HSet)

        # 2) Re-select and enforce formatting through the property dialog.
        if hasattr(hwp, "FindCtrl"):
            hwp.FindCtrl()
        shape_param = param_sets.HShapeObject
        action.GetDefault("EquationPropertyDialog", shape_param.HSet)
        shape_param.HSet.SetItem("ShapeType", 3)  # 3 == Equation
        shape_param.Version = "Equation Version 60"
        shape_param.EqFontName = opts.eq_font_name
        shape_param.HSet.SetItem("ApplyTo", 0)  # Current selection only
        shape_param.HSet.SetItem("TreatAsChar", 1 if opts.treat_as_char else 0)
        action.Execute("EquationPropertyDialog", shape_param.HSet)

        # EquationPropertyDialog is modeled as a modal dialog; close it with Cancel
        # so the COM automation can continue without UI interruptions.
        hwp.Run("Cancel")

        # 3) Move caret outside the control (and optionally break the paragraph).
        action.Run("MoveRight")
        if opts.ensure_newline:
            action.Run("BreakPara")
    except EquationAutomationError:
        raise
    except Exception as exc:  # pragma: no cover - actual HWP automation error
        raise EquationAutomationError(f"Failed to insert equation: {exc}") from exc


def _point_to_hwp_unit(hwp: Any, point: float) -> float:
    """Convert a point size into HWP internal units, with graceful fallback."""
    if point <= 0:
        return 0.0
    if hasattr(hwp, "PointToHwpUnit"):
        return hwp.PointToHwpUnit(point)
    # Hard-coded fallback: 1pt == 100 Hwp units.
    return point * 100.0
