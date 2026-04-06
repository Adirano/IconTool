import tkinter as tk
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

        # 左侧画布（可伸缩）
        self._canvas = ImageCanvas(content, on_selection_callback=self._on_selection)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 分隔线
        ttk.Separator(content, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y)

        # 右侧面板（固定宽度）
        self._right = RightPanel(content)
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
        except Exception as exc:
            messagebox.showerror("打开失败", f"无法读取图片文件：\n{exc}")

    def _paste_clipboard(self):
        image = self._controller.load_from_clipboard()
        if image is not None:
            self._canvas.show_image(image)
        else:
            messagebox.showwarning("粘贴失败", "剪贴板中未检测到图片")

    def _on_selection(self, left, top, width, height):
        image = self._controller.get_current_image()
        if image is None:
            return
        cropped = crop_image(image, left, top, width, height)
        self._right.update_selection(left, top, width, height, cropped)
