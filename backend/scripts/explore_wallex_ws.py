"""Explore Wallex WebSocket — raw connection, 10s listen, print all messages."""
import json
import time
import websocket

WALLEX_WS = "wss://api.wallex.ir/ws"
DURATION = 10


def main() -> None:
    ws = websocket.create_connection(WALLEX_WS, timeout=10)
    print("✅ connected")

    # Engine.IO handshake: server sends open packet first
    first = ws.recv()
    print("📥 handshake:", first[:200])

    # Socket.IO connect (packet type 40 = connect to default namespace)
    ws.send("40")
    print("📤 sent: 40 (Socket.IO connect)")

    # Subscribe to all@price
    sub = json.dumps(["subscribe", {"channel": "all@price"}])
    ws.send(sub)
    print(f"📤 sent: {sub}")

    end = time.time() + DURATION
    while time.time() < end:
        try:
            msg = ws.recv()
            print("📥", msg[:300])
        except websocket.WebSocketTimeoutException:
            pass

    ws.close()
    print("🏁 done")


if __name__ == "__main__":
    main()
