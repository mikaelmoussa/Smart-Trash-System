"""YOLOv8 waste detection + Smart Recycle Bin GUI (Tkinter) + Arduino COM4.

Requirements (no extra installs beyond these):
- ultralytics
- opencv-python
- pyserial

What this script does:
- Grabs a frame from ESP32 MJPEG stream: http://192.168.0.250:81/stream
- Runs YOLOv8 on the frame using best_model.pt
- Displays:
  - LEFT: live feed frame with bounding boxes
  - RIGHT: reference image (purely for human visual comparison) from test_images/
- Sends commands to Arduino over COM4 at 9600 baud:
  - ITEM:PLASTIC | ITEM:PAPER | ITEM:METAL | ITEM:GLASS
- Non-blocking serial listener thread:
  - Parses DONE:/REJECTED: responses and updates GUI/log/bin panel
  - Parses bin status line like: METAL:OK(12.5cm) PLASTIC:FULL(2.1cm) ...
- Bin FULL logic:
  - If a bin is FULL, DO NOT send ITEM command and log: "<time> <BIN> bin is FULL - item rejected"
- GUI controls:
  - START / STOP / QUIT
  - Capture Now
  - Check Bins (sends CHECKBINS)

Note:
- Reference images are ONLY displayed; they are NOT used for detection.
"""

from __future__ import annotations

import io
import re
import threading
import time
import urllib.request
import urllib.error

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from ultralytics import YOLO


# =====================
# Configuration
# =====================

ESP32_STREAM_URL = "http://10.114.208.123:81/stream"

SERIAL_PORT = "COM4"
SERIAL_BAUD = 9600
SERIAL_TIMEOUT = 2

CONF_THRESHOLD = 0.20
DETECTION_INTERVAL_SEC = 10


# Order matters for GUI/bin panel.
BIN_ORDER = ["METAL", "PLASTIC", "GLASS", "PAPER"]

# VALID labels we send to Arduino.
VALID_LABELS = ["PLASTIC", "METAL", "PAPER", "GLASS"]


# YOLO classes (your model names are normalized through normalize_label())
CLASS_NAMES = ["paper", "plastic", "metal", "glass"]

# Reference images (purely display)
# =====================
# Helpers
# =====================



def resolve_project_root() -> Path:
    """Return repo folder containing best_model.pt and test_images/."""
    this_file = Path(__file__).resolve()

    # Common layouts: either directly in repo root, or nested.
    candidates = [
        this_file.parent,
        this_file.parent / "YOLO-Waste-Detection-main",
        Path.cwd(),
    ]

    for c in candidates:
        if (c / "best_model.pt").exists():
            return c


    # Fallback: parent
    return this_file.parent


def normalize_label(label: str) -> str:
    ll = str(label).strip().lower()
    for canonical in CLASS_NAMES:
        if canonical in ll:
            return canonical
    # If it doesn't match, return the raw lower-case
    return ll


def item_to_classname(item: str) -> Optional[str]:
    item_u = str(item).strip().upper()
    if item_u in BIN_ORDER:
        return item_u
    # allow e.g. 'paper'
    low = item_u.lower()
    if "paper" in low:
        return "PAPER"
    if "plastic" in low:
        return "PLASTIC"
    if "metal" in low:
        return "METAL"
    if "glass" in low:
        return "GLASS"
    return None


def now_ts() -> str:
    return time.strftime("%H:%M:%S")


def cv2_to_jpeg_bytes(bgr_img, quality: int = 90) -> bytes:
    rgb = bgr_img[:, :, ::-1]
    pil_img = None
    try:
        from PIL import Image

        pil_img = Image.fromarray(rgb)
        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG", quality=quality)
        return buf.getvalue()
    except Exception:
        # If PIL isn't available, return nothing.
        return b""


