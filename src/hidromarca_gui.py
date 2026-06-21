import json
import shutil
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
import numpy as np
from PIL import Image, ImageTk

APP_NAME = "HidroMarca GUI"
DEFAULT_TOP_TEXT = "ESTE WEY YA VIVE EN EL 2050"
DEFAULT_HANDLE = "@hidrocalido"


class HidroMarcaApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1180x820")
        self.root.minsize(980, 680)

        self.video_path: Path | None = None
        self.audio_path: Path | None = None
        self.logo_path: Path | None = None
        self.output_path: Path | None = None

        self.frame_bgr: np.ndarray | None = None
        self.frame_w = 0
        self.frame_h = 0
        self.fps = 30.0
        self.total_frames = 0
        self.duration = 0.0

        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.canvas_img = None
        self.tk_img = None

        self.mode = tk.StringVar(value="top")
        self.top_text = tk.StringVar(value=DEFAULT_TOP_TEXT)
        self.handle = tk.StringVar(value=DEFAULT_HANDLE)
        self.status = tk.StringVar(value="Selecciona video, audio y logo.")

        self.top_rois: list[tuple[int, int, int, int]] = []
        self.bottom_rois: list[tuple[int, int, int, int]] = []
        self.drag_start: tuple[int, int] | None = None
        self.drag_rect_id = None

        self._build_ui()
        self._bind_events()

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(top, text="1. Elegir video MP4", command=self.pick_video).pack(side=tk.LEFT, padx=3)
        ttk.Button(top, text="2. Elegir audio MP3", command=self.pick_audio).pack(side=tk.LEFT, padx=3)
        ttk.Button(top, text="3. Elegir logo", command=self.pick_logo).pack(side=tk.LEFT, padx=3)
        ttk.Button(top, text="Guardar como...", command=self.pick_output).pack(side=tk.LEFT, padx=3)
        ttk.Button(top, text="Exportar MP4", command=self.export_video).pack(side=tk.RIGHT, padx=3)

        paths = ttk.Frame(self.root, padding=(8, 0, 8, 4))
        paths.pack(side=tk.TOP, fill=tk.X)
        self.video_label = ttk.Label(paths, text="Video: —", anchor="w")
        self.video_label.pack(fill=tk.X)
        self.audio_label = ttk.Label(paths, text="Audio: —", anchor="w")
        self.audio_label.pack(fill=tk.X)
        self.logo_label = ttk.Label(paths, text="Logo: —", anchor="w")
        self.logo_label.pack(fill=tk.X)
        self.output_label = ttk.Label(paths, text="Salida: —", anchor="w")
        self.output_label.pack(fill=tk.X)

        opts = ttk.Frame(self.root, padding=(8, 4, 8, 4))
        opts.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(opts, text="Texto superior:").pack(side=tk.LEFT)
        ttk.Entry(opts, textvariable=self.top_text, width=38).pack(side=tk.LEFT, padx=4)
        ttk.Label(opts, text="Marca inferior:").pack(side=tk.LEFT, padx=(12, 0))
        ttk.Entry(opts, textvariable=self.handle, width=20).pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(opts, text="Modo superior", value="top", variable=self.mode).pack(side=tk.LEFT, padx=12)
        ttk.Radiobutton(opts, text="Modo inferior", value="bottom", variable=self.mode).pack(side=tk.LEFT)
        ttk.Button(opts, text="Deshacer zona", command=self.undo_roi).pack(side=tk.LEFT, padx=12)
        ttk.Button(opts, text="Limpiar modo", command=self.clear_mode).pack(side=tk.LEFT, padx=3)
        ttk.Button(opts, text="Limpiar todo", command=self.clear_all).pack(side=tk.LEFT, padx=3)

        help_frame = ttk.Frame(self.root, padding=(8, 0, 8, 4))
        help_frame.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(
            help_frame,
            text="Uso: elige modo superior/inferior, arrastra cajas sobre el video. Puedes marcar varias zonas. El preview NO deforma el video.",
            foreground="#333",
        ).pack(side=tk.LEFT)

        main = ttk.Frame(self.root, padding=8)
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main, bg="#1f1f1f", highlightthickness=1, highlightbackground="#777")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        side = ttk.Frame(main, width=260)
        side.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))
        ttk.Label(side, text="Zonas superiores", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.top_list = tk.Listbox(side, height=10)
        self.top_list.pack(fill=tk.X, pady=(2, 8))
        ttk.Label(side, text="Zonas inferiores", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.bottom_list = tk.Listbox(side, height=10)
        self.bottom_list.pack(fill=tk.X, pady=(2, 8))
        ttk.Button(side, text="Guardar selección JSON", command=self.save_selection).pack(fill=tk.X, pady=2)
        ttk.Button(side, text="Cargar selección JSON", command=self.load_selection).pack(fill=tk.X, pady=2)
        ttk.Separator(side).pack(fill=tk.X, pady=10)
        ttk.Label(side, text="Estado").pack(anchor="w")
        ttk.Label(side, textvariable=self.status, wraplength=240, foreground="#004080").pack(anchor="w", fill=tk.X)

        bottom = ttk.Frame(self.root, padding=(8, 0, 8, 8))
        bottom.pack(side=tk.BOTTOM, fill=tk.X)
        self.progress = ttk.Progressbar(bottom, mode="determinate")
        self.progress.pack(fill=tk.X)

    def _bind_events(self):
        self.canvas.bind("<Configure>", lambda event: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.root.bind("<Control-z>", lambda event: self.undo_roi())
        self.root.bind("<Delete>", lambda event: self.clear_mode())

    def pick_video(self):
        p = filedialog.askopenfilename(
            title="Elegir video MP4",
            filetypes=[("Videos", "*.mp4 *.mov *.mkv *.avi"), ("Todos", "*.*")],
        )
        if not p:
            return
        self.video_path = Path(p)
        self.load_video_first_frame()
        self.video_label.config(text=f"Video: {self.video_path}")
        if self.output_path is None:
            self.output_path = self.video_path.with_name(self.video_path.stem + "_HIDROMARCA_GUI_FINAL.mp4")
            self.output_label.config(text=f"Salida: {self.output_path}")
        self.status.set("Video cargado. Marca zonas en el canvas.")

    def pick_audio(self):
        p = filedialog.askopenfilename(title="Elegir audio MP3", filetypes=[("Audio", "*.mp3 *.wav *.m4a *.aac"), ("Todos", "*.*")])
        if not p:
            return
        self.audio_path = Path(p)
        self.audio_label.config(text=f"Audio: {self.audio_path}")

    def pick_logo(self):
        p = filedialog.askopenfilename(title="Elegir logo", filetypes=[("Imagen", "*.jpg *.jpeg *.png *.webp"), ("Todos", "*.*")])
        if not p:
            return
        self.logo_path = Path(p)
        self.logo_label.config(text=f"Logo: {self.logo_path}")
        self.redraw()

    def pick_output(self):
        p = filedialog.asksaveasfilename(title="Guardar salida MP4", defaultextension=".mp4", filetypes=[("MP4", "*.mp4")])
        if not p:
            return
        self.output_path = Path(p)
        self.output_label.config(text=f"Salida: {self.output_path}")

    def load_video_first_frame(self):
        cap = cv2.VideoCapture(str(self.video_path))
        if not cap.isOpened():
            messagebox.showerror(APP_NAME, "No pude abrir el video.")
            return
        ok, frame = cap.read()
        self.frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.fps if self.fps else 0.0
        cap.release()
        if not ok or frame is None:
            messagebox.showerror(APP_NAME, "No pude leer el primer frame.")
            return
        self.frame_bgr = frame
        self.redraw()

    def canvas_to_frame(self, cx: int, cy: int) -> tuple[int, int] | None:
        if self.frame_bgr is None:
            return None
        x = (cx - self.offset_x) / self.scale
        y = (cy - self.offset_y) / self.scale
        if x < 0 or y < 0 or x >= self.frame_w or y >= self.frame_h:
            return None
        return int(round(x)), int(round(y))

    def frame_to_canvas(self, x: int, y: int) -> tuple[int, int]:
        return int(round(self.offset_x + x * self.scale)), int(round(self.offset_y + y * self.scale))

    def on_mouse_down(self, event):
        p = self.canvas_to_frame(event.x, event.y)
        if p is None:
            return
        self.drag_start = p
        if self.drag_rect_id:
            self.canvas.delete(self.drag_rect_id)
            self.drag_rect_id = None

    def on_mouse_drag(self, event):
        if self.drag_start is None:
            return
        p = self.canvas_to_frame(event.x, event.y)
        if p is None:
            return
        x0, y0 = self.drag_start
        x1, y1 = p
        c0 = self.frame_to_canvas(x0, y0)
        c1 = self.frame_to_canvas(x1, y1)
        if self.drag_rect_id:
            self.canvas.delete(self.drag_rect_id)
        color = "#00ff00" if self.mode.get() == "top" else "#00aaff"
        self.drag_rect_id = self.canvas.create_rectangle(*c0, *c1, outline=color, width=3, dash=(6, 3))

    def on_mouse_up(self, event):
        if self.drag_start is None:
            return
        p = self.canvas_to_frame(event.x, event.y)
        if p is None:
            self.drag_start = None
            return
        x0, y0 = self.drag_start
        x1, y1 = p
        self.drag_start = None
        if self.drag_rect_id:
            self.canvas.delete(self.drag_rect_id)
            self.drag_rect_id = None
        x = min(x0, x1)
        y = min(y0, y1)
        w = abs(x1 - x0)
        h = abs(y1 - y0)
        if w < 5 or h < 5:
            return
        roi = (x, y, w, h)
        if self.mode.get() == "top":
            self.top_rois.append(roi)
        else:
            self.bottom_rois.append(roi)
        self.refresh_lists()
        self.redraw()

    def refresh_lists(self):
        self.top_list.delete(0, tk.END)
        self.bottom_list.delete(0, tk.END)
        for i, r in enumerate(self.top_rois, 1):
            self.top_list.insert(tk.END, f"{i}: x={r[0]} y={r[1]} w={r[2]} h={r[3]}")
        for i, r in enumerate(self.bottom_rois, 1):
            self.bottom_list.insert(tk.END, f"{i}: x={r[0]} y={r[1]} w={r[2]} h={r[3]}")

    def undo_roi(self):
        if self.mode.get() == "top" and self.top_rois:
            self.top_rois.pop()
        elif self.mode.get() == "bottom" and self.bottom_rois:
            self.bottom_rois.pop()
        self.refresh_lists()
        self.redraw()

    def clear_mode(self):
        if self.mode.get() == "top":
            self.top_rois.clear()
        else:
            self.bottom_rois.clear()
        self.refresh_lists()
        self.redraw()

    def clear_all(self):
        self.top_rois.clear()
        self.bottom_rois.clear()
        self.refresh_lists()
        self.redraw()

    def save_selection(self):
        if not self.video_path:
            return
        p = filedialog.asksaveasfilename(title="Guardar selección", defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not p:
            return
        data = {
            "video": str(self.video_path),
            "audio": str(self.audio_path) if self.audio_path else "",
            "logo": str(self.logo_path) if self.logo_path else "",
            "output": str(self.output_path) if self.output_path else "",
            "top_text": self.top_text.get(),
            "handle": self.handle.get(),
            "top_rois": self.top_rois,
            "bottom_rois": self.bottom_rois,
            "frame_w": self.frame_w,
            "frame_h": self.frame_h,
        }
        Path(p).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        self.status.set(f"Selección guardada: {p}")

    def load_selection(self):
        p = filedialog.askopenfilename(title="Cargar selección", filetypes=[("JSON", "*.json")])
        if not p:
            return
        data = json.loads(Path(p).read_text(encoding="utf-8"))
        self.top_text.set(data.get("top_text", DEFAULT_TOP_TEXT))
        self.handle.set(data.get("handle", DEFAULT_HANDLE))
        self.top_rois = [tuple(map(int, r)) for r in data.get("top_rois", [])]
        self.bottom_rois = [tuple(map(int, r)) for r in data.get("bottom_rois", [])]
        self.refresh_lists()
        self.redraw()
        self.status.set(f"Selección cargada: {p}")

    def redraw(self):
        self.canvas.delete("all")
        if self.frame_bgr is None:
            self.canvas.create_text(30, 30, text="Elige un video para empezar", anchor="nw", fill="white", font=("Segoe UI", 16))
            return
        canvas_w = max(1, self.canvas.winfo_width())
        canvas_h = max(1, self.canvas.winfo_height())
        self.scale = min(canvas_w / self.frame_w, canvas_h / self.frame_h)
        draw_w = int(self.frame_w * self.scale)
        draw_h = int(self.frame_h * self.scale)
        self.offset_x = (canvas_w - draw_w) // 2
        self.offset_y = (canvas_h - draw_h) // 2

        preview = self.make_preview_frame(self.frame_bgr.copy(), for_canvas=True)
        rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb).resize((draw_w, draw_h), Image.Resampling.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(pil)
        self.canvas.create_image(self.offset_x, self.offset_y, image=self.tk_img, anchor="nw")

        self.draw_roi_outlines()

    def draw_roi_outlines(self):
        for i, r in enumerate(self.top_rois, 1):
            x, y, w, h = r
            x0, y0 = self.frame_to_canvas(x, y)
            x1, y1 = self.frame_to_canvas(x + w, y + h)
            self.canvas.create_rectangle(x0, y0, x1, y1, outline="#00ff00", width=2)
            self.canvas.create_text(x0 + 4, y0 + 4, text=f"S{i}", anchor="nw", fill="#00ff00", font=("Segoe UI", 11, "bold"))
        for i, r in enumerate(self.bottom_rois, 1):
            x, y, w, h = r
            x0, y0 = self.frame_to_canvas(x, y)
            x1, y1 = self.frame_to_canvas(x + w, y + h)
            self.canvas.create_rectangle(x0, y0, x1, y1, outline="#00aaff", width=2)
            self.canvas.create_text(x0 + 4, y0 + 4, text=f"I{i}", anchor="nw", fill="#00aaff", font=("Segoe UI", 11, "bold"))

    @staticmethod
    def union_rois(rois: list[tuple[int, int, int, int]]) -> tuple[int, int, int, int]:
        x = min(r[0] for r in rois)
        y = min(r[1] for r in rois)
        x2 = max(r[0] + r[2] for r in rois)
        y2 = max(r[1] + r[3] for r in rois)
        return x, y, x2 - x, y2 - y

    def draw_text_centered(self, img: np.ndarray, text: str, roi: tuple[int, int, int, int]):
        x, y, w, h = roi
        font = cv2.FONT_HERSHEY_SIMPLEX
        thickness = max(1, int(round(h / 32)))
        scale = 1.0
        for candidate in np.linspace(2.4, 0.25, 120):
            (tw, th), baseline = cv2.getTextSize(text, font, float(candidate), thickness)
            if tw <= int(w * 0.94) and th <= int(h * 0.62):
                scale = float(candidate)
                break
        (tw, th), baseline = cv2.getTextSize(text, font, scale, thickness)
        tx = x + (w - tw) // 2
        ty = y + (h + th) // 2 - baseline
        cv2.putText(img, text, (tx, ty), font, scale, (255, 255, 255), thickness + 3, cv2.LINE_AA)
        cv2.putText(img, text, (tx, ty), font, scale, (0, 0, 0), thickness, cv2.LINE_AA)

    def draw_logo_handle(self, img: np.ndarray, logo_bgr: np.ndarray, roi: tuple[int, int, int, int]):
        x, y, w, h = roi
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0), -1)
        margin = max(3, int(round(h * 0.10)))
        logo_size = max(12, min(h - margin * 2, int(w * 0.23)))
        logo = cv2.resize(logo_bgr, (logo_size, logo_size), interpolation=cv2.INTER_AREA)
        lx = x + margin
        ly = y + (h - logo_size) // 2
        img[ly:ly + logo_size, lx:lx + logo_size] = logo
        text_x = lx + logo_size + margin
        available_w = max(20, x + w - text_x - margin)
        font = cv2.FONT_HERSHEY_SIMPLEX
        thickness = max(1, int(round(h / 36)))
        scale = 1.0
        for candidate in np.linspace(1.9, 0.2, 120):
            (tw, th), baseline = cv2.getTextSize(self.handle.get(), font, float(candidate), thickness)
            if tw <= available_w and th <= int(h * 0.72):
                scale = float(candidate)
                break
        (tw, th), baseline = cv2.getTextSize(self.handle.get(), font, scale, thickness)
        ty = y + (h + th) // 2 - baseline
        cv2.putText(img, self.handle.get(), (text_x, ty), font, scale, (0, 0, 0), thickness + 4, cv2.LINE_AA)
        cv2.putText(img, self.handle.get(), (text_x, ty), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)

    def make_preview_frame(self, frame: np.ndarray, for_canvas=False) -> np.ndarray:
        out = frame.copy()
        if self.top_rois:
            for x, y, w, h in self.top_rois:
                cv2.rectangle(out, (x, y), (x + w, y + h), (245, 245, 245), -1)
            union = self.union_rois(self.top_rois)
            x, y, w, h = union
            cv2.rectangle(out, (x, y), (x + w, y + h), (0, 0, 0), max(1, int(h / 45)))
            self.draw_text_centered(out, self.top_text.get(), union)
        if self.bottom_rois:
            logo = self.load_logo_bgr()
            if logo is not None:
                for x, y, w, h in self.bottom_rois:
                    cv2.rectangle(out, (x, y), (x + w, y + h), (0, 0, 0), -1)
                self.draw_logo_handle(out, logo, self.union_rois(self.bottom_rois))
        return out

    def load_logo_bgr(self):
        if not self.logo_path:
            return None
        logo = cv2.imread(str(self.logo_path), cv2.IMREAD_COLOR)
        return logo

    def validate_ready(self):
        if self.video_path is None or self.frame_bgr is None:
            raise RuntimeError("Falta elegir video.")
        if self.audio_path is None:
            raise RuntimeError("Falta elegir audio.")
        if self.logo_path is None:
            raise RuntimeError("Falta elegir logo.")
        if self.output_path is None:
            raise RuntimeError("Falta elegir salida.")
        if not self.top_rois:
            raise RuntimeError("Falta marcar al menos una zona superior.")
        if not self.bottom_rois:
            raise RuntimeError("Falta marcar al menos una zona inferior.")
        ffmpeg = shutil.which("ffmpeg") or r"C:\ffmpeg\bin\ffmpeg.exe"
        if not Path(ffmpeg).exists() and not shutil.which("ffmpeg"):
            raise RuntimeError("No encontré FFmpeg en PATH ni en C:\\ffmpeg\\bin.")
        return ffmpeg

    def export_video(self):
        try:
            ffmpeg = self.validate_ready()
        except Exception as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        self.status.set("Renderizando frames...")
        self.root.update_idletasks()
        try:
            temp = self.output_path.with_name(self.output_path.stem + "_temp_silent.mp4")
            if temp.exists():
                temp.unlink()
            if self.output_path.exists():
                self.output_path.unlink()
            self.render_silent(temp)
            self.mux_audio(ffmpeg, temp)
            try:
                temp.unlink()
            except Exception:
                pass
            self.status.set(f"Listo: {self.output_path}")
            messagebox.showinfo(APP_NAME, f"Listo:\n{self.output_path}")
        except Exception as exc:
            self.status.set("Error")
            messagebox.showerror(APP_NAME, str(exc))

    def render_silent(self, temp_path: Path):
        cap = cv2.VideoCapture(str(self.video_path))
        if not cap.isOpened():
            raise RuntimeError("No pude abrir el video para exportar.")
        writer = cv2.VideoWriter(str(temp_path), cv2.VideoWriter_fourcc(*"mp4v"), self.fps, (self.frame_w, self.frame_h))
        if not writer.isOpened():
            cap.release()
            raise RuntimeError("No pude crear video temporal.")
        self.progress.config(maximum=max(1, self.total_frames), value=0)
        idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            out = self.make_preview_frame(frame)
            writer.write(out)
            idx += 1
            if idx % 10 == 0:
                self.progress.config(value=idx)
                self.status.set(f"Renderizando frames {idx}/{self.total_frames}")
                self.root.update_idletasks()
        cap.release()
        writer.release()
        self.progress.config(value=self.total_frames)
        if not temp_path.exists() or temp_path.stat().st_size == 0:
            raise RuntimeError("El temporal de video quedó vacío.")

    def mux_audio(self, ffmpeg: str, temp_path: Path):
        self.status.set("Combinando audio con FFmpeg...")
        self.root.update_idletasks()
        cmd = [
            ffmpeg,
            "-y",
            "-i", str(temp_path),
            "-i", str(self.audio_path),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            "-af", "apad",
            "-shortest",
            "-t", f"{self.duration:.3f}",
            "-movflags", "+faststart",
            str(self.output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError("FFmpeg falló:\n" + result.stderr[-2000:])
        if not self.output_path.exists() or self.output_path.stat().st_size == 0:
            raise RuntimeError("El archivo final no se generó.")


def main():
    root = tk.Tk()
    app = HidroMarcaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
