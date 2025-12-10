from __future__ import annotations

import asyncio
import json
import logging
import ssl
from typing import Any, Optional

from aiohttp import ClientSession, ClientWebSocketResponse, WSMsgType

_LOGGER = logging.getLogger(__name__)


class SiegeniaClient:
    """Async WebSocket client for Siegenia devices."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 443,
        use_ssl: bool = True,
        heartbeat_seconds: int = 10,
        session: Optional[ClientSession] = None,
    ) -> None:
        self._host = host
        self._username = username
        self._password = password
        self._port = port
        self._use_ssl = use_ssl
        self._hb = heartbeat_seconds
        self._session = session
        self._ws: Optional[ClientWebSocketResponse] = None
        self._req_id = 0
        self._pending: dict[int, asyncio.Future] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._receiver_task: Optional[asyncio.Task] = None
        self._token: Optional[str] = None
        self.on_push = None  # optional callback for unsolicited frames
        self._connect_lock: asyncio.Lock = asyncio.Lock()

    @property
    def connected(self) -> bool:
        return self._ws is not None and not self._ws.closed

    async def connect(self) -> None:
        async with self._connect_lock:
            if self.connected:
                return

            if self._session is None:
                self._session = ClientSession()

            scheme = "wss" if self._use_ssl else "ws"
            url = f"{scheme}://{self._host}:{self._port}/WebSocket"

            ssl_ctx = None
            if self._use_ssl:
                import asyncio
                from functools import partial
                
                # SSL Context im Executor erstellen (non-blocking)
                loop = asyncio.get_event_loop()
                ssl_ctx = await loop.run_in_executor(
                    None, 
                    ssl.create_default_context
                )
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE

            _LOGGER.debug("Connecting WS to %s", url)
            self._ws = await self._session.ws_connect(
                url,
                ssl=ssl_ctx,
                headers={"Origin": f"{scheme}://{self._host}:{self._port}"},
            )

            # Start receiver and heartbeat, then login
            self._receiver_task = asyncio.create_task(self._receiver())
            await self.login(self._username, self._password)
            self._heartbeat_task = asyncio.create_task(self._heartbeat())
            _LOGGER.debug("WS connected")

    async def _receiver(self) -> None:
        assert self._ws is not None
        ws = self._ws
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except Exception as exc:
                    _LOGGER.warning("WS JSON error: %s (%s)", exc, msg.data)
                    continue

                rid = data.get("id")
                status = data.get("status")
                payload = data.get("data")
                fut = self._pending.pop(rid, None)
                if fut is not None and not fut.done():
                    fut.set_result((status, payload))
                else:
                    # unsolicited push
                    try:
                        if callable(self.on_push):
                            self.on_push(data)
                    except Exception as _exc:
                        _LOGGER.debug("on_push callback error: %s", _exc)
            elif msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.ERROR):
                _LOGGER.debug("WS closed: %s", msg.type)
                break

        # mark closed
        try:
            if self._ws and not self._ws.closed:
                await self._ws.close()
        except Exception:
            pass
        self._ws = None

    async def close(self) -> None:
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        if self._receiver_task:
            self._receiver_task.cancel()
            self._receiver_task = None
        if self._ws and not self._ws.closed:
            await self._ws.close()
        self._ws = None
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None

    async def _send(self, command: Any, params: Optional[dict] = None, timeout: float = 5.0):
        if not self.connected:
            await self.connect()
            if not self.connected:
                raise RuntimeError("WS not connected")

        self._req_id += 1
        rid = self._req_id

        if isinstance(command, str):
            req = {"command": command}
        else:
            req = dict(command)
        if params is not None:
            req["params"] = params
        req["id"] = rid

        loop = asyncio.get_event_loop()
        fut: asyncio.Future = loop.create_future()
        self._pending[rid] = fut

        try:
            assert self._ws is not None
            await self._ws.send_str(json.dumps(req))
        except Exception:
            # reconnect once and retry
            await self.connect()
            try:
                assert self._ws is not None
                await self._ws.send_str(json.dumps(req))
            except Exception as exc:
                self._pending.pop(rid, None)
                raise

        try:
            status, payload = await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(rid, None)
            raise TimeoutError("Siegenia request timed out")
        if status != "ok":
            raise RuntimeError(f"Siegenia error: {status}")
        return payload

    async def login(self, username: str, password: str) -> dict:
        payload = await self._send({"command": "login", "user": username, "password": password, "long_life": False})
        token = payload.get("token") if isinstance(payload, dict) else None
        self._token = token
        return payload

    async def keep_alive(self) -> None:
        await self._send("keepAlive", {"extend_session": True})

    async def _heartbeat(self) -> None:
        while True:
            try:
                await asyncio.sleep(self._hb)
                await self.keep_alive()
            except asyncio.CancelledError:
                return
            except Exception as exc:
                _LOGGER.debug("Heartbeat error: %s", exc)

    # Device commands
    async def get_device(self) -> dict:
        return await self._send("getDevice")

    async def get_device_state(self) -> dict:
        return await self._send("getDeviceState")

    async def get_device_params(self) -> dict:
        return await self._send("getDeviceParams")

    async def set_device_params(self, params: dict) -> dict:
        return await self._send("setDeviceParams", params=params)

    async def reboot_device(self) -> None:
        await self._send("rebootDevice")

    async def reset_device(self) -> None:
        await self._send("resetDevice")

    async def renew_cert(self) -> None:
        await self._send("renewCert")
