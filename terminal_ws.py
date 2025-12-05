
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        await ws.send_text("iMac terminale bağlandı. Komut yaz ve Enter'a bas.\\n")
        while True:
            cmd = await ws.receive_text()
            cmd = cmd.strip()
            if not cmd:
                continue
            # Basit exit
            if cmd in {"exit", "quit"}:
                await ws.send_text("Bağlantı kapatılıyor...\\n")
                break

            # Komutu çalıştır
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            out, _ = await proc.communicate()
            text = out.decode("utf-8", errors="ignore")
            if not text.strip():
                text = "(Komuttan çıktı gelmedi.)\\n"
            await ws.send_text(f"$ {cmd}\\n{text}\\n")
    except WebSocketDisconnect:
        # Sessizce çık
        pass
