"""Entry point for ``python -m pccm``.

Dispatches between GUI mode (default) and CLI mode (``python -m pccm cli``).
"""

from __future__ import annotations


def main() -> None:
    """Application entry point."""
    import sys

    # CLI mode: python -m pccm cli [commands...]
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        from pccm.cli.dispatcher import dispatch

        sys.exit(dispatch(sys.argv[2:]))
        return

    # GUI mode (default)
    # Force high-DPI scaling on Qt 6 before QApplication is created.
    # This must happen before any PySide6 import.
    from pccm.config import Config  # noqa: E402

    Config.ensure_directories()

    from pccm.app import create_app, run

    app = create_app(sys.argv)
    run(app)


if __name__ == "__main__":
    main()
