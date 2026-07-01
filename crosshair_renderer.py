import colorsys
import math
from typing import Any, Mapping, Optional, Tuple

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover - runtime dependency is required by the app build.
    Image = None
    ImageDraw = None


def _get(settings: Any, key: str, default: Any = None) -> Any:
    if hasattr(settings, "get"):
        return settings.get(key, default)
    if isinstance(settings, Mapping):
        return settings.get(key, default)
    return default


def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
    r, g, b = colorsys.hsv_to_rgb(h / 360.0, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


def hex_to_rgb(value: str) -> Tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def current_color(settings: Any, hue: float = 0, dynamic_x: Optional[int] = None) -> Tuple[int, int, int]:
    if _get(settings, "rainbow_mode", False):
        return hsv_to_rgb(hue, 1.0, 1.0)
    if _get(settings, "dynamic_color", False):
        screen_w = _get(settings, "screen_width", 1920)
        if dynamic_x is None:
            dynamic_x = int(screen_w / 2)
        if screen_w > 0:
            return hsv_to_rgb((dynamic_x / screen_w) * 360, 1.0, 1.0)
    return hex_to_rgb(_get(settings, "color", "#00FF00"))


def opacity_byte(settings: Any) -> int:
    opacity = int(float(_get(settings, "opacity", 1.0)) * 255)
    return max(0, min(255, opacity))


def render_crosshair_image(
    settings: Any,
    size: int = 512,
    hue: float = 0,
    dynamic_x: Optional[int] = None,
    apply_opacity: bool = False,
):
    if Image is None:
        return None
    size = int(size)
    if size <= 0:
        return None

    full_alpha = 255
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2

    custom_pixels = _get(settings, "custom_pixels", [])
    if _get(settings, "pixel_perfect", False) and custom_pixels:
        for px, py, color_hex in custom_pixels:
            if _get(settings, "rainbow_mode", False):
                dist = abs(px) + abs(py)
                rgb = hsv_to_rgb((hue + dist * 10) % 360, 1.0, 1.0)
            else:
                rgb = hex_to_rgb(color_hex)
            ax = cx + int(px)
            ay = cy + int(py)
            if 0 <= ax < size and 0 <= ay < size:
                draw.point((ax, ay), fill=rgb + (full_alpha,))
    else:
        arm_size = int(_get(settings, "size", 20.0))
        thickness = int(_get(settings, "thickness", 2.0))
        gap = int(_get(settings, "gap", 4.0))
        fill_color = current_color(settings, hue=hue, dynamic_x=dynamic_x) + (full_alpha,)

        outline_enabled = _get(settings, "outline_enabled", False)
        outline_width = int(_get(settings, "outline_width", 1.0))
        outline_color = hex_to_rgb(_get(settings, "outline_color", "#000000")) + (full_alpha,)

        inner = gap
        outer = gap + arm_size
        max_reach = size // 2
        if outer > max_reach:
            outer = max_reach
            if inner > outer:
                inner = outer

        thickness_half = thickness // 2
        perp_start = -thickness_half
        perp_end = perp_start + thickness - 1

        def draw_box(x0, y0, x1, y1):
            if x0 > x1:
                x0, x1 = x1, x0
            if y0 > y1:
                y0, y1 = y1, y0
            if outline_enabled and outline_width > 0:
                draw.rectangle([x0 - outline_width, y0 - outline_width, x1 + outline_width, y1 + outline_width], fill=outline_color)
            draw.rectangle([x0, y0, x1, y1], fill=fill_color)

        if outer > inner:
            draw_box(cx + perp_start, cy - outer, cx + perp_end, cy - inner)
            draw_box(cx + perp_start, cy + inner, cx + perp_end, cy + outer)
            draw_box(cx - outer, cy + perp_start, cx - inner, cy + perp_end)
            draw_box(cx + inner, cy + perp_start, cx + outer, cy + perp_end)

        if _get(settings, "center_dot", False):
            dot_size = int(_get(settings, "center_dot_size", 2.0))
            if _get(settings, "rainbow_mode", False):
                dot_color = hsv_to_rgb((hue + 180) % 360, 1.0, 1.0)
            else:
                dot_color = hex_to_rgb(_get(settings, "center_dot_color", "#FF0000"))
            dot_fill = dot_color + (full_alpha,)
            radius = dot_size // 2
            x0 = cx - radius
            y0 = cy - radius
            x1 = x0 + dot_size - 1
            y1 = y0 + dot_size - 1
            if outline_enabled and outline_width > 0:
                draw.ellipse([x0 - outline_width, y0 - outline_width, x1 + outline_width, y1 + outline_width], fill=outline_color)
            draw.ellipse([x0, y0, x1, y1], fill=dot_fill)

    if apply_opacity:
        alpha = opacity_byte(settings)
        if alpha < 255:
            r, g, b, a = img.split()
            a = a.point(lambda value: int(value * alpha / 255))
            img = Image.merge("RGBA", (r, g, b, a))
    return img


def _padded_bbox(bbox, image_size: Tuple[int, int], scale: float = 1.05):
    left, top, right, bottom = bbox
    width = max(1, right - left)
    height = max(1, bottom - top)
    target_width = max(width, int(math.ceil(width * scale)))
    target_height = max(height, int(math.ceil(height * scale)))
    center_x = (left + right) / 2
    center_y = (top + bottom) / 2

    crop_left = int(math.floor(center_x - target_width / 2))
    crop_top = int(math.floor(center_y - target_height / 2))
    crop_right = crop_left + target_width
    crop_bottom = crop_top + target_height

    img_width, img_height = image_size
    if crop_left < 0:
        crop_right -= crop_left
        crop_left = 0
    if crop_top < 0:
        crop_bottom -= crop_top
        crop_top = 0
    if crop_right > img_width:
        crop_left -= crop_right - img_width
        crop_right = img_width
    if crop_bottom > img_height:
        crop_top -= crop_bottom - img_height
        crop_bottom = img_height

    crop_left = max(0, crop_left)
    crop_top = max(0, crop_top)
    return crop_left, crop_top, crop_right, crop_bottom


def render_crosshair_preview_image(
    settings: Any,
    size: int = 512,
    hue: float = 0,
    dynamic_x: Optional[int] = None,
    apply_opacity: bool = True,
    padding_scale: float = 1.05,
):
    img = render_crosshair_image(
        settings,
        size=size,
        hue=hue,
        dynamic_x=dynamic_x,
        apply_opacity=apply_opacity,
    )
    if img is None:
        return None, (0, 0), (0, 0)

    alpha_bbox = img.getchannel("A").getbbox()
    if alpha_bbox is None:
        empty = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        return empty, (0, 0), (1, 1)

    frame_bbox = _padded_bbox(alpha_bbox, img.size, padding_scale)
    cropped = img.crop(frame_bbox)
    crosshair_size = (alpha_bbox[2] - alpha_bbox[0], alpha_bbox[3] - alpha_bbox[1])
    return cropped, crosshair_size, cropped.size


def rgba_to_bgra_bytes(img) -> bytes:
    r, g, b, a = img.split()
    return Image.merge("RGBA", (b, g, r, a)).tobytes()


def render_crosshair_bgra(settings: Any, size: int = 512, hue: float = 0, dynamic_x: Optional[int] = None) -> Optional[bytes]:
    img = render_crosshair_image(settings, size=size, hue=hue, dynamic_x=dynamic_x, apply_opacity=False)
    if img is None:
        return None
    return rgba_to_bgra_bytes(img)
