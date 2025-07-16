import itertools
import sys
import threading
import time


class Spinner:
    """Simple command-line spinner animation."""

    def __init__(self, message: str = "Loading"):
        self._message = message
        self._spinner = itertools.cycle(['|', '/', '-', '\\'])
        self._running = False
        self._thread = None

    def start(self) -> None:
        """Start the spinner in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._animate)
        self._thread.start()

    def _animate(self) -> None:
        while self._running:
            sys.stdout.write(f"\r{self._message} {next(self._spinner)}")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * (len(self._message) + 2) + "\r")
        sys.stdout.flush()

    def stop(self) -> None:
        """Stop the spinner and wait for the thread to finish."""
        if not self._running:
            return
        self._running = False
        if self._thread:
            self._thread.join()
            self._thread = None
