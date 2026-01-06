"""
WebSocket Stream Server
OBS에서 JPEG 프레임을 실시간으로 수신하는 WebSocket 서버
"""

import asyncio
import logging
from typing import Optional

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

from .frame_queue import get_queue

logger = logging.getLogger("VisionStreamServer")

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 6060


class VisionStreamServer:
    """OBS WebSocket 프레임 수신 서버"""
    
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, queue_maxsize: int = 10):
        self.host = host
        self.port = port
        self.queue = get_queue(queue_maxsize)
        self._server = None
        self._running = False
        self._client_count = 0
        
    async def handler(self, websocket) -> None:
        """WebSocket 연결 핸들러"""
        client_id = self._client_count
        self._client_count += 1
        logger.info(f"👁️ Client #{client_id} connected from {websocket.remote_address}")
        
        try:
            async for message in websocket:
                if isinstance(message, bytes):
                    await self.queue.put(message)
                    if self.queue.total_frames % 100 == 0:
                        stats = self.queue.stats()
                        logger.info(f"📊 Frames: {stats['total_frames']} | Dropped: {stats['dropped_frames']}")
                elif message == "ping":
                    await websocket.send("pong")
                elif message == "stats":
                    import json
                    await websocket.send(json.dumps(self.queue.stats()))
        except Exception as e:
            logger.info(f"Client #{client_id} disconnected: {e}")
    
    async def start(self) -> None:
        """서버 시작"""
        if not WEBSOCKETS_AVAILABLE:
            logger.error("websockets 패키지 필요: pip install websockets")
            return
        self._running = True
        self._server = await websockets.serve(self.handler, self.host, self.port, max_size=10*1024*1024)
        logger.info(f"🚀 Vision Stream Server: ws://{self.host}:{self.port}")
        await self._server.wait_closed()
    
    async def stop(self) -> None:
        """서버 종료"""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    server = VisionStreamServer()
    try:
        await server.start()
    except KeyboardInterrupt:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
