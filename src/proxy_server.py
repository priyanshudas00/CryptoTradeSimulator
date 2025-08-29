import asyncio
import json
import logging
import websockets
from websockets import WebSocketServerProtocol
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("proxy_server")

# Store connected frontend clients
connected_clients = set()

# Exchange WebSocket URLs (Binance only for now)
EXCHANGE_WS_URLS = {
    "Binance": "wss://stream.binance.com:9443/ws/btcusdt@depth5@100ms"
}

async def exchange_listener(uri: str, forward_queue: asyncio.Queue):
    try:
        async with websockets.connect(uri) as websocket:
            logger.info(f"Connected to exchange WebSocket: {uri}")
            if "coinbase" in uri:
                # Subscribe to level2 channel for Coinbase
                subscribe_msg = {
                    "type": "subscribe",
                    "product_ids": ["BTC-USD"],
                    "channels": ["level2"]
                }
                await websocket.send(json.dumps(subscribe_msg))
            try:
                async for message in websocket:
                    await forward_queue.put(message)
            except websockets.ConnectionClosed:
                logger.warning(f"Connection to exchange {uri} closed")
    except Exception as e:
        logger.error(f"Failed to connect to exchange {uri}: {e}")

async def forward_to_clients(forward_queue: asyncio.Queue):
    while True:
        message = await forward_queue.get()
        if connected_clients:
            logger.info(f"Forwarding message to {len(connected_clients)} clients")
            send_tasks = [asyncio.create_task(client.send(message)) for client in connected_clients]
            await asyncio.wait(send_tasks)

async def register_client(websocket: WebSocketServerProtocol):
    connected_clients.add(websocket)
    logger.info(f"Client connected: {websocket.remote_address}")

async def unregister_client(websocket: WebSocketServerProtocol):
    connected_clients.remove(websocket)
    logger.info(f"Client disconnected: {websocket.remote_address}")

async def proxy_handler(websocket):
    await register_client(websocket)
    try:
        async for message in websocket:
            # For now, just log messages from clients (if any)
            logger.info(f"Received message from client: {message}")
    except websockets.ConnectionClosed:
        pass
    finally:
        await unregister_client(websocket)

async def main():
    forward_queue = asyncio.Queue()

    # Start exchange listeners
    tasks = []
    for uri in EXCHANGE_WS_URLS.values():
        tasks.append(asyncio.create_task(exchange_listener(uri, forward_queue)))

    # Start forwarding task
    tasks.append(asyncio.create_task(forward_to_clients(forward_queue)))

    # Start WebSocket server for frontend clients
    server = await websockets.serve(proxy_handler, "0.0.0.0", 8765)
    logger.info("Proxy WebSocket server started on ws://0.0.0.0:8765")

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Proxy server stopped by user")
