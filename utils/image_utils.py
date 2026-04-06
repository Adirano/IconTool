from PIL import Image

try:
    _RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    _RESAMPLE = Image.LANCZOS


def load_image_from_file(path):
    return Image.open(path).convert("RGBA")


def crop_image(image, left, top, width, height):
    return image.crop((left, top, left + width, top + height))


def resize_to_fit(image, max_w, max_h):
    w, h = image.size
    if w <= max_w and h <= max_h:
        return image
    ratio = min(max_w / w, max_h / h)
    return image.resize((int(w * ratio), int(h * ratio)), _RESAMPLE)
