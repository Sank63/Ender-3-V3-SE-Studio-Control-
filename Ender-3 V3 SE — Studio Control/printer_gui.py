import sys
import time
import re
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import serial
import serial.tools.list_ports

DEFAULT_BAUDRATE = 115200

THEMES = {
    "dark": {
        "bg": "#131314",
        "surface": "#1e1f20",
        "surface_border": "#3c4043",
        "card": "#282a2c",
        "fg": "#e3e3e3",
        "fg_muted": "#8e918f",
        "accent": "#a8c7fa",
        "accent_bg": "#0842a0",
        "accent_hover": "#0b57d0",
        "btn_normal": "#37393b",
        "btn_normal_hover": "#4a4d51",
        "btn_fg": "#e3e3e3",
        "btn_disabled": "#222426",
        "btn_disabled_fg": "#55585c",
        "btn_start": "#1e8e3e",
        "btn_start_hover": "#28a745",
        "btn_start_fg": "#ffffff",
        "btn_pause": "#e37400",
        "btn_pause_hover": "#f57c00",
        "btn_pause_fg": "#ffffff",
        "btn_stop": "#d93025",
        "btn_stop_hover": "#ea4335",
        "btn_stop_fg": "#ffffff",
        "badge_connected": "#81c995",
        "badge_disconnected": "#f28b82",
        "telemetry": "#8ab4f8",
    },
    "light": {
        "bg": "#f8fafd",
        "surface": "#ffffff",
        "surface_border": "#e1e3e1",
        "card": "#f0f4f9",
        "fg": "#1f1f1f",
        "fg_muted": "#5f6368",
        "accent": "#0b57d0",
        "accent_bg": "#d3e3fd",
        "accent_hover": "#c2d7fc",
        "btn_normal": "#e8eaed",
        "btn_normal_hover": "#dadce0",
        "btn_fg": "#1f1f1f",
        "btn_disabled": "#e4e7eb",
        "btn_disabled_fg": "#9aa0a6",
        "btn_start": "#1e8e3e",
        "btn_start_hover": "#187a33",
        "btn_start_fg": "#ffffff",
        "btn_pause": "#e37400",
        "btn_pause_hover": "#c76400",
        "btn_pause_fg": "#ffffff",
        "btn_stop": "#d93025",
        "btn_stop_hover": "#b8241a",
        "btn_stop_fg": "#ffffff",
        "badge_connected": "#1e8e3e",
        "badge_disconnected": "#d93025",
        "telemetry": "#0b57d0",
    }
}

