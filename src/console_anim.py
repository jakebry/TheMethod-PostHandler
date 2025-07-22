import itertools
import sys
import threading
import time


class Spinner:
    """Simple command-line spinner animation, or simple log messages in non-interactive/cloud environments."""

    def __init__(self, message: str = "Loading"):
        self._message = message
        self._spinner = itertools.cycle(['|', '/', '-', '\\'])
        self._running = False
        self._thread = None
        self._is_tty = sys.stdout.isatty()

    def start(self) -> None:
        """Start the spinner in a background thread, or print a start log if not a TTY."""
        if self._running:
            return
        self._running = True
        if self._is_tty:
            self._thread = threading.Thread(target=self._animate)
            self._thread.start()
        else:
            print(f"[START] {self._message}")

    def _animate(self) -> None:
        while self._running:
            sys.stdout.write(f"\r{self._message} {next(self._spinner)}")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * (len(self._message) + 2) + "\r")
        sys.stdout.flush()

    def step(self, detail: str) -> None:
        """Log a progress step. In TTY, does nothing (spinner animates). In cloud, prints a short log."""
        if not self._is_tty:
            print(f"[STEP] {detail}")

    def stop(self, status: str = "DONE") -> None:
        """Stop the spinner and print a stop log if not a TTY."""
        if not self._running:
            return
        self._running = False
        if self._is_tty:
            if self._thread:
                self._thread.join()
                self._thread = None
        else:
            print(f"[{status}] {self._message}")
