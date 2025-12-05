import asyncio
import os
import pty
from fastapi import APIRouter, WebSocket
from fastapi.websockets import WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/terminal")
async def terminal_ws(ws: WebSocket):
    """
    Lokal iMac üzerinde çalışan basit bir PTY terminal.
    Sadece LAN içinden erişilen Uvicorn instance'ı için.
    """
    await ws.accept()

    # zsh yoksa "bash" ile değiştirirsin
    pid, fd = pty.fork()
    if pid == 0:
        # Child: shell'i exec et
        os.execvp("zsh", ["zsh"])

    loop = asyncio.get_event_loop()

    async def read_from_pty():
        try:
            while True:
                data = await loop.run_in_executor(None, os.read, fd, 1024)
                if not data:
                    break
                # Terminal çıktısını web'e gönder
                await ws.send_text(data.decode(errors="ignore"))
        except Exception:
            # Sessizce bit
            pass

    reader_task = asyncio.create_task(read_from_pty())

    try:
        while True:
            msg = await ws.receive_text()
            if msg.strip() == "__EXIT__":
                break
            os.write(fd, msg.encode())
    except WebSocketDisconnect:
        pass
    finally:
        reader_task.cancel()
        try:
            os.close(fd)
        except OSError:
            pass
