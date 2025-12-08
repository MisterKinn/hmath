"""
Python wrapper that shells out to the Node CLI for LaTeX -> HwpEqn conversion.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NODE_CLI = PROJECT_ROOT / "node_eqn" / "hwp_eqn_cli.js"


class LatexConversionError(RuntimeError):
    pass


def latex_to_hwpeqn(latex: str, timeout: float = 15.0) -> str:
    """
    Convert LaTeX into the HwpEqn syntax using the Node CLI.

    Returns the original LaTeX string if conversion fails, so the caller can
    still insert something into the document.
    """
    text = latex.strip()
    if not text:
        return ""

    if not NODE_CLI.exists():
        logger.error("Equation CLI not found at %s", NODE_CLI)
        return latex

    cmd = ["node", str(NODE_CLI)]
    try:
        result = subprocess.run(
            cmd,
            input=text,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )
        output = result.stdout.strip()
        if not output:
            logger.warning("Equation converter returned empty output.")
            return latex
        return output
    except FileNotFoundError as exc:
        logger.error("Node.js is not installed or not on PATH: %s", exc)
    except subprocess.CalledProcessError as exc:
        logger.error(
            "Equation converter failed (exit %s): %s",
            exc.returncode,
            exc.stderr.strip(),
        )
    except subprocess.TimeoutExpired:
        logger.error("Equation converter timed out after %s seconds", timeout)
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected error while converting equation: %s", exc)

    return latex

