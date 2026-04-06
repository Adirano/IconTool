# IconTool

一个基于 Python + Tkinter 的图片标注工具，支持从本地文件或剪贴板导入图片，鼠标框选区域并导出选区图像。

## 功能说明

- 导入图片
  - 从本地选择图片文件
  - `Ctrl+V` 从剪贴板粘贴图片
- 左侧画布交互
  - 鼠标滚轮缩放（以鼠标位置为中心）
  - 鼠标移动到边缘时自动平移画布，便于浏览未显示区域
  - 鼠标左键拖拽框选标注区域
- 右侧信息面板
  - 显示选区坐标（JSON 格式）
  - 一键复制坐标
  - 选区预览
  - 保存选区为 PNG
- 状态栏信息
  - 显示原图分辨率（`宽*高`）
  - 显示当前缩放百分比

## 环境与依赖

- 操作系统：Windows（推荐）
- Python：3.10+
- 依赖包：
  - `Pillow`
- 标准库（无需安装）：
  - `tkinter`

## 本地开发运行

### 1. 创建并激活虚拟环境（可选但推荐）

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

### 2. 安装依赖

```powershell
pip install pillow
```

### 3. 启动应用

```powershell
python main.py
```

## 编译构建 EXE

项目根目录已提供一键构建脚本 [build_exe.bat](build_exe.bat)。

### 方法一：双击构建（推荐）

- 在资源管理器中双击运行 `build_exe.bat`
- 构建完成后产物位于：`dist/IconTool.exe`

### 方法二：命令行构建

```cmd
build_exe.bat
```

脚本会自动执行以下步骤：

1. 优先使用项目内 `.venv` 的 Python（若不存在则使用系统 Python）
2. 安装/更新 `pyinstaller` 和 `pillow`
3. 清理旧的 `build/`、`dist/`、`*.spec`
4. 打包生成单文件 GUI 可执行程序 `IconTool.exe`

## 发布说明

- 可分发文件：`dist/IconTool.exe`
- 目标机器：Windows
- 一般情况下可直接拷贝到其他 Windows 电脑运行

## 目录结构

```text
IconTool/
  controllers/
  gui/
  utils/
  main.py
  config.py
  build_exe.bat
```

## 常见问题

- 剪贴板粘贴无图片：请先确认系统剪贴板中确实是图片数据。
- 双击构建脚本报错：
  - 检查 Python 是否安装并可用
  - 检查网络是否可访问 pip 源
  - 如果使用虚拟环境，确认 `.venv` 已创建
