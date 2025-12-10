"""JSON-RPC 2.0 HTTP client for communicating with BalatroBot."""

from dataclasses import dataclass, field
from typing import Any, Literal

import httpx


class BalatroError(Exception):
    """Exception raised when BalatroBot returns an error response."""

    def __init__(
        self,
        code: int,
        message: str,
        data: dict[Literal["name"], str],
    ) -> None:
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"[{data['name']}] {message}")


@dataclass
class BalatroClient:
    """JSON-RPC 2.0 client for communicating with BalatroBot.

    Usage:
        with BalatroClient() as client:
            result = client.call("gamestate")
            print(result["state"])
    """

    host: str = "127.0.0.1"
    port: int = 12346
    timeout: float = 30.0

    _client: httpx.Client | None = field(default=None, init=False, repr=False)
    _request_id: int = field(default=0, init=False, repr=False)

    def __enter__(self) -> "BalatroClient":
        """Create and configure the HTTP client."""
        self._client = httpx.Client(
            base_url=f"http://{self.host}:{self.port}",
            timeout=self.timeout,
        )
        return self

    def __exit__(self, *_: Any) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def call(self, method: str, params: dict[str, Any] | None = None) -> Any:
        """Send a JSON-RPC 2.0 request and return the result.

        Args:
            method: The JSON-RPC method name.
            params: Optional parameters for the method.

        Returns:
            The result field from the JSON-RPC response.

        Raises:
            RuntimeError: If called without entering the context manager.
            BalatroError: If the server returns an error response.
        """
        if self._client is None:
            raise RuntimeError(
                "Client not connected. Use 'with BalatroClient() as client:'"
            )

        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self._request_id,
        }

        response = self._client.post("/", json=payload)
        data = response.json()

        if "error" in data:
            error = data["error"]
            raise BalatroError(
                code=error["code"],
                message=error["message"],
                data=error.get("data"),
            )

        return data["result"]