def grab_frame_opencv(url):
    try:
        stream = urllib.request.urlopen(url, timeout=10)
        bytes_buffer = b""
        frames_found = 0
        last_good_frame = None

        while frames_found < 6:  # read 6 frames, use the last one
            chunk = stream.read(4096)
            if not chunk:
                break
            bytes_buffer += chunk

            start = bytes_buffer.find(b'\xff\xd8\xff')
            end = bytes_buffer.find(b'\xff\xd9')

            if start != -1 and end != -1 and end > start:
                jpg = bytes_buffer[start:end+2]
                bytes_buffer = bytes_buffer[end+2:]

                frame = cv2.imdecode(
                    np.frombuffer(jpg, dtype=np.uint8),
                    cv2.IMREAD_COLOR
                )

                if frame is not None and frame.shape[0] > 0:
                    frames_found += 1
                    last_good_frame = frame  # keep updating

        return last_good_frame  # return the last brightest frame

    except Exception as e:
        print(f"Stream error: {e}")
        return None




def grab_frame_mjpeg_urllib(source: str, fallback_single_url: Optional[str] = None, timeout: float = 5.0) -> Optional[object]:
    """Grab a single BGR frame from an MJPEG stream using urllib+imdecode.


    OpenCV VideoCapture sometimes fails to decode ESP32-CAM MJPEG directly.
    Returns None on failure.
    """
    import urllib.request

    try:
        stream = urllib.request.urlopen(source, timeout=timeout)
        bytes_buffer = b""

        # Keep reading until we can extract a complete JPEG frame.
        while True:
            chunk = stream.read(1024)
            if not chunk:
                break
            bytes_buffer += chunk

            a = bytes_buffer.find(b"\xff\xd8")  # JPEG SOI
            b = bytes_buffer.find(b"\xff\xd9")  # JPEG EOI

            if a != -1 and b != -1 and b > a:
                jpg = bytes_buffer[a : b + 2]
                bytes_buffer = bytes_buffer[b + 2 :]
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    return frame
    except Exception:
        pass

    # Fallback to a single-frame JPEG (often supported by ESP32-CAM)
    if fallback_single_url:
        try:
            frame_bytes = urllib.request.urlopen(fallback_single_url, timeout=timeout).read()
            frame = cv2.imdecode(np.frombuffer(frame_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
            return frame
        except Exception:
            return None

    return None



def draw_reference_placeholder_text(w: int, h: int, text: str) -> "object":
    """Create a grey placeholder PIL-like image via OpenCV (BGR)."""
    import numpy as np

    img = np.full((h, w, 3), 200, dtype=np.uint8)
    cv2.putText(
        img,
        text,
        (10, h // 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (60, 60, 60),
        2,
        cv2.LINE_AA,
    )
    return img


# =====================
# Serial + GUI state model
# =====================


@dataclass
class BinFill:
    state: str = "UNKNOWN"  # OK | FULL | UNKNOWN
    detail: str = ""  # e.g. "12.5cm"


class SerialManager:
    def __init__(self, logger_fn, on_bins_line_fn, on_item_resp_fn):
        self._logger_fn = logger_fn
        self._on_bins_line_fn = on_bins_line_fn
        self._on_item_resp_fn = on_item_resp_fn

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._ser = None

        # Arduino expects: ITEM:PLASTIC (newline ok)
        # It replies: DONE:PLASTIC, REJECTED:PLASTIC bin is full!, or
        # bin status line containing METAL:OK(12.5cm) etc.
        self._thread = None

    def start(self):
        try:
            import serial  # type: ignore

            # MUST match Arduino: pythonser = serial.Serial('COM4', 9600, timeout=2)
            self._ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=SERIAL_TIMEOUT)
        except Exception as e:
            self._logger_fn(f"[Serial] Could not open {SERIAL_PORT}: {e}")
            self._ser = None
            return

        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        with self._lock:
            try:
                if self._ser is not None:
                    self._ser.close()
            except Exception:
                pass

    def _read_loop(self):
        # Non-blocking for GUI: this thread blocks on serial.read
        while not self._stop_event.is_set():
            with self._lock:
                ser = self._ser

            if ser is None:
                time.sleep(0.2)
                continue

            try:
                line = ser.readline()
                if not line:
                    continue

                try:
                    msg = line.decode("utf-8", errors="ignore").strip()
                except Exception:
                    continue

                if not msg:
                    continue

                self._logger_fn(f"Arduino: {msg}")

                # Parse DONE/REJECTED
                m_done = re.match(r"^DONE\s*:\s*([A-Za-z]+)\s*$", msg, re.IGNORECASE)
                m_rej = re.match(r"^REJECTED\s*:\s*([A-Za-z]+)\s*(.*)$", msg, re.IGNORECASE)

                if m_done:
                    cls = item_to_classname(m_done.group(1))
                    if cls:
                        self._on_item_resp_fn("DONE", cls, msg)
                    continue

                if m_rej:
                    cls = item_to_classname(m_rej.group(1))
                    if cls:
                        self._on_item_resp_fn("REJECTED", cls, msg)
                    continue

                # Parse bins status line: METAL:OK(12.5cm) PLASTIC:FULL(2.1cm) ...
                # We'll accept both OK/FULL and ignore unknown.
                if any(b + ":" in msg.upper() for b in BIN_ORDER):
                    self._on_bins_line_fn(msg)

            except Exception:
                # If serial read fails, do a brief wait.
                time.sleep(0.2)

    def send(self, text: str) -> None:
        with self._lock:
            ser = self._ser
            if ser is None:
                return

            try:
                ser.write((text.strip() + "\n").encode("utf-8"))
                ser.flush()
            except Exception:
                # silent fail
                pass


# =====================
# GUI application
# =====================


class WasteDetectorApp:
    def __init__(self, root):
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.root = root
        self.root.title("Smart Recycle Bin - YOLO Waste Detection")

        self.project_dir = resolve_project_root()
        model_path = self.project_dir / "best_model.pt"
        if not model_path.exists():
            raise FileNotFoundError(f"best_model.pt not found at: {model_path}")



        # YOLO model
        self.model = YOLO(str(model_path))

        # Detection thread control
        self._stop_event = threading.Event()
        self._run_event = threading.Event()
        self._capture_now_event = threading.Event()

        # Bin status
        self.bin_status: dict[str, BinFill] = {b: BinFill() for b in BIN_ORDER}

        # GUI TK images refs
        self._tk_live_img = None
        self._tk_ref_img = None

        # Log storage
        self._log_items = []

        # Serial test control
        self._serial_test_lock = threading.Lock()

        # Build GUI
        self._build_ui()

        # Serial manager with callbacks
        self.serial = SerialManager(
            logger_fn=self._log_line,
            on_bins_line_fn=self._handle_bins_line_from_arduino,
            on_item_resp_fn=self._handle_item_response,
        )
        self.serial.start()

        # Start detection loop thread
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

        # Set COM indicator initial state (unknown until test)
        self._set_com_indicator(False)

        self.root.protocol("WM_DELETE_WINDOW", self.quit)

    def _build_ui(self):
        tk = self.tk
        ttk = self.ttk

        container = tk.Frame(self.root, padx=10, pady=10)
        container.pack(fill="both", expand=True)

        # Top: buttons
        btn_frame = tk.Frame(container)
        btn_frame.pack(fill="x")

        tk.Button(btn_frame, text="START", width=10, command=self.start).pack(side="left", padx=(0, 6))
        tk.Button(btn_frame, text="STOP", width=10, command=self.stop).pack(side="left", padx=(0, 6))
        tk.Button(btn_frame, text="Capture Now", width=12, command=self.capture_now).pack(side="left", padx=(0, 6))
        tk.Button(btn_frame, text="Check Bins", width=12, command=self.check_bins).pack(side="left", padx=(0, 6))
        tk.Button(btn_frame, text="QUIT", width=10, command=self.quit).pack(side="left")


        # Middle: images left/right
        mid_frame = tk.Frame(container)
        mid_frame.pack(fill="both", expand=True, pady=(10, 10))

        # Live feed panel (full width)
        live_frame = tk.LabelFrame(mid_frame, text="Live Feed")
        live_frame.pack(side="left", fill="both", expand=True, padx=(0, 0))

        self.live_label = tk.Label(live_frame, bg="#111")
        self.live_label.pack(fill="both", expand=True)


        # Right sidebar: status panels
        sidebar = tk.Frame(mid_frame)
        sidebar.pack(side="right", fill="y", padx=(6, 0))

        # Detection + Arduino response panel
        self.status_var = tk.StringVar(value="Status: Stopped")
        self.last_var = tk.StringVar(value="Last detected: -")

        tk.Label(sidebar, textvariable=self.status_var, font=("Segoe UI", 12)).pack(pady=(0, 4))
        tk.Label(sidebar, textvariable=self.last_var, font=("Segoe UI", 11)).pack(pady=(0, 10))

        self.arduino_resp_var = tk.StringVar(value="Arduino: -")
        self.arduino_resp_label = tk.Label(sidebar, textvariable=self.arduino_resp_var, font=("Segoe UI", 12), fg="#444")
        self.arduino_resp_label.pack(pady=(0, 10))

        # Bin status panel
        bin_frame = tk.LabelFrame(sidebar, text="Bin Status")
        bin_frame.pack(fill="x", pady=(0, 10))

        self.bin_vars: dict[str, tk.StringVar] = {}
        self.bin_labels: dict[str, tk.Label] = {}

        for b in BIN_ORDER:
            v = tk.StringVar(value=f"{b}:   UNKNOWN")
            self.bin_vars[b] = v
            lbl = tk.Label(bin_frame, textvariable=v, font=("Consolas", 11), anchor="w")
            lbl.pack(fill="x", padx=6)
            self.bin_labels[b] = lbl

        # Source label
        self.source_var = tk.StringVar(value=f"ESP32: {ESP32_STREAM_URL}")
        tk.Label(
            sidebar,
            textvariable=self.source_var,
            font=("Segoe UI", 8),
            fg="#666",
            wraplength=260,
            justify="left",
        ).pack(pady=(0, 8))

        # Log box
        log_frame = tk.LabelFrame(container, text="Log")
        log_frame.pack(fill="both", expand=False, pady=(0, 0))

        self.log_list = tk.Listbox(log_frame, height=10)
        self.log_list.pack(fill="both", expand=True, padx=6, pady=6)

        # Initialize live placeholder only
        self._set_live_placeholder()


    def _set_com_indicator(self, is_ok: bool) -> None:
        color = "#007a00" if is_ok else "#c00000"
        try:
            self.com_indicator_canvas.itemconfig(self.com_indicator_circle, fill=color, outline=color)
            # also update label text color briefly
            self.com_indicator_label.configure(fg=color)
        except Exception:
            pass


    def _log_line(self, text: str) -> None:
        # Ensure timestamp formatting
        line = f"[{now_ts()}] {text}"
        self._log_items.append(line)

        def _update():
            self.log_list.insert("end", line)
            self.log_list.yview_moveto(1.0)

        self.root.after(0, _update)

    def _set_live_placeholder(self):
        import numpy as np
        placeholder = np.full((360, 480, 3), 40, dtype=np.uint8)
        cv2.putText(
            placeholder,
            "Waiting for stream...",
            (20, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (220, 220, 220),
            2,
            cv2.LINE_AA,
        )

        from PIL import Image, ImageTk

        rgb = placeholder[:, :, ::-1]
        img = Image.fromarray(rgb)
        img = img.resize((480, 360))
        tk_img = ImageTk.PhotoImage(img)
        self._tk_live_img = tk_img
        self.live_label.configure(image=tk_img)



    def start(self):
        self.status_var.set("Status: Running...")
        self._run_event.set()

    def stop(self):
        self.status_var.set("Status: Stopped")
        self._run_event.clear()

    def capture_now(self):
        self._capture_now_event.set()

    def quit(self):
        self.status_var.set("Status: Stopped")
        self._stop_event.set()
        self._run_event.clear()
        self._capture_now_event.set()
        try:
            self.serial.stop()
        except Exception:
            pass
        self.root.after(150, self.root.destroy)

    def check_bins(self):
        self._log_line("Sent: CHECKBINS")
        self.serial.send("CHECKBINS")

    def _update_bin_panel(self):
        def _do():
            for b in BIN_ORDER:
                st = self.bin_status[b]
                if st.state == "FULL":
                    fg = "#c00000"
                elif st.state == "OK":
                    fg = "#007a00"
                else:
                    fg = "#444"

                if st.state in ("OK", "FULL") and st.detail:
                    txt = f"{b}:   {st.state:<4} ({st.detail})"
                elif st.state in ("OK", "FULL"):
                    txt = f"{b}:   {st.state}"
                else:
                    txt = f"{b}:   UNKNOWN"

                self.bin_vars[b].set(txt)
                self.bin_labels[b].configure(fg=fg)

        self.root.after(0, _do)

    def _handle_bins_line_from_arduino(self, msg: str):
        # Example:
        # METAL:OK(12.5cm) PLASTIC:OK(8.3cm) GLASS:FULL(2.1cm) PAPER:OK(15.2cm)
        up = msg.upper()
        for b in BIN_ORDER:
            # capture like METAL:OK(12.5CM)
            pat = rf"{b}\s*:\s*(OK|FULL)\s*\(([^\)]*)\)"
            m = re.search(pat, up)
            if m:
                state = m.group(1)
                detail = m.group(2).strip()
                self.bin_status[b] = BinFill(state=state, detail=detail)

        self._update_bin_panel()
        self._log_line("Bin status updated")

    def _handle_item_response(self, kind: str, cls: str, raw_msg: str):
        # Update colored response label
        if kind == "DONE":
            self.arduino_resp_var.set(f"✅ Sorted: {cls}")
            self.arduino_resp_label.configure(fg="#007a00")
        else:
            # REJECTED
            # Ensure message ends with original
            self.arduino_resp_var.set(f"❌ Rejected: {raw_msg.split(':', 1)[1].strip() if ':' in raw_msg else cls}")
            self.arduino_resp_label.configure(fg="#c00000")



    def _set_live_image(self, bgr_img):
        from PIL import Image, ImageTk

        # Resize to panel (no letterboxing)
        box_w = self.live_label.winfo_width() or 640
        box_h = self.live_label.winfo_height() or 480

        frame_resized = cv2.resize(bgr_img, (box_w, box_h), interpolation=cv2.INTER_LINEAR)

        # Convert to RGB PIL
        rgb = frame_resized[:, :, ::-1]
        pil = Image.fromarray(rgb)

        tk_img = ImageTk.PhotoImage(pil)
        self._tk_live_img = tk_img
        self.live_label.configure(image=tk_img)


    def _send_item_if_not_full(self, cls_u: str, conf: float):
        cls_u = str(cls_u).upper().strip()

        # Enforce valid labels only.
        if cls_u not in VALID_LABELS:
            self._log_line(f"[DEBUG] Unknown label not sent: {cls_u}")
            return False

        # Enforce FULL bin rule.
        st = self.bin_status.get(cls_u, BinFill())

        if st.state == "FULL":
            self._log_line(f"{cls_u} bin is FULL — item rejected")
            return False


        text = f"ITEM:{cls_u}"
        self._log_line(f"Sent: {text}")
        self.serial.send(text)
        return True

    def test_serial(self):
        # Background thread so GUI does not freeze
        if not self._serial_test_lock.acquire(blocking=False):
            self._log_line("⚠️ Serial test already running")
            return

        t = threading.Thread(target=self._serial_test_worker, daemon=True)
        t.start()

    def _serial_test_worker(self):
        try:
            import serial  # type: ignore
            import serial.tools.list_ports

            self._log_line(f"Testing {SERIAL_PORT}...")

            # List available ports
            ports = serial.tools.list_ports.comports()
            port_lines = []
            for p in ports:
                desc = p.description or ""
                port_lines.append(f"{p.device} ({desc})".strip())

            if port_lines:
                self._log_line("Available ports: " + ", ".join(port_lines))
            else:
                self._log_line("Available ports: (none)")

            # Try open SERIAL_PORT
            try:
                self._log_line(f"Trying to open {SERIAL_PORT} at {SERIAL_BAUD} baud...")
                ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=2)
            except serial.SerialException as e:
                self._log_line(f"❌ {SERIAL_PORT} error: {e}")
                self._set_com_indicator(False)


                if port_lines:
                    self._log_line("⚠️ Check Arduino is connected and COM port is correct")
                else:
                    self._log_line("⚠️ No serial ports detected")
                return

            try:
                self._log_line(f"✅ {SERIAL_PORT} opened successfully")
                ser.write(b"CHECKBINS\n")
                self._log_line("✅ Sent: CHECKBINS")

                time.sleep(2)

                response = None
                if ser.in_waiting:
                    try:
                        response = ser.readline().decode().strip()
                    except Exception:
                        response = None

                if response:
                    self._log_line(f"✅ Arduino responded: {response}")
                    # Update bin status panel using same parser
                    self._handle_bins_line_from_arduino(response)
                    self._set_com_indicator(True)
                    self._log_line("✅ Serial connection working")
                else:
                    self._log_line("❌ No response from Arduino")
                    self._set_com_indicator(False)
                    self._log_line("⚠️ Arduino may be unresponsive")
            finally:
                try:
                    ser.close()
                    self._log_line(f"✅ {SERIAL_PORT} closed cleanly")
                except Exception:
                    pass

        finally:
            try:
                self._serial_test_lock.release()
            except Exception:
                pass

    def _loop(self):
        # Detection loop thread: never blocks GUI.
        interval_sec = DETECTION_INTERVAL_SEC

        while not self._stop_event.is_set():
            # Wait until running or capture requested
            if not self._run_event.is_set() and not self._capture_now_event.is_set():
                time.sleep(0.1)
                continue

            capture_now = self._capture_now_event.is_set()
            if capture_now:
                self._capture_now_event.clear()

            # Grab frame (retry silently every interval if stream unreachable)
            frame = None
            while not self._stop_event.is_set():
                frame = grab_frame_opencv(ESP32_STREAM_URL)

                if frame is not None:
                    break

                # stream not reachable: silent retry
                # If user STOPs, exit wait
                if not self._run_event.is_set() and not self._capture_now_event.is_set():
                    break
                time.sleep(interval_sec)

            if frame is None or self._stop_event.is_set():
                continue

            # Run YOLO
            try:
                # NO preprocessing — use raw frame directly
                # frame = frame  (no changes)

                # ONLY send items if best confidence > 0.5

                # Capture 1 frame only and choose the best-confidence detection from this single frame.

                if frame is None:
                    self._log_line("ESP32 not reachable, retrying...")
                    continue

                results = self.model(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), conf=CONF_THRESHOLD, verbose=False)

                best_label_u = None
                best_conf = 0.0
                best_r0 = None

                names = getattr(self.model, "names", {}) or {}

                # get best detection from this single frame
                for r in results:
                    for box in r.boxes:
                        conf = float(box.conf[0])
                        cls_id = int(box.cls[0])
                        name = None
                        if isinstance(names, dict):
                            name = names.get(cls_id, names.get(str(cls_id)))
                        if name is None:
                            name = CLASS_NAMES[cls_id] if 0 <= cls_id < len(CLASS_NAMES) else str(cls_id)

                        label = normalize_label(name)
                        cls_u = item_to_classname(label)
                        if cls_u is None:
                            continue

                        if conf > best_conf and cls_u in VALID_LABELS:
                            best_conf = conf
                            best_label_u = cls_u
                            best_r0 = r

                # Update GUI live feed with bounding boxes
                annotated = frame
                if best_r0 is not None:
                    try:
                        annotated = best_r0.plot()
                    except Exception:
                        annotated = frame
                self._set_live_image(annotated)

                # Keep original GUI behavior
                if best_label_u is None:
                    self.last_var.set("Last detected: -")
                    self._log_line("Detected: none")

                else:
                    self.last_var.set(f"Last detected: {best_label_u} ({best_conf:.2f})")
                    self._log_line(f"Detected: {best_label_u} ({best_conf:.2f})")

                    if best_conf >= CONF_THRESHOLD:
                        self._send_item_if_not_full(best_label_u, best_conf)






            except Exception as e:
                # Keep GUI alive
                self._log_line(f"[WARNING] Detection cycle error: {e}")

            # Interval control
            if self._stop_event.is_set():
                break
            if not capture_now:
                for _ in range(int(interval_sec * 10)):
                    if self._stop_event.is_set() or (not self._run_event.is_set() and not self._capture_now_event.is_set()):
                        break
                    time.sleep(0.1)


def main():
    import tkinter as tk

    root = tk.Tk()
    _ = WasteDetectorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

