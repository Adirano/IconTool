import tkinter as tk
from tkinter import ttk
from PIL import ImageTk

from config import SELECTION_COLOR, SELECTION_WIDTH
from utils.coordinate_utils import normalize_rect


class ImageCanvas(tk.Frame):
    """左侧图片显示与选区画布"""

    def __init__(self, parent, on_selection_callback=None):
        super().__init__(parent, bg="#2b2b2b")
        self.on_selection_callback = on_selection_callback
        self.image = None
        self._photo_image = None
        self._selection_id = None
        self._drag_start = None
        self._build_ui()

    # ------------------------------------------------------------------
    # 构建 UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        self._v_scroll = ttk.Scrollbar(self, orient=tk.VERTICAL)
        self._h_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL)

        self.canvas = tk.Canvas(
            self,
            bg="#2b2b2b",
            cursor="crosshair",
            highlightthickness=0,
            yscrollcommand=self._v_scroll.set,
            xscrollcommand=self._h_scroll.set,
        )

        self._v_scroll.config(command=self.canvas.yview)
        self._h_scroll.config(command=self.canvas.xview)

        self._v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 鼠标事件
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        # 画布尺寸变化时重新居中占位文字
        self.canvas.bind("<Configure>", self._on_configure)

        self._draw_placeholder()

    # ------------------------------------------------------------------
    # 占位文字
    # ------------------------------------------------------------------
    def _draw_placeholder(self):
        self.canvas.delete("all")
        w = max(self.canvas.winfo_width(), 400)
        h = max(self.canvas.winfo_height(), 400)
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

    # ------------------------------------------------------------------
    # 坐标转换（处理滚动偏移）
    # ------------------------------------------------------------------
    def _canvas_xy(self, event):
        return self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

    # ------------------------------------------------------------------
    # 鼠标事件处理
    # ------------------------------------------------------------------
    def _on_press(self, event):
        if self.image is None:
            return
        self._drag_start = self._canvas_xy(event)
        if self._selection_id is not None:
            self.canvas.delete(self._selection_id)
            self._selection_id = None

    def _on_drag(self, event):
        if self.image is None or self._drag_start is None:
            return
        x, y = self._canvas_xy(event)
        x0, y0 = self._drag_start
        if self._selection_id is not None:
            self.canvas.delete(self._selection_id)
        self._selection_id = self.canvas.create_rectangle(
            x0, y0, x, y,
            outline=SELECTION_COLOR,
            width=SELECTION_WIDTH,
            tags="selection",
        )

    def _on_release(self, event):
        if self.image is None or self._drag_start is None:
            return
        x, y = self._canvas_xy(event)
        x0, y0 = self._drag_start
        self._drag_start = None

        # 坐标限制在图片范围内
        img_w, img_h = self.image.size
        x0 = max(0.0, min(float(x0), float(img_w)))
        y0 = max(0.0, min(float(y0), float(img_h)))
        x = max(0.0, min(float(x), float(img_w)))
        y = max(0.0, min(float(y), float(img_h)))

        left, top, width, height = normalize_rect(x0, y0, x, y)
        if width <= 0 or height <= 0:
            return

        # 用精确边界重绘最终选框
        if self._selection_id is not None:
            self.canvas.delete(self._selection_id)
        self._selection_id = self.canvas.create_rectangle(
            left, top, left + width, top + height,
            outline=SELECTION_COLOR,
            width=SELECTION_WIDTH,
            tags="selection",
        )

        if self.on_selection_callback:
            self.on_selection_callback(left, top, width, height)

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------
    def show_image(self, image):
        self.image = image
        self._photo_image = ImageTk.PhotoImage(image)
        self._selection_id = None

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self._photo_image, tags="image")
        self.canvas.configure(scrollregion=(0, 0, image.width, image.height))
