import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import ImageTk

from config import RIGHT_PANEL_WIDTH, PREVIEW_MAX_SIZE
from utils.coordinate_utils import rect_to_json_str
from utils.image_utils import resize_to_fit


class RightPanel(tk.Frame):
    """右侧信息面板：坐标显示、一键复制、选区预览、保存按钮"""

    def __init__(self, parent):
        super().__init__(parent, width=RIGHT_PANEL_WIDTH, bg="#f5f5f5")
        self.pack_propagate(False)
        self._cropped_image = None
        self._photo_image = None
        self._build_ui()

    # ------------------------------------------------------------------
    # 构建 UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        H_PAD = {"padx": 14}

        # ---- 坐标信息区 ----
        tk.Label(
            self, text="选区坐标",
            font=("Microsoft YaHei", 11, "bold"),
            bg="#f5f5f5", fg="#333333", anchor="w",
        ).pack(fill=tk.X, padx=14, pady=(14, 2))

        self._coord_text = tk.Text(
            self, height=3,
            font=("Consolas", 10),
            bg="#ffffff", fg="#333333",
            relief=tk.SOLID, bd=1,
            state=tk.DISABLED,
            wrap=tk.NONE,
        )
        self._coord_text.pack(fill=tk.X, padx=14, pady=(0, 6))

        self._copy_btn = ttk.Button(
            self, text="一键复制坐标",
            command=self._copy_coords,
            state=tk.DISABLED,
        )
        self._copy_btn.pack(fill=tk.X, padx=14, pady=(0, 10))

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=14)

        # ---- 选区预览区 ----
        tk.Label(
            self, text="选区预览",
            font=("Microsoft YaHei", 11, "bold"),
            bg="#f5f5f5", fg="#333333", anchor="w",
        ).pack(fill=tk.X, padx=14, pady=(10, 2))

        # 占位框（无选区时显示）
        self._placeholder_frame = tk.Frame(self, bg="#dddddd", height=80)
        self._placeholder_frame.pack(fill=tk.X, padx=14, pady=(0, 6))
        self._placeholder_frame.pack_propagate(False)
        tk.Label(
            self._placeholder_frame, text="暂无选区",
            bg="#dddddd", fg="#999999",
            font=("Microsoft YaHei", 10),
        ).pack(expand=True)

        # 实际预览 Canvas（加载选区后替换占位框）
        self._preview_canvas = tk.Canvas(
            self, bg="#dddddd", highlightthickness=0,
        )

        self._save_btn = ttk.Button(
            self, text="保存选区图片 (PNG)",
            command=self._save_image,
            state=tk.DISABLED,
        )
        self._save_btn.pack(fill=tk.X, padx=14, pady=(0, 14))

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------
    def update_selection(self, left, top, width, height, cropped_image):
        self._cropped_image = cropped_image

        # 更新坐标文字
        coord_str = rect_to_json_str(left, top, width, height)
        self._coord_text.config(state=tk.NORMAL)
        self._coord_text.delete("1.0", tk.END)
        self._coord_text.insert("1.0", coord_str)
        self._coord_text.config(state=tk.DISABLED)

        # 更新预览图
        self._update_preview(cropped_image)

        # 启用按钮
        self._copy_btn.config(state=tk.NORMAL, text="一键复制坐标")
        self._save_btn.config(state=tk.NORMAL)

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------
    def _update_preview(self, image):
        display = resize_to_fit(image, PREVIEW_MAX_SIZE, PREVIEW_MAX_SIZE)
        self._photo_image = ImageTk.PhotoImage(display)

        # 隐藏占位框，显示预览 canvas
        self._placeholder_frame.pack_forget()
        self._save_btn.pack_forget()

        self._preview_canvas.config(width=display.width, height=display.height)
        self._preview_canvas.delete("all")
        self._preview_canvas.create_image(0, 0, anchor=tk.NW, image=self._photo_image)
        self._preview_canvas.pack(padx=14, pady=(0, 6))

        self._save_btn.pack(fill=tk.X, padx=14, pady=(0, 14))

    def _copy_coords(self):
        text = self._coord_text.get("1.0", tk.END).strip()
        self.clipboard_clear()
        self.clipboard_append(text)
        self._copy_btn.config(text="已复制!")
        self.after(1500, lambda: self._copy_btn.config(text="一键复制坐标"))

    def _save_image(self):
        if self._cropped_image is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG 图片", "*.png"), ("所有文件", "*.*")],
            title="保存选区图片",
        )
        if path:
            self._cropped_image.save(path, "PNG")
            messagebox.showinfo("保存成功", f"选区图片已保存至：\n{path}")
