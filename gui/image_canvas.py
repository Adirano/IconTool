import tkinter as tk
from PIL import Image, ImageTk

from config import SELECTION_COLOR, SELECTION_WIDTH
from utils.coordinate_utils import normalize_rect


class ImageCanvas(tk.Frame):
    """左侧图片显示与选区画布"""

    def __init__(self, parent, on_selection_callback=None, on_view_changed_callback=None):
        super().__init__(parent, bg="#2b2b2b")
        self.on_selection_callback = on_selection_callback
        self.on_view_changed_callback = on_view_changed_callback

        self.image = None
        self._display_image = None
        self._photo_image = None

        self._selection_id = None
        self._selection_rect = None  # (left, top, width, height) in image pixels
        self._drag_start_img = None
        self._drag_current_rect = None

        self._scale = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0
        self._min_scale = 0.05
        self._max_scale = 10.0

        self._edge_trigger_px = 28
        self._edge_pan_interval_ms = 30
        self._edge_pan_step_px = 22
        self._edge_pan_job = None
        self._last_mouse_canvas = (0, 0)

        self._build_ui()

    # ------------------------------------------------------------------
    # 构建 UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        self.canvas = tk.Canvas(
            self,
            bg="#2b2b2b",
            cursor="crosshair",
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 鼠标事件
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)

        # 鼠标滚轮缩放
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)

        # 画布尺寸变化时重新居中占位文字
        self.canvas.bind("<Configure>", self._on_configure)

        self._draw_placeholder()

    # ------------------------------------------------------------------
    # 坐标/布局工具
    # ------------------------------------------------------------------
    def _display_size(self):
        if self.image is None:
            return 0, 0
        w = max(1, int(round(self.image.width * self._scale)))
        h = max(1, int(round(self.image.height * self._scale)))
        return w, h

    def _clamp_offset(self):
        if self.image is None:
            return
        canvas_w = max(1, self.canvas.winfo_width())
        canvas_h = max(1, self.canvas.winfo_height())
        disp_w, disp_h = self._display_size()

        if disp_w <= canvas_w:
            self._offset_x = (canvas_w - disp_w) / 2.0
        else:
            min_x = canvas_w - disp_w
            max_x = 0.0
            self._offset_x = min(max(self._offset_x, min_x), max_x)

        if disp_h <= canvas_h:
            self._offset_y = (canvas_h - disp_h) / 2.0
        else:
            min_y = canvas_h - disp_h
            max_y = 0.0
            self._offset_y = min(max(self._offset_y, min_y), max_y)

    def _clamp_image_xy(self, x, y):
        if self.image is None:
            return 0, 0
        return (
            max(0, min(int(round(x)), self.image.width)),
            max(0, min(int(round(y)), self.image.height)),
        )

    def _to_image_xy(self, canvas_x, canvas_y):
        return (
            (canvas_x - self._offset_x) / self._scale,
            (canvas_y - self._offset_y) / self._scale,
        )

    def _to_canvas_xy(self, image_x, image_y):
        return (
            image_x * self._scale + self._offset_x,
            image_y * self._scale + self._offset_y,
        )

    def _refresh_display_image(self):
        if self.image is None:
            self._display_image = None
            self._photo_image = None
            return
        disp_w, disp_h = self._display_size()
        if disp_w == self.image.width and disp_h == self.image.height:
            self._display_image = self.image
        else:
            self._display_image = self.image.resize((disp_w, disp_h), resample=Image.Resampling.LANCZOS)
        self._photo_image = ImageTk.PhotoImage(self._display_image)

    def _notify_view_changed(self):
        if self.on_view_changed_callback is None:
            return
        if self.image is None:
            self.on_view_changed_callback(None, None, self._scale)
            return
        self.on_view_changed_callback(self.image.width, self.image.height, self._scale)

    def _draw_selection_rect(self, rect):
        if self._selection_id is not None:
            self.canvas.delete(self._selection_id)
            self._selection_id = None
        if rect is None:
            return
        left, top, width, height = rect
        if width <= 0 or height <= 0:
            return
        x0, y0 = self._to_canvas_xy(left, top)
        x1, y1 = self._to_canvas_xy(left + width, top + height)
        self._selection_id = self.canvas.create_rectangle(
            x0,
            y0,
            x1,
            y1,
            outline=SELECTION_COLOR,
            width=SELECTION_WIDTH,
            tags="selection",
        )

    # 鼠标滚轮缩放
    def _on_mousewheel(self, event):
        if self.image is None:
            return

        canvas_x = event.x
        canvas_y = event.y
        image_x, image_y = self._to_image_xy(canvas_x, canvas_y)

        if hasattr(event, "delta"):
            delta = event.delta
        elif event.num == 4:
            delta = 120
        elif event.num == 5:
            delta = -120
        else:
            delta = 0

        if delta == 0:
            return "break"

        scale_factor = 1.1 if delta > 0 else (1 / 1.1)
        new_scale = min(max(self._scale * scale_factor, self._min_scale), self._max_scale)
        if abs(new_scale - self._scale) < 1e-6:
            return "break"

        self._offset_x = canvas_x - image_x * new_scale
        self._offset_y = canvas_y - image_y * new_scale
        self._scale = new_scale

        self._redraw_image()
        self._notify_view_changed()
        return "break"

    # ------------------------------------------------------------------
    # 占位文字
    # ------------------------------------------------------------------
    def _draw_placeholder(self):
        self.canvas.delete("all")
        w = max(self.canvas.winfo_width(), 420)
        h = max(self.canvas.winfo_height(), 420)
        self.canvas.create_text(
            w // 2,
            h // 2,
            text="从本地选取图片文件或 Ctrl+V 粘贴图片",
            font=("Microsoft YaHei", 14),
            fill="#888888",
            tags="placeholder",
        )

    def _on_configure(self, event):
        if self.image is None:
            self._draw_placeholder()
            return
        self._redraw_image()

    # ------------------------------------------------------------------
    # 边缘自动平移
    # ------------------------------------------------------------------
    def _on_motion(self, event):
        self._last_mouse_canvas = (event.x, event.y)
        if self.image is not None:
            self._start_edge_pan()

    def _is_near_edge(self, x, y):
        canvas_w = max(1, self.canvas.winfo_width())
        canvas_h = max(1, self.canvas.winfo_height())
        m = self._edge_trigger_px
        return x < m or x > (canvas_w - m) or y < m or y > (canvas_h - m)

    def _start_edge_pan(self):
        if self._edge_pan_job is None:
            self._edge_pan_job = self.after(self._edge_pan_interval_ms, self._edge_pan_step)

    def _stop_edge_pan(self):
        if self._edge_pan_job is not None:
            self.after_cancel(self._edge_pan_job)
            self._edge_pan_job = None

    def _edge_pan_step(self):
        self._edge_pan_job = None
        if self.image is None:
            return

        x, y = self._last_mouse_canvas
        canvas_w = max(1, self.canvas.winfo_width())
        canvas_h = max(1, self.canvas.winfo_height())
        m = self._edge_trigger_px

        dx = 0.0
        dy = 0.0
        if x < m:
            dx = min(self._edge_pan_step_px, m - x)
        elif x > canvas_w - m:
            dx = -min(self._edge_pan_step_px, x - (canvas_w - m))

        if y < m:
            dy = min(self._edge_pan_step_px, m - y)
        elif y > canvas_h - m:
            dy = -min(self._edge_pan_step_px, y - (canvas_h - m))

        if dx != 0.0 or dy != 0.0:
            prev_x = self._offset_x
            prev_y = self._offset_y
            self._offset_x += dx
            self._offset_y += dy
            self._clamp_offset()

            moved = (abs(self._offset_x - prev_x) > 1e-6) or (abs(self._offset_y - prev_y) > 1e-6)
            if moved:
                self._redraw_image()
                self._update_drag_preview(self._last_mouse_canvas[0], self._last_mouse_canvas[1])

        if self._drag_start_img is not None or self._is_near_edge(x, y):
            self._start_edge_pan()

    def _update_drag_preview(self, canvas_x, canvas_y):
        if self._drag_start_img is None:
            return
        x0, y0 = self._drag_start_img
        x1, y1 = self._to_image_xy(canvas_x, canvas_y)
        x0, y0 = self._clamp_image_xy(x0, y0)
        x1, y1 = self._clamp_image_xy(x1, y1)
        left, top, width, height = normalize_rect(x0, y0, x1, y1)
        self._drag_current_rect = (left, top, width, height)
        self._draw_selection_rect(self._drag_current_rect)

    # ------------------------------------------------------------------
    # 鼠标事件处理
    # ------------------------------------------------------------------
    def _on_press(self, event):
        if self.image is None:
            return
        self.canvas.focus_set()
        self._last_mouse_canvas = (event.x, event.y)

        start_x, start_y = self._to_image_xy(event.x, event.y)
        self._drag_start_img = self._clamp_image_xy(start_x, start_y)
        self._drag_current_rect = None
        self._selection_rect = None
        self._draw_selection_rect(None)
        self._update_drag_preview(event.x, event.y)
        self._start_edge_pan()

    def _on_drag(self, event):
        if self.image is None or self._drag_start_img is None:
            return
        self._last_mouse_canvas = (event.x, event.y)
        self._update_drag_preview(event.x, event.y)

    def _on_release(self, event):
        if self.image is None or self._drag_start_img is None:
            return

        self._stop_edge_pan()
        self._last_mouse_canvas = (event.x, event.y)
        self._update_drag_preview(event.x, event.y)

        left, top, width, height = self._drag_current_rect or (0, 0, 0, 0)
        self._drag_start_img = None
        self._drag_current_rect = None

        if width <= 0 or height <= 0:
            self._selection_rect = None
            self._draw_selection_rect(None)
            return

        self.set_selection_rect(left, top, width, height, notify=True)

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------
    def show_image(self, image):
        self.image = image
        self._scale = 1.0
        self._selection_rect = None
        self._drag_start_img = None
        self._drag_current_rect = None

        canvas_w = max(1, self.canvas.winfo_width())
        canvas_h = max(1, self.canvas.winfo_height())
        disp_w, disp_h = self._display_size()
        self._offset_x = (canvas_w - disp_w) / 2.0
        self._offset_y = (canvas_h - disp_h) / 2.0

        self._redraw_image()
        self._notify_view_changed()

    def set_selection_rect(self, left, top, width, height, notify=False):
        if self.image is None:
            return False

        left = int(left)
        top = int(top)
        width = int(width)
        height = int(height)

        if left < 0 or top < 0 or width <= 0 or height <= 0:
            return False
        if left + width > self.image.width or top + height > self.image.height:
            return False

        self._selection_rect = (left, top, width, height)
        self._draw_selection_rect(self._selection_rect)

        if notify and self.on_selection_callback:
            self.on_selection_callback(left, top, width, height)
        return True

    def _redraw_image(self):
        self.canvas.delete("all")
        if self.image is None:
            self._draw_placeholder()
            return

        self._clamp_offset()
        self._refresh_display_image()
        self.canvas.create_image(self._offset_x, self._offset_y, anchor=tk.NW, image=self._photo_image, tags="image")

        rect = self._drag_current_rect if self._drag_current_rect is not None else self._selection_rect
        self._draw_selection_rect(rect)
