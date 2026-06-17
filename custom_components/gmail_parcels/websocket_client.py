import asyncio
import contextlib
import json
import logging
from typing import Any, Callable, Dict, List, Optional

import aiohttp

_LOGGER = logging.getLogger(__name__)


class WebsocketClient:
    def __init__(self, url: str) -> None:
        self._url = url
        self._session: Optional[aiohttp.ClientSession] = None
        self._task: Optional[asyncio.Task] = None
        self._data: Dict[str, Any] = {}
        self._callbacks: List[Callable[[], None]] = []

    async def async_start(self) -> None:
        if self._task:
            return
        self._session = aiohttp.ClientSession()
        self._task = asyncio.create_task(self._run())

    async def async_stop(self) -> None:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        if self._session:
            await self._session.close()

    def subscribe(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Register a callback; returns an unsubscribe function."""
        self._callbacks.append(callback)

        def _unsubscribe() -> None:
            with contextlib.suppress(ValueError):
                self._callbacks.remove(callback)

        return _unsubscribe

    @property
    def data(self) -> Dict[str, Any]:
        return self._data

    async def _run(self) -> None:
        assert self._session is not None
        while True:
            try:
                async with self._session.ws_connect(self._url) as ws:
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            self._handle_message(msg.data)
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            _LOGGER.warning("websocket error: %s", msg.data)
                            break
            except Exception as err:  # pragma: no cover - startup retry
                _LOGGER.warning("websocket connection failed: %s", err)
                await asyncio.sleep(5)

    def _handle_message(self, raw: str) -> None:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            _LOGGER.debug("skipping non-json message")
            return
        if payload.get("type") != "parcels":
            return
        self._data = payload.get("data", {})
        for cb in self._callbacks:
            cb()