class RoundedButton(tk.Canvas):
    """Виджет кнопки с закругленными углами на базе холста Canvas."""
    def __init__(self, parent, text="", command=None, radius=10,
                 bg="#37393b", fg="#ffffff", hover_bg=None, parent_bg=None,
                 disabled_bg="#222426", disabled_fg="#55585c",
                 font=("Segoe UI", 9, "bold"), width=None, height=36,
                 state="normal", cursor="hand2", **kwargs):

        self.parent = parent
        self.text = text
        self.command = command
        self.radius = radius
        self.bg_color = bg
        self.fg_color = fg
        self.hover_bg = hover_bg
        self.disabled_bg = disabled_bg
        self.disabled_fg = disabled_fg
        self.parent_bg = parent_bg or "#131314"
        self.font = font
        self.btn_width = width
        self.btn_height = height
        self.state = state
        self.cursor_style = cursor

        super().__init__(
            parent,
            width=self.btn_width or 100,
            height=self.btn_height,
            bg=self.parent_bg,
            highlightthickness=0,
            bd=0,
            cursor=self.cursor_style if self.state == "normal" else "arrow",
            **kwargs
        )

        self.poly_id = None
        self.text_id = None
        self.is_hovered = False

        self.bind("<Configure>", self._on_resize)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

        self._draw()

    def _adjust_color(self, hex_color, amount):
        if not hex_color or not hex_color.startswith("#") or len(hex_color) != 7:
            return hex_color
        try:
            r = max(0, min(255, int(hex_color[1:3], 16) + amount))
            g = max(0, min(255, int(hex_color[3:5], 16) + amount))
            b = max(0, min(255, int(hex_color[5:7], 16) + amount))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()

        if w <= 1:
            w = self.btn_width or 100
        if h <= 1:
            h = self.btn_height

        r = min(self.radius, w // 2, h // 2)
        x1, y1 = 2, 2
        x2, y2 = w - 2, h - 2

        points = [
            x1 + r, y1,
            x1 + r, y1,
            x2 - r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1 + r,
            x1, y1
        ]

        if self.state == "disabled":
            fill_color = self.disabled_bg
            text_color = self.disabled_fg
        elif self.is_hovered:
            fill_color = self.hover_bg if self.hover_bg else self._adjust_color(self.bg_color, 20)
            text_color = self.fg_color
        else:
            fill_color = self.bg_color
            text_color = self.fg_color

        self.poly_id = self.create_polygon(points, fill=fill_color, smooth=True)
        self.text_id = self.create_text(w / 2, h / 2, text=self.text, fill=text_color, font=self.font)

    def _on_resize(self, event):
        if event.width > 1 and event.height > 1:
            self._draw()

    def _on_enter(self, event):
        if self.state == "normal":
            self.is_hovered = True
            super().configure(cursor=self.cursor_style)
            self._draw()

    def _on_leave(self, event):
        self.is_hovered = False
        self._draw()

    def _on_press(self, event):
        if self.state == "normal":
            press_bg = self._adjust_color(self.bg_color, -20)
            self.itemconfig(self.poly_id, fill=press_bg)

    def _on_release(self, event):
        if self.state == "normal":
            self._draw()
            if 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height():
                if self.command:
                    self.command()

    def configure(self, **kwargs):
        if "text" in kwargs:
            self.text = kwargs.pop("text")
        if "state" in kwargs:
            self.state = kwargs.pop("state")
            super().configure(cursor=self.cursor_style if self.state == "normal" else "arrow")
        if "bg" in kwargs or "background" in kwargs:
            self.bg_color = kwargs.pop("bg", kwargs.pop("background", None))
        if "fg" in kwargs or "foreground" in kwargs:
            self.fg_color = kwargs.pop("fg", kwargs.pop("foreground", None))
        if "parent_bg" in kwargs:
            self.parent_bg = kwargs.pop("parent_bg")
            super().configure(bg=self.parent_bg)
        if "hover_bg" in kwargs:
            self.hover_bg = kwargs.pop("hover_bg")
        if "disabled_bg" in kwargs:
            self.disabled_bg = kwargs.pop("disabled_bg")
        if "disabled_fg" in kwargs:
            self.disabled_fg = kwargs.pop("disabled_fg")
        if "command" in kwargs:
            self.command = kwargs.pop("command")
        if "radius" in kwargs:
            self.radius = kwargs.pop("radius")

        self._draw()

    config = configure

class PrinterControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ender-3 V3 SE — Studio Control")
        self.root.geometry("620x720")
        self.root.minsize(600, 680)

        try:
            self.root.iconbitmap("app_icon.ico")
        except Exception:
            pass

        self.current_theme = "dark"
        self.ser = None
        self.serial_lock = threading.Lock()
        self.is_connected = False
        self.is_printing = False
        self.pause_requested = False
        self.is_paused = False
        self.resume_requested = False
        self.stop_requested = False

        self.commands = []
        self.file_path = ""
        self.step_size = tk.DoubleVar(value=10.0)

        self.last_x, self.last_y, self.last_z = 0.0, 0.0, 0.0

        self.setup_ui()
        self.apply_theme()
        self.refresh_com_ports()

        self.root.after(2500, self.poll_telemetry_loop)

    def parse_telemetry(self, raw_str: str) -> str:
        """Преобразует строку Marlin вроде 'T:205.12 /205.00 B:60.05 /60.00' в понятный текст."""
        t_match = re.search(r"T:\s*([\d.]+)(?:\s*/\s*([\d.]+))?", raw_str)
        b_match = re.search(r"B:\s*([\d.]+)(?:\s*/\s*([\d.]+))?", raw_str)

        parts = []
        if t_match:
            cur_t = float(t_match.group(1))
            target_t = float(t_match.group(2)) if t_match.group(2) else 0.0
            if target_t > 0:
                parts.append(f"Темп. сопла: {cur_t:.1f}°C (цель {target_t:.0f}°C)")
            else:
                parts.append(f"Темп. сопла: {cur_t:.1f}°C")

        if b_match:
            cur_b = float(b_match.group(1))
            target_b = float(b_match.group(2)) if b_match.group(2) else 0.0
            if target_b > 0:
                parts.append(f"Темп. стола: {cur_b:.1f}°C (цель {target_b:.0f}°C)")
            else:
                parts.append(f"Темп. стола: {cur_b:.1f}°C")

        if parts:
            return "✦  " + "   |   ".join(parts)
        return f"✦  {raw_str}"

    def setup_ui(self):
        # 1. Шапка
        self.header_frame = tk.Frame(self.root, pady=12, padx=16)
        self.header_frame.pack(fill="x")

        title_container = tk.Frame(self.header_frame)
        title_container.pack(side="left")

        self.lbl_logo = tk.Label(title_container, text="✦ Ender-3 V3 SE", font=("Segoe UI", 13, "bold"))
        self.lbl_logo.pack(anchor="w")

        self.lbl_subtitle = tk.Label(title_container, text="Direct USB-C Spooler & Hardware Panel", font=("Segoe UI", 8))
        self.lbl_subtitle.pack(anchor="w")

        self.btn_theme = RoundedButton(
            self.header_frame, text="☀️ Светлая", font=("Segoe UI", 9, "bold"),
            radius=15, width=105, height=32, command=self.toggle_theme
        )
        self.btn_theme.pack(side="right")

        # 2. Карточка подключения
        self.card_conn = tk.Frame(self.root, padx=14, pady=10, relief="flat", bd=1)
        self.card_conn.pack(fill="x", padx=16, pady=4)

        tk.Label(self.card_conn, text="Подключение:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)

        self.port_combobox = ttk.Combobox(self.card_conn, width=22, state="readonly")
        self.port_combobox.pack(side="left", padx=6)

        self.btn_refresh = RoundedButton(
            self.card_conn, text="⟳", font=("Segoe UI", 10, "bold"),
            radius=8, width=34, height=28, command=self.refresh_com_ports
        )
        self.btn_refresh.pack(side="left", padx=3)

        self.btn_connect = RoundedButton(
            self.card_conn, text="Подключить", font=("Segoe UI", 9, "bold"),
            radius=10, width=115, height=28, command=self.toggle_connection
        )
        self.btn_connect.pack(side="left", padx=6)

        self.lbl_conn_status = tk.Label(self.card_conn, text="● Отключен", font=("Segoe UI", 9, "bold"))
        self.lbl_conn_status.pack(side="right", padx=6)

        # 3. Вкладки
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=8)

        self.tab_print = tk.Frame(self.notebook, padx=10, pady=10)
        self.tab_manual = tk.Frame(self.notebook, padx=10, pady=10)

        self.notebook.add(self.tab_print, text="  ✦ Печать файла  ")
        self.notebook.add(self.tab_manual, text="  ⚙ Ручное управление  ")

        self._build_print_tab()
        self._build_manual_tab()

        # 4. Футер
        self.footer_frame = tk.Frame(self.root, padx=16, pady=8)
        self.footer_frame.pack(fill="x", side="bottom")

        self.lbl_telemetry = tk.Label(
            self.footer_frame, text="✦ Принтер в режиме ожидания", font=("Segoe UI", 9), anchor="w"
        )
        self.lbl_telemetry.pack(fill="x")

    def _build_print_tab(self):
        # Выбор файла
        self.card_file = tk.Frame(self.tab_print, padx=12, pady=12, relief="flat", bd=1)
        self.card_file.pack(fill="x", pady=6)

        self.btn_browse = RoundedButton(
            self.card_file, text="Выбрать .gcode", font=("Segoe UI", 9, "bold"),
            radius=9, width=130, height=32, command=self.browse_file
        )
        self.btn_browse.pack(side="left", padx=4)

        self.lbl_filename = tk.Label(self.card_file, text="Файл модели не выбран", font=("Segoe UI", 9))
        self.lbl_filename.pack(side="left", padx=10)

        # Аналитика и прогресс
        self.card_progress = tk.Frame(self.tab_print, padx=14, pady=14, relief="flat", bd=1)
        self.card_progress.pack(fill="x", pady=8)

        self.lbl_percent = tk.Label(self.card_progress, text="Готов к печати (0%)", font=("Segoe UI", 12, "bold"))
        self.lbl_percent.pack(anchor="w", pady=2)

        self.progress_bar = ttk.Progressbar(self.card_progress, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill="x", pady=8)

        stats_row = tk.Frame(self.card_progress)
        stats_row.pack(fill="x")

        self.lbl_cmds = tk.Label(stats_row, text="Команды: 0 / 0", font=("Segoe UI", 9))
        self.lbl_cmds.pack(side="left")

        self.lbl_time = tk.Label(stats_row, text="Прошло: 00:00  •  Осталось: --:--", font=("Segoe UI", 9))
        self.lbl_time.pack(side="right")

        # Кнопки действий
        self.btn_frame = tk.Frame(self.tab_print, pady=10)
        self.btn_frame.pack(fill="x")

        self.btn_start = RoundedButton(
            self.btn_frame, text="▶  Старт печати", font=("Segoe UI", 11, "bold"),
            radius=14, height=46, command=self.start_print_thread
        )
        self.btn_start.pack(side="left", fill="x", expand=True, padx=4)

        self.btn_pause = RoundedButton(
            self.btn_frame, text="⏸  Пауза", font=("Segoe UI", 11, "bold"),
            radius=14, height=46, state="disabled", command=self.toggle_pause
        )
        self.btn_pause.pack(side="left", fill="x", expand=True, padx=4)

        self.btn_stop = RoundedButton(
            self.btn_frame, text="⏹  Стоп", font=("Segoe UI", 11, "bold"),
            radius=14, height=46, state="disabled", command=self.stop_print
        )
        self.btn_stop.pack(side="left", fill="x", expand=True, padx=4)

    def _build_manual_tab(self):
        # 1. Нагрев
        self.card_heat = tk.Frame(self.tab_manual, padx=14, pady=12, relief="flat", bd=1)
        self.card_heat.pack(fill="x", pady=6)

        tk.Label(self.card_heat, text="Управление температурой", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=4)

        row_nozzle = tk.Frame(self.card_heat)
        row_nozzle.pack(fill="x", pady=3)
        tk.Label(row_nozzle, text="Сопло (°C):", width=12, anchor="w").pack(side="left")
        self.entry_nozzle = ttk.Entry(row_nozzle, width=8)
        self.entry_nozzle.insert(0, "205")
        self.entry_nozzle.pack(side="left", padx=6)
        self.btn_set_nozzle = RoundedButton(
            row_nozzle, text="Нагреть", font=("Segoe UI", 8, "bold"),
            radius=8, width=80, height=28, command=self.set_nozzle_temp
        )
        self.btn_set_nozzle.pack(side="left", padx=4)

        row_bed = tk.Frame(self.card_heat)
        row_bed.pack(fill="x", pady=3)
        tk.Label(row_bed, text="Стол (°C):", width=12, anchor="w").pack(side="left")
        self.entry_bed = ttk.Entry(row_bed, width=8)
        self.entry_bed.insert(0, "60")
        self.entry_bed.pack(side="left", padx=6)
        self.btn_set_bed = RoundedButton(
            row_bed, text="Нагреть", font=("Segoe UI", 8, "bold"),
            radius=8, width=80, height=28, command=self.set_bed_temp
        )
        self.btn_set_bed.pack(side="left", padx=4)

        row_presets = tk.Frame(self.card_heat)
        row_presets.pack(fill="x", pady=6)
        self.btn_pre_pla = RoundedButton(
            row_presets, text="PLA (205 / 60)", font=("Segoe UI", 8),
            radius=8, width=105, height=28, command=lambda: self.apply_preset(205, 60)
        )
        self.btn_pre_pla.pack(side="left", padx=3)

        self.btn_pre_petg = RoundedButton(
            row_presets, text="PETG (230 / 75)", font=("Segoe UI", 8),
            radius=8, width=105, height=28, command=lambda: self.apply_preset(230, 75)
        )
        self.btn_pre_petg.pack(side="left", padx=3)

        self.btn_pre_cool = RoundedButton(
            row_presets, text="Охладить", font=("Segoe UI", 8),
            radius=8, width=85, height=28, command=lambda: self.apply_preset(0, 0)
        )
        self.btn_pre_cool.pack(side="left", padx=3)

        # 2. Перемещение
        self.card_move = tk.Frame(self.tab_manual, padx=14, pady=12, relief="flat", bd=1)
        self.card_move.pack(fill="both", expand=True, pady=6)

        tk.Label(self.card_move, text="Перемещение каретки и стола", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=4)

        f_step = tk.Frame(self.card_move)
        f_step.pack(fill="x", pady=4)
        tk.Label(f_step, text="Шаг: ", font=("Segoe UI", 9)).pack(side="left")
        for val in [0.1, 1.0, 10.0, 50.0]:
            ttk.Radiobutton(f_step, text=f"{val} мм", variable=self.step_size, value=val).pack(side="left", padx=4)

        grid_frame = tk.Frame(self.card_move)
        grid_frame.pack(pady=8)

        bw, bh, br = 64, 38, 9
        self.btn_y_up = RoundedButton(grid_frame, text="Y+  ▲", width=bw, height=bh, radius=br, command=lambda: self.jog_axis("Y", 1))
        self.btn_y_up.grid(row=0, column=1, pady=3, padx=2)

        self.btn_x_left = RoundedButton(grid_frame, text="◀  X-", width=bw, height=bh, radius=br, command=lambda: self.jog_axis("X", -1))
        self.btn_x_left.grid(row=1, column=0, padx=3, pady=2)

        self.btn_home = RoundedButton(grid_frame, text="⌂ Home", width=bw, height=bh, radius=br, command=self.home_all_axes)
        self.btn_home.grid(row=1, column=1, padx=3, pady=2)

        self.btn_x_right = RoundedButton(grid_frame, text="X+  ▶", width=bw, height=bh, radius=br, command=lambda: self.jog_axis("X", 1))
        self.btn_x_right.grid(row=1, column=2, padx=3, pady=2)

        self.btn_y_down = RoundedButton(grid_frame, text="Y-  ▼", width=bw, height=bh, radius=br, command=lambda: self.jog_axis("Y", -1))
        self.btn_y_down.grid(row=2, column=1, pady=3, padx=2)

        tk.Frame(grid_frame, width=20).grid(row=0, column=3)

        self.btn_z_up = RoundedButton(grid_frame, text="Z+  ▲", width=bw, height=bh, radius=br, command=lambda: self.jog_axis("Z", 1))
        self.btn_z_up.grid(row=0, column=4, pady=3, padx=2)

        self.btn_z_down = RoundedButton(grid_frame, text="Z-  ▼", width=bw, height=bh, radius=br, command=lambda: self.jog_axis("Z", -1))
        self.btn_z_down.grid(row=2, column=4, pady=3, padx=2)

        self.btn_unlock = RoundedButton(
            self.card_move, text="Обесточить двигатели (M84)", font=("Segoe UI", 8),
            radius=8, width=190, height=28, command=self.disable_steppers
        )
        self.btn_unlock.pack(anchor="w", pady=4)

    # ------------------ Тема оформления ------------------
    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.btn_theme.config(text="🌙 Тёмная" if self.current_theme == "light" else "☀️ Светлая")
        self.apply_theme()

    def apply_theme(self):
        t = THEMES[self.current_theme]

        self.root.configure(bg=t["bg"])
        self.header_frame.configure(bg=t["bg"])
        self.header_frame.winfo_children()[0].configure(bg=t["bg"])
        self.footer_frame.configure(bg=t["bg"])
        self.btn_frame.configure(bg=t["bg"])

        self.lbl_logo.configure(bg=t["bg"], fg=t["accent"])
        self.lbl_subtitle.configure(bg=t["bg"], fg=t["fg_muted"])
        self.lbl_telemetry.configure(bg=t["bg"], fg=t["telemetry"])

        cards = [self.card_conn, self.card_file, self.card_progress, self.card_heat, self.card_move]
        for c in cards:
            c.configure(bg=t["surface"], highlightbackground=t["surface_border"], highlightthickness=1)
            for child in c.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=t["surface"], fg=t["fg"])
                elif isinstance(child, tk.Frame):
                    child.configure(bg=t["surface"])
                    for sub in child.winfo_children():
                        if isinstance(sub, tk.Label):
                            sub.configure(bg=t["surface"], fg=t["fg"])
                        elif isinstance(sub, tk.Frame):
                            sub.configure(bg=t["surface"])

        self.lbl_conn_status.configure(
            fg=t["badge_connected"] if self.is_connected else t["badge_disconnected"]
        )

        self.tab_print.configure(bg=t["bg"])
        self.tab_manual.configure(bg=t["bg"])

        self.style.configure("TNotebook", background=t["bg"], borderwidth=0)
        self.style.configure(
            "TNotebook.Tab", background=t["card"], foreground=t["fg"],
            padding=[14, 6], font=("Segoe UI", 9, "bold"), borderwidth=0
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", t["accent_bg"])],
            foreground=[("selected", "#ffffff" if self.current_theme == "dark" else t["accent"])]
        )

        self.style.configure(
            "Horizontal.TProgressbar",
            background=t["accent"],
            troughcolor=t["card"],
            borderwidth=0
        )

        self.btn_theme.configure(
            parent_bg=t["bg"], bg=t["card"], fg=t["fg"], hover_bg=t["btn_normal_hover"]
        )

        self.btn_refresh.configure(
            parent_bg=t["surface"], bg=t["btn_normal"], fg=t["btn_fg"], hover_bg=t["btn_normal_hover"]
        )

        self.btn_connect.configure(
            parent_bg=t["surface"],
            bg=t["btn_normal"] if self.is_connected else t["accent_bg"],
            fg=t["btn_fg"] if self.is_connected else ("#ffffff" if self.current_theme == "dark" else t["accent"]),
            hover_bg=t["btn_normal_hover"] if self.is_connected else t["accent_hover"]
        )

        self.btn_browse.configure(
            parent_bg=t["surface"], bg=t["btn_normal"], fg=t["btn_fg"],
            hover_bg=t["btn_normal_hover"], disabled_bg=t["btn_disabled"], disabled_fg=t["btn_disabled_fg"]
        )

        self.btn_start.configure(
            parent_bg=t["bg"], bg=t["btn_start"], fg=t["btn_start_fg"],
            hover_bg=t["btn_start_hover"], disabled_bg=t["btn_disabled"], disabled_fg=t["btn_disabled_fg"]
        )

        self.btn_pause.configure(
            parent_bg=t["bg"], bg=t["btn_pause"] if not self.is_paused else "#1a73e8",
            fg=t["btn_pause_fg"], hover_bg=t["btn_pause_hover"],
            disabled_bg=t["btn_disabled"], disabled_fg=t["btn_disabled_fg"]
        )

        self.btn_stop.configure(
            parent_bg=t["bg"], bg=t["btn_stop"], fg=t["btn_stop_fg"],
            hover_bg=t["btn_stop_hover"], disabled_bg=t["btn_disabled"], disabled_fg=t["btn_disabled_fg"]
        )

        manual_buttons = [
            self.btn_set_nozzle, self.btn_set_bed, self.btn_pre_pla, self.btn_pre_petg,
            self.btn_pre_cool, self.btn_y_up, self.btn_x_left, self.btn_home,
            self.btn_x_right, self.btn_y_down, self.btn_z_up, self.btn_z_down, self.btn_unlock
        ]
        for b in manual_buttons:
            b.configure(
                parent_bg=t["surface"], bg=t["btn_normal"], fg=t["btn_fg"],
                hover_bg=t["btn_normal_hover"], disabled_bg=t["btn_disabled"], disabled_fg=t["btn_disabled_fg"]
            )

    # ------------------ Логика управления ------------------
    def refresh_com_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [f"{p.device} ({p.description})" for p in ports]
        self.port_combobox["values"] = port_list
        if port_list:
            self.port_combobox.current(0)
        else:
            self.port_combobox.set("Порты не обнаружены")

    def toggle_connection(self):
        t = THEMES[self.current_theme]
        if not self.is_connected:
            port_str = self.port_combobox.get()
            if not port_str or "Порты не" in port_str:
                messagebox.showerror("Ошибка", "Выберите порт подключения.")
                return

            com_device = port_str.split(" ")[0]
            try:
                self.ser = serial.Serial(com_device, DEFAULT_BAUDRATE, timeout=1.0)
                time.sleep(2.5)
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()
                self.is_connected = True
                self.btn_connect.config(text="Отключить", bg=t["btn_normal"], fg=t["btn_fg"])
                self.lbl_conn_status.config(text="● Онлайн", fg=t["badge_connected"])
                self.lbl_telemetry.config(text=f"✦ Соединение активно ({com_device})")
            except Exception as e:
                messagebox.showerror("Ошибка порта", str(e))
        else:
            if self.is_printing:
                messagebox.showwarning("Внимание", "Нельзя отключать кабель во время печати.")
                return
            with self.serial_lock:
                if self.ser and self.ser.is_open:
                    self.ser.close()
                self.ser = None
            self.is_connected = False
            self.btn_connect.config(text="Подключить", bg=t["accent_bg"], fg="#ffffff" if self.current_theme == "dark" else t["accent"])
            self.lbl_conn_status.config(text="● Отключен", fg=t["badge_disconnected"])
            self.lbl_telemetry.config(text="✦ Порт закрыт.")

    def raw_send_and_wait(self, cmd_str, timeout_seconds=120.0):
        with self.serial_lock:
            if not self.ser or not self.ser.is_open:
                return False
            try:
                self.ser.write((cmd_str + "\n").encode("ascii"))
            except Exception:
                return False

            start_wait = time.time()
            while True:
                if self.stop_requested:
                    return False
                line = self.ser.readline().decode("ascii", errors="ignore").strip()
                if line:
                    start_wait = time.time()
                    if "T:" in line:
                        self.lbl_telemetry.config(text=self.parse_telemetry(line))
                    if "ok" in line.lower():
                        return True
                if time.time() - start_wait > timeout_seconds:
                    return False

    def send_async_command(self, cmd_str):
        if not self.is_connected:
            messagebox.showwarning("Внимание", "Сначала нажмите «Подключить».")
            return
        if self.is_printing:
            return
        threading.Thread(target=self.raw_send_and_wait, args=(cmd_str,), daemon=True).start()

    def jog_axis(self, axis, direction):
        dist = self.step_size.get() * direction
        speed = 3000 if axis in ["X", "Y"] else 800
        cmd_chain = f"G91\nG1 {axis}{dist:.2f} F{speed}\nG90"
        for c in cmd_chain.split("\n"):
            self.send_async_command(c)

    def home_all_axes(self):
        if messagebox.askyesno("Калибровка", "Запустить автопарковку всех осей (G28)?"):
            self.send_async_command("G28")

    def disable_steppers(self):
        self.send_async_command("M84")
        self.lbl_telemetry.config(text="✦ Моторы обесточены (M84)")

    def set_nozzle_temp(self):
        try:
            temp = int(self.entry_nozzle.get())
            self.send_async_command(f"M104 S{temp}")
            self.lbl_telemetry.config(text=f"✦ Нагрев сопла: {temp}°C")
        except ValueError:
            messagebox.showerror("Ошибка", "Введите целое число градусов.")

    def set_bed_temp(self):
        try:
            temp = int(self.entry_bed.get())
            self.send_async_command(f"M140 S{temp}")
            self.lbl_telemetry.config(text=f"✦ Нагрев стола: {temp}°C")
        except ValueError:
            messagebox.showerror("Ошибка", "Введите целое число градусов.")

    def apply_preset(self, nozzle_t, bed_t):
        self.entry_nozzle.delete(0, tk.END)
        self.entry_nozzle.insert(0, str(nozzle_t))
        self.entry_bed.delete(0, tk.END)
        self.entry_bed.insert(0, str(bed_t))
        self.send_async_command(f"M104 S{nozzle_t}")
        self.send_async_command(f"M140 S{bed_t}")
        self.lbl_telemetry.config(text=f"✦ Пресет: Сопло {nozzle_t}°C, Стол {bed_t}°C")

    def poll_telemetry_loop(self):
        if self.is_connected and not self.is_printing and not self.is_paused:
            threading.Thread(target=self._query_m105, daemon=True).start()
        self.root.after(2500, self.poll_telemetry_loop)

    def _query_m105(self):
        with self.serial_lock:
            if self.ser and self.ser.is_open:
                try:
                    self.ser.write(b"M105\n")
                    line = self.ser.readline().decode("ascii", errors="ignore").strip()
                    if "T:" in line:
                        self.lbl_telemetry.config(text=self.parse_telemetry(line))
                except Exception:
                    pass

    def browse_file(self):
        f = filedialog.askopenfilename(filetypes=[("G-code files", "*.gcode"), ("All files", "*.*")])
        if f:
            self.file_path = f
            self.lbl_filename.config(text=f.split("/")[-1].split("\\")[-1])

    def toggle_pause(self):
        if not self.is_paused and not self.pause_requested:
            self.pause_requested = True
            self.btn_pause.config(text="Отвод...", state="disabled")
            self.lbl_telemetry.config(text="✦ Завершаем сегмент и отводим сопло...")
        elif self.is_paused:
            self.resume_requested = True
            self.btn_pause.config(text="Возврат...", state="disabled")

    def stop_print(self):
        if messagebox.askyesno("Экстренный стоп", "Прервать печать и обесточить нагреватели?"):
            self.stop_requested = True
            self.lbl_telemetry.config(text="✦ Аварийная остановка...")
            threading.Thread(target=self._emergency_kill, daemon=True).start()

    def _emergency_kill(self):
        with self.serial_lock:
            if self.ser and self.ser.is_open:
                try:
                    self.ser.write(b"\nM410\nM104 S0\nM140 S0\nM106 S0\nM84\n")
                    self.ser.flush()
                except Exception:
                    pass

    def _finish_print_parking(self):
        """Безопасный отвод сопла, выдвижение стола вперед и охлаждение."""
        self.lbl_telemetry.config(text="✦ Завершение: подъем башни и выдвижение стола...")

        self.raw_send_and_wait("M83")
        self.raw_send_and_wait("G1 E-3 F1800")

        if self.last_z < 235:
            self.raw_send_and_wait("G91")
            self.raw_send_and_wait("G1 Z15 F1200")
            self.raw_send_and_wait("G90")
        else:
            self.raw_send_and_wait("G90")
            self.raw_send_and_wait("G1 Z250 F1200")

        self.raw_send_and_wait("G90")
        self.raw_send_and_wait("G1 X10 Y210 F5000")

        self.raw_send_and_wait("M104 S0")
        self.raw_send_and_wait("M140 S0")
        self.raw_send_and_wait("M106 S0")
        self.raw_send_and_wait("M84")

    def start_print_thread(self):
        if not self.file_path:
            messagebox.showwarning("Внимание", "Выберите .gcode файл перед стартом.")
            return

        if not self.is_connected:
            self.toggle_connection()
            if not self.is_connected:
                return

        self.is_printing = True
        self.stop_requested = False
        self.pause_requested = False
        self.is_paused = False
        self.resume_requested = False

        self.btn_start.config(state="disabled")
        self.btn_browse.config(state="disabled")
        self.btn_pause.config(state="normal", text="⏸  Пауза")
        self.btn_stop.config(state="normal")
        self.notebook.tab(1, state="disabled")

        threading.Thread(target=self._run_print_loop, daemon=True).start()

    def _run_print_loop(self):
        t = THEMES[self.current_theme]
        with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_lines = f.readlines()

        self.commands = [re.sub(r";.*$", "", l).strip() for l in raw_lines if re.sub(r";.*$", "", l).strip()]
        total = len(self.commands)
        self.progress_bar["maximum"] = total
        start_time = time.time()

        for idx, cmd in enumerate(self.commands, start=1):
            if self.stop_requested:
                break

            # Пауза
            if self.pause_requested:
                self.is_paused = True
                self.pause_requested = False
                self.lbl_telemetry.config(text="✦ Парковка сопла в угол...")

                self.raw_send_and_wait("M83")
                self.raw_send_and_wait("G1 E-3 F1800")
                self.raw_send_and_wait("G91")
                self.raw_send_and_wait("G1 Z10 F1200")
                self.raw_send_and_wait("G90")
                self.raw_send_and_wait("G1 X10 Y200 F6000")

                self.btn_pause.config(text="▶  Продолжить", bg="#1a73e8", fg="#ffffff", state="normal")
                self.lbl_telemetry.config(text="✦ Пауза. Сопло безопасно отведено.")

                while not self.resume_requested and not self.stop_requested:
                    time.sleep(0.2)

                if self.stop_requested:
                    break

                self.lbl_telemetry.config(text="✦ Возврат сопла...")
                self.raw_send_and_wait("G90")
                self.raw_send_and_wait(f"G1 X{self.last_x} Y{self.last_y} F6000")
                self.raw_send_and_wait("G91")
                self.raw_send_and_wait("G1 Z-10 F1200")
                self.raw_send_and_wait("G90")
                self.raw_send_and_wait("M83")
                self.raw_send_and_wait("G1 E3 F1800")

                self.is_paused = False
                self.resume_requested = False
                self.btn_pause.config(text="⏸  Пауза", bg=t["btn_pause"], fg=t["btn_pause_fg"], state="normal")

            # Координаты
            mx, my, mz = re.search(r"X([-\d.]+)", cmd), re.search(r"Y([-\d.]+)", cmd), re.search(r"Z([-\d.]+)", cmd)
            if mx: self.last_x = float(mx.group(1))
            if my: self.last_y = float(my.group(1))
            if mz: self.last_z = float(mz.group(1))

            success = self.raw_send_and_wait(cmd)
            if not success and self.stop_requested:
                break

            # Прогресс и проценты
            percent = int((idx / total) * 100)
            self.progress_bar["value"] = idx
            self.lbl_percent.config(text=f"Печать: {percent}%")
            self.lbl_cmds.config(text=f"Команды: {idx} / {total}")

            # Расчет прошедшего времени
            elapsed = int(time.time() - start_time)
            el_m, el_s = divmod(elapsed, 60)
            el_h, el_m = divmod(el_m, 60)
            if el_h > 0:
                elapsed_str = f"{el_h}:{el_m:02d}:{el_s:02d}"
            else:
                elapsed_str = f"{el_m:02d}:{el_s:02d}"

            # Динамический расчет оставшегося времени
            if idx > 25 and idx < total:
                rate = idx / elapsed if elapsed > 0 else 0
                if rate > 0:
                    remaining_sec = int((total - idx) / rate)
                    rem_m, rem_s = divmod(remaining_sec, 60)
                    rem_h, rem_m = divmod(rem_m, 60)
                    if rem_h > 0:
                        remaining_str = f"~{rem_h} ч {rem_m:02d} мин"
                    else:
                        remaining_str = f"~{rem_m:02d}:{rem_s:02d}"
                else:
                    remaining_str = "Расчет..."
            elif idx >= total:
                remaining_str = "00:00"
            else:
                remaining_str = "Расчет..."

            self.lbl_time.config(text=f"Прошло: {elapsed_str}  •  Осталось: {remaining_str}")

        # Финализация печати
        if self.stop_requested:
            self._emergency_kill()
            self.lbl_telemetry.config(text="✦ Печать отменена: нагреватели обесточены.")
        else:
            self._finish_print_parking()
            self.lbl_telemetry.config(text="✦ Готово: стол подан вперед, башня поднята.")
            messagebox.showinfo("Готово", "Печать успешно завершена!\nСтол выдвинут вперед, деталь готова к снятию.")

        self._reset_ui()

    def _reset_ui(self):
        t = THEMES[self.current_theme]
        self.btn_start.config(state="normal", bg=t["btn_start"])
        self.btn_browse.config(state="normal")
        self.btn_pause.config(state="disabled", text="⏸  Пауза", bg=t["btn_pause"])
        self.btn_stop.config(state="disabled", bg=t["btn_stop"])
        self.notebook.tab(1, state="normal")
        self.is_printing = False

if __name__ == "__main__":
    root = tk.Tk()
    app = PrinterControlApp(root)
    root.mainloop()