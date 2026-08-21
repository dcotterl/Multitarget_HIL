"""GUI entry points for the Multitarget HIL package."""


def main():
    """Launch the Tkinter GUI on demand."""

    from .app import main as run_main

    run_main()


__all__ = ["main"]
