from __future__ import annotations

from pathlib import Path
import argparse
import signal
import tempfile
import threading

from djconnect_pi.client_api import ClientAPI
from djconnect_pi.client_api import ClientAPIState
from djconnect_pi.config import Config
from djconnect_pi.config import save_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18080)
    parser.add_argument("--token", default="ci-token")
    parser.add_argument("--ready-file")
    args = parser.parse_args()

    stop_event = threading.Event()
    signal.signal(signal.SIGTERM, lambda _signum, _frame: stop_event.set())
    signal.signal(signal.SIGINT, lambda _signum, _frame: stop_event.set())

    with tempfile.TemporaryDirectory(prefix="djconnect-postman-") as tmp:
        tmp_path = Path(tmp)
        cfg = Config(
            device_id="djconnect-raspberry-pi-ABCDEF123456",
            device_name="DJConnect CI",
            device_token=args.token,
            ha_url="http://homeassistant.local:8123",
            paired=True,
            local_api_host=args.host,
            local_api_port=args.port,
            screenshot_file=str(tmp_path / "screenshot.png"),
        )
        config_path = tmp_path / "config.json"
        save_config(config_path, cfg)

        def playback_provider() -> dict[str, object]:
            return {
                "title": "CI Track",
                "artist": "DJConnect",
                "is_playing": False,
                "volume": 35,
            }

        def command_handler(command: str, payload: dict[str, object]) -> dict[str, object]:
            return {"success": True, "command": command, "payload": payload}

        def screenshot_handler() -> dict[str, object]:
            return {
                "success": True,
                "path": str(tmp_path / "screenshot.png"),
                "content_type": "image/png",
                "size": 0,
                "content_base64": "",
            }

        state = ClientAPIState(
            cfg=cfg,
            config_path=config_path,
            playback_provider=playback_provider,
            command_handler=command_handler,
            screenshot_handler=screenshot_handler,
            pair_handler=lambda: None,
            forget_handler=lambda: None,
        )
        api = ClientAPI(state)
        local_url = api.start()
        if args.ready_file:
            Path(args.ready_file).write_text(local_url, encoding="utf-8")
        try:
            stop_event.wait()
        finally:
            api.stop()


if __name__ == "__main__":
    main()
