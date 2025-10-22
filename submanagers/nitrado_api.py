
from __future__ import annotations
import os
import argparse
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import requests

DEFAULT_API_BASE = "https://api.nitrado.net"
TIMEOUT = 20
RETRYABLE = (429, 500, 502, 503, 504)
TOKEN = os.getenv("NITRADO_TKN")
SERVICE_ID = os.getenv("NITRADO_SERVICE_ID")

class NitradoAPIError(Exception):
    """Raised for non-transient API errors or unexpected responses."""

class NitradoApiPlayerInfo:
    name: str
    player: str
    nickname: str

    def __init__(self, data: Dict[str, Any]):
        self.name = data.get("name", "")
        self.player = data.get("player", "")
        self.nickname = data.get("nickname", "")

    def __str__(self) -> str:
        return f"Player {self.name} ({self.player}), nickname {self.nickname}"

class NitradoApiGameServerInfo:
    server_id: int
    status: str
    name: str
    version: str

    def __init__(self, data: Dict[str, Any]):
        self.server_id = data.get("id", 0)
        self.status = data.get("status", "")
        name = data.get("details", {}).get("name", "")
        self.name = name.split("-")[0].strip() if "-" in name else name
        self.version = name.split("-")[-1].strip() if "-" in name else ""
        print(data)

    def __str__(self) -> str:
        return f"GameServer {self.name} (ID: {self.server_id}), status: {self.status}, version: {self.version} "


class NitradoClient:
    """
    Thin wrapper around the Nitrado REST API.

    - token: Nitrado OAuth/long-life token
    - api_base: override API base URL (rarely needed)
    - cert_path: path to a local certificate package (CA/cert/key in PEM).
                 Taken from env var NITRADO_CERT_PATH if not passed.
    """

    def __init__(
        self,
        token: str = TOKEN,
        api_base: str = DEFAULT_API_BASE,
        user_agent: str = "nitrado-asa-client/1.2"
    ):
        if not token:
            raise ValueError("Nitrado token is required")

        self.token = token
        self.api_base = api_base.rstrip("/")
        self.user_agent = user_agent

    # -------------------------
    # Internals
    # -------------------------
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }

    def _request(self, method: str, path: str, *, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.api_base}{path}"
        backoff = 1.0
        for _ in range(5):
            resp = requests.request(
                method,
                url,
                headers=self._headers(),
                json=json,
                timeout=TIMEOUT
            )
            if resp.status_code in RETRYABLE:
                time.sleep(backoff)
                backoff = min(backoff * 2, 8.0)
                continue

            try:
                data = resp.json()
            except Exception:
                raise NitradoAPIError(f"{resp.status_code} {resp.reason}: {resp.text[:200]}")

            if resp.ok:
                return data
            msg = data.get("message") or data.get("error") or f"{resp.status_code} {resp.reason}"
            raise NitradoAPIError(msg)

        raise NitradoAPIError("Repeated transient errors when calling Nitrado API.")

    # -------------------------
    # Public API
    # -------------------------
    def list_services(self) -> List[NitradoApiGameServerInfo]:
        data = self._request("GET", "/services")
        return [NitradoApiGameServerInfo(item) for item in data.get("data", {}).get("services", [])]

    def get_gameserver(self, service_id: str | int=SERVICE_ID) -> Dict[str, Any]:
        return self._request("GET", f"/services/{service_id}/gameservers")

    def get_status(self, service_id: str | int=SERVICE_ID) -> str:
        data = self.get_gameserver(service_id)
        return data["data"]["gameserver"]["status"]

    def start_server(self, service_id: str | int=SERVICE_ID, wait: bool=True) -> None:
        self._request("POST", f"/services/{service_id}/gameservers/restart")

        if wait:
            self.poll_until(("started",), service_id=service_id)

    def stop_server(self, service_id: str | int=SERVICE_ID, *, force: bool = False, wait: bool=True) -> None:
        payload = {"force": True} if force else None
        self._request("POST", f"/services/{service_id}/gameservers/stop", json=payload)

        if wait:
            self.poll_until(("stopped",), service_id=service_id)

    def poll_until(
        self,
        target: Tuple[str, ...],
        *,
        give_up_after: int = 300,
        interval: float = 5.0,
        service_id: str | int=SERVICE_ID,
    ) -> str:
        deadline = time.time() + give_up_after
        last = ""
        while time.time() < deadline:
            last = self.get_status(service_id)
            if last in target:
                return last
            time.sleep(interval)
        return last

    def get_active_players(self, service_id: str | int=SERVICE_ID) -> List[NitradoApiPlayerInfo]:
        data = self.get_gameserver(service_id)
        gs = data.get("data", {}).get("gameserver", {})

        players = []

        if isinstance(gs.get("players"), list):
            players = gs["players"]
        elif isinstance(gs.get("player_list"), list):
            players = gs["player_list"]

        query = gs.get("query") or {}
        if not players and isinstance(query.get("players"), list):
            players = [{"name": n} if not isinstance(n, dict) else n for n in query["players"]]

        players = [NitradoApiPlayerInfo(p) if isinstance(p, dict) else NitradoApiPlayerInfo({"name": str(p)}) for p in players]

        return players
    

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Nitrado ASA server controller")
    p.add_argument("action", choices=["list-services", "status", "start", "stop", "players"], help="Action to perform")

    # Auth & API
    p.add_argument("--token", default=os.getenv("NITRADO_TKN"), help="Nitrado OAuth/long-life token")
    p.add_argument("--service-id", default=os.getenv("NITRADO_SERVICE_ID"), help="Nitrado service ID (numeric)")
    p.add_argument("--api-base", default=DEFAULT_API_BASE, help="Override API base URL (rarely needed)")
    # Behavior
    p.add_argument("--force", action="store_true", help="Use force stop (if supported)")
    p.add_argument("--wait", action="store_true", help="For start/stop: wait until the server reaches target state")
    p.add_argument("--timeout", type=int, default=300, help="Max seconds to wait with --wait (default 300)")
    p.add_argument("--interval", type=float, default=5.0, help="Polling interval seconds (default 5.0)")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    if not args.token:
        print("Missing --token (or NITRADO_TKN env var).", file=sys.stderr)
        return 2

    client = NitradoClient(
        args.token,
        api_base=args.api_base,
        # cert_path=os.environ.get("SCIOTEQ_CA_CERT"),
    )

    try:
        if args.action == "list-services":
            services = client.list_services()
            print(f"{len(services)} service(s) found:")
            for s in services:
                print(f" - {s}")
            return 0

        if not args.service_id:
            print("Missing --service-id (or NITRADO_SERVICE_ID env var) for this action.", file=sys.stderr)
            return 2

        sid = args.service_id

        if args.action == "status":
            print(client.get_status(sid))
            return 0

        if args.action == "start":
            client.start_server(sid)
            if args.wait:
                final = client.poll_until(sid, ("started",), give_up_after=args.timeout, interval=args.interval)
                print(f"started (final state: {final})")
            else:
                print("start requested")
            return 0

        if args.action == "stop":
            client.stop_server(sid, force=args.force)
            if args.wait:
                final = client.poll_until(sid, ("stopped",), give_up_after=args.timeout, interval=args.interval)
                print(f"stopped (final state: {final})")
            else:
                print("stop requested")
            return 0

        if args.action == "players":
            info = client.get_active_players(sid)
            print(f"{len(info)} player(s) online")
            for p in info:
                print(f" - {p}")
            return 0

    except NitradoAPIError as e:
        print(f"Nitrado API error: {e}", file=sys.stderr)
        return 1
    except requests.RequestException as e:
        print(f"Network error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())