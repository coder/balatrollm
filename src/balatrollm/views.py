"""HTTP server for serving views and run data."""

import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

VIEWS_PORT = 12345


class SilentHTTPRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler that suppresses access logs."""

    def log_message(self, format: str, *args) -> None:
        """Override to suppress HTTP access logging."""
        pass


class ViewsServer:
    """Background HTTP server for views."""

    def __init__(self, root_dir: Path):
        """Initialize server with project root directory.

        Args:
            root_dir: Project root directory (parent of views/ and runs/)
        """
        self.root_dir = root_dir
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the server in a background thread."""
        handler = partial(SilentHTTPRequestHandler, directory=str(self.root_dir))
        self._server = HTTPServer(("", VIEWS_PORT), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        print("Views available at:")
        print(f"  http://localhost:{VIEWS_PORT}/views/task.html")
        print(f"  http://localhost:{VIEWS_PORT}/views/responses.html")

    def stop(self) -> None:
        """Stop the server."""
        if self._server:
            self._server.shutdown()
