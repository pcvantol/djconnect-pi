from __future__ import annotations

from pathlib import Path
import argparse
import threading
import tkinter as tk
from tkinter import simpledialog

from .config import DEFAULT_CONFIG_PATH, load_config, save_config
from .ha import DJConnectError, HAClient, Playback


class DJConnectApp:
    def __init__(self, root: tk.Tk, config_path: Path) -> None:
        self.root = root
        self.config_path = config_path
        self.cfg = load_config(config_path)
        self.client = HAClient(self.cfg)
        self.playback = Playback()
        self.status_var = tk.StringVar(value="Not paired")
        self.track_var = tk.StringVar(value=self.playback.title)
        self.artist_var = tk.StringVar(value="")
        self.volume_var = tk.IntVar(value=self.playback.volume)
        self.shuffle_var = tk.BooleanVar(value=False)
        self.repeat_var = tk.StringVar(value="off")
        self._build_ui()
        self.root.after(400, self.ensure_paired)
        self.root.after(2500, self.refresh)

    def _build_ui(self) -> None:
        self.root.title("DJConnect Pi")
        self.root.geometry("720x720")
        self.root.configure(bg="#101416")
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda _event: self.root.attributes("-fullscreen", False))

        tk.Label(self.root, textvariable=self.status_var, fg="#9fb4b8", bg="#101416", font=("Helvetica", 14)).pack(pady=(18, 8))
        art = tk.Frame(self.root, width=360, height=280, bg="#263136", highlightthickness=1, highlightbackground="#4b5f66")
        art.pack_propagate(False)
        art.pack(pady=8)
        tk.Label(art, text="DJConnect", fg="#eaf4f5", bg="#263136", font=("Helvetica", 34, "bold")).pack(expand=True)

        tk.Label(self.root, textvariable=self.track_var, fg="#f5f7f7", bg="#101416", font=("Helvetica", 25, "bold"), wraplength=650).pack(pady=(16, 2))
        tk.Label(self.root, textvariable=self.artist_var, fg="#b7c7ca", bg="#101416", font=("Helvetica", 17), wraplength=650).pack(pady=(0, 18))

        controls = tk.Frame(self.root, bg="#101416")
        controls.pack(pady=10)
        self._button(controls, "Prev", lambda: self.send("previous")).grid(row=0, column=0, padx=10)
        self.play_button = self._button(controls, "Play", self.toggle_play, width=9, height=2)
        self.play_button.grid(row=0, column=1, padx=10)
        self._button(controls, "Next", lambda: self.send("next")).grid(row=0, column=2, padx=10)

        volume = tk.Scale(
            self.root,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.volume_var,
            command=self.set_volume,
            length=560,
            bg="#101416",
            fg="#f5f7f7",
            troughcolor="#263136",
            highlightthickness=0,
            font=("Helvetica", 12),
        )
        volume.pack(pady=24)

        toggles = tk.Frame(self.root, bg="#101416")
        toggles.pack(pady=6)
        tk.Checkbutton(
            toggles,
            text="Shuffle",
            variable=self.shuffle_var,
            command=self.set_shuffle,
            indicatoron=False,
            width=10,
            height=2,
            bg="#263136",
            fg="#f5f7f7",
            selectcolor="#1db954",
            font=("Helvetica", 15, "bold"),
        ).grid(row=0, column=0, padx=10)
        self._button(toggles, "Repeat", self.cycle_repeat, width=10).grid(row=0, column=1, padx=10)

    def _button(self, parent: tk.Widget, text: str, command, width: int = 7, height: int = 2) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            height=height,
            bg="#1db954",
            fg="#06100a",
            activebackground="#47d976",
            relief="flat",
            font=("Helvetica", 17, "bold"),
        )

    def ensure_paired(self) -> None:
        if not self.cfg.ha_url:
            value = simpledialog.askstring("DJConnect", "Home Assistant URL", parent=self.root)
            if value:
                self.cfg.ha_url = value.strip()
                save_config(self.config_path, self.cfg)
        if not self.cfg.paired or not self.cfg.device_token:
            code = simpledialog.askstring("DJConnect", "Pairing code", parent=self.root)
            if code:
                self._background(lambda: self._pair(code.strip()))

    def _pair(self, code: str) -> None:
        try:
            self.client.pair(code)
            save_config(self.config_path, self.cfg)
            self.status_var.set("Paired")
        except Exception as exc:
            self.status_var.set(f"Pairing failed: {exc}")

    def refresh(self) -> None:
        self._background(self._refresh)
        self.root.after(5000, self.refresh)

    def _refresh(self) -> None:
        try:
            data = self.client.command("status") if self.cfg.paired else self.client.status()
            self.playback = self.client.playback_from_status(data)
            self.root.after(0, self._render_playback)
            self.client.status(self.playback)
        except Exception as exc:
            self.root.after(0, lambda: self.status_var.set(f"Offline: {exc}"))

    def _render_playback(self) -> None:
        self.status_var.set("Connected")
        self.track_var.set(self.playback.title)
        self.artist_var.set(self.playback.artist)
        self.volume_var.set(self.playback.volume)
        self.shuffle_var.set(self.playback.shuffle)
        self.repeat_var.set(self.playback.repeat)
        self.play_button.configure(text="Pause" if self.playback.is_playing else "Play")

    def toggle_play(self) -> None:
        self.send("pause" if self.playback.is_playing else "play")

    def set_volume(self, value: str) -> None:
        self._background(lambda: self.send("set_volume", value=int(float(value))))

    def set_shuffle(self) -> None:
        self.send("set_shuffle", value=bool(self.shuffle_var.get()))

    def cycle_repeat(self) -> None:
        next_value = {"off": "context", "context": "track", "track": "off"}.get(self.repeat_var.get(), "off")
        self.repeat_var.set(next_value)
        self.send("set_repeat", value=next_value)

    def send(self, command: str, **payload) -> None:
        def work() -> None:
            try:
                data = self.client.command(command, **payload)
                self.playback = self.client.playback_from_status(data)
                self.root.after(0, self._render_playback)
            except DJConnectError as exc:
                self.root.after(0, lambda: self.status_var.set(str(exc)))

        self._background(work)

    def _background(self, target) -> None:
        threading.Thread(target=target, daemon=True).start()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--ha-url", default="")
    args = parser.parse_args()
    cfg = load_config(args.config)
    if args.ha_url:
        cfg.ha_url = args.ha_url
        save_config(args.config, cfg)
    root = tk.Tk()
    DJConnectApp(root, args.config)
    root.mainloop()


if __name__ == "__main__":
    main()

