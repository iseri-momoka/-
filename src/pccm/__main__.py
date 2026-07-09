"""Entry point for ``python -m pccm``.

Handles early platform workarounds before handing off to the GUI app.
"""

from __future__ import annotations


def main() -> None:
    """Application entry point."""
    import sys

    # Force high-DPI scaling on Qt 6 before QApplication is created.
    # This must happen before any PySide6 import.
    from pccm.config import Config  # noqa: E402

    Config.ensure_directories()

    from pccm.app import create_app, run

    app = create_app(sys.argv)
    run(app)


if __name__ == "__main__":
    main()
