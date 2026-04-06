import json


def normalize_rect(x1, y1, x2, y2):
    """将任意两点坐标规范化为 (left, top, width, height)"""
    left = int(min(x1, x2))
    top = int(min(y1, y2))
    right = int(max(x1, x2))
    bottom = int(max(y1, y2))
    return left, top, right - left, bottom - top


def rect_to_json_str(left, top, width, height):
    d = {"left": left, "top": top, "width": width, "height": height}
    return json.dumps(d, ensure_ascii=False)
