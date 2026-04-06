from PIL import ImageGrab


def get_image_from_clipboard():
    """从剪贴板获取图片，返回 PIL Image 或 None"""
    try:
        image = ImageGrab.grabclipboard()
        if image is not None:
            return image.convert("RGBA")
    except Exception:
        pass
    return None
