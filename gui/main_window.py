import tkinter as tk
import json
from tkinter import ttk, filedialog, messagebox

from config import APP_TITLE
from controllers.image_controller import ImageController
from gui.image_canvas import ImageCanvas
from gui.right_panel import RightPanel
from utils.image_utils import crop_image


class MainWindow(tk.Tk):
    """主窗口：左侧图片画布 + 右侧信息面板"""

    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1280x800")
        self.minsize(900, 620)

        self._controller = ImageController()
        self._build_menu()
        self._build_ui()
        self._bind_hotkeys()

    # ------------------------------------------------------------------
    # 菜单
    # ------------------------------------------------------------------
    def _build_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(
            label="打开图片文件...",
            command=self._open_file,
            accelerator="Ctrl+O",
        )
        file_menu.add_command(
            label="从剪贴板粘贴",
            command=self._paste_clipboard,
            accelerator="Ctrl+V",
        )
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.quit)
        menubar.add_cascade(label="文件", menu=file_menu)
        self.config(menu=menubar)

    # ------------------------------------------------------------------
    # 布局
    # ------------------------------------------------------------------
    def _build_ui(self):
        # 工具栏
        toolbar = tk.Frame(self, bg="#e4e4e4", height=44)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        ttk.Button(toolbar, text="打开图片", command=self._open_file).pack(
            side=tk.LEFT, padx=8, pady=7
        )
        ttk.Button(toolbar, text="粘贴图片  Ctrl+V", command=self._paste_clipboard).pack(
            side=tk.LEFT, padx=2, pady=7
        )

        # 内容区域
        content = tk.Frame(self)
        content.pack(fill=tk.BOTH, expand=True)

        # 左侧容器（画布 + 底部状态栏）
        left_panel = tk.Frame(content)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 左侧画布（可伸缩）
        self._canvas = ImageCanvas(
            left_panel,
            on_selection_callback=self._on_selection,
            on_view_changed_callback=self._on_view_changed,
        )
        self._canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 图片信息栏：分辨率 + 缩放比例
        status_bar = tk.Frame(left_panel, bg="#f0f0f0", height=28, bd=1, relief=tk.SOLID)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        status_bar.pack_propagate(False)

        self._view_info_var = tk.StringVar(value="分辨率: - | 缩放: 100%")
        tk.Label(
            status_bar,
            textvariable=self._view_info_var,
            bg="#f0f0f0",
            fg="#333333",
            font=("Microsoft YaHei", 10),
            anchor="w",
            padx=8,
        ).pack(fill=tk.BOTH, expand=True)

        # 分隔线
        ttk.Separator(content, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y)

        # 右侧面板（固定宽度）
        self._right = RightPanel(content, on_test_coord_callback=self._on_test_coord)
        self._right.pack(side=tk.RIGHT, fill=tk.Y)

    # ------------------------------------------------------------------
    # 快捷键
    # ------------------------------------------------------------------
    def _bind_hotkeys(self):
        self.bind("<Control-o>", lambda _e: self._open_file())
        self.bind("<Control-v>", lambda _e: self._paste_clipboard())

    # ------------------------------------------------------------------
    # 事件处理
    # ------------------------------------------------------------------
    def _open_file(self):
        path = filedialog.askopenfilename(
            title="选择图片文件",
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tiff *.ico"),
                ("所有文件", "*.*"),
            ],
        )
        if not path:
            return
        try:
            image = self._controller.load_from_file(path)
            self._canvas.show_image(image)
            self._right.set_image_loaded(True)
        except Exception as exc:
            messagebox.showerror("打开失败", f"无法读取图片文件：\n{exc}")

    def _paste_clipboard(self):
        image = self._controller.load_from_clipboard()
        if image is not None:
            self._canvas.show_image(image)
            self._right.set_image_loaded(True)
        else:
            messagebox.showwarning("粘贴失败", "剪贴板中未检测到图片")

    def _parse_test_rect(self, text):
        if not text:
            raise ValueError("请输入坐标，格式为 left,top,width,height")

        try:
            data = json.loads(text)
            if isinstance(data, dict):
                nums = [data["left"], data["top"], data["width"], data["height"]]
            elif isinstance(data, (list, tuple)) and len(data) == 4:
                nums = list(data)
            else:
                raise ValueError("JSON 坐标格式不正确")
        except Exception:
            parts = [part.strip() for part in text.replace("，", ",").split(",") if part.strip()]
            if len(parts) != 4:
                raise ValueError("坐标格式错误，请使用 left,top,width,height")
            nums = parts

        try:
            left, top, width, height = (int(value) for value in nums)
        except Exception as exc:
            raise ValueError("坐标必须是整数") from exc

        return left, top, width, height

    def _validate_test_rect(self, left, top, width, height, image_w, image_h):
        if left < 0 or top < 0:
            raise ValueError("left 与 top 不能小于 0")
        if width <= 0 or height <= 0:
            raise ValueError("width 与 height 必须大于 0")
        if left + width > image_w or top + height > image_h:
            raise ValueError(
                f"坐标越界：选框范围不能超过当前图片分辨率 {image_w}*{image_h}"
            )

    def _on_test_coord(self, text):
        image = self._controller.get_current_image()
        if image is None:
            messagebox.showwarning("无法测试", "请先加载图片后再执行坐标测试")
            return

        try:
            left, top, width, height = self._parse_test_rect(text)
            self._validate_test_rect(left, top, width, height, image.width, image.height)
        except ValueError as exc:
            messagebox.showerror("坐标无效", str(exc))
            return

        ok = self._canvas.set_selection_rect(left, top, width, height, notify=True)
        if not ok:
            messagebox.showerror("坐标无效", "坐标无法应用到当前图片，请检查输入")

    def _on_selection(self, left, top, width, height):
        image = self._controller.get_current_image()
        if image is None:
            return
        cropped = crop_image(image, left, top, width, height)
        self._right.update_selection(left, top, width, height, cropped)

    def _on_view_changed(self, image_w, image_h, scale):
        if image_w is None or image_h is None:
            self._view_info_var.set("分辨率: - | 缩放: 100%")
            return
        zoom_percent = int(round(scale * 100))
        self._view_info_var.set(f"分辨率: {image_w}*{image_h} | 缩放: {zoom_percent}%")
