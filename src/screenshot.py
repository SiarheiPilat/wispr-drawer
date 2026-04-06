import os
from datetime import datetime
from PIL import ImageGrab, Image, ImageDraw


def capture_screen() -> Image.Image:
    return ImageGrab.grab()


def composite_with_drawings(screenshot: Image.Image, lines: list) -> Image.Image:
    """Overlay red drawing lines onto the screenshot."""
    if not lines:
        return screenshot
    draw = ImageDraw.Draw(screenshot)
    for x1, y1, x2, y2 in lines:
        draw.line([(x1, y1), (x2, y2)], fill="red", width=3)
    return screenshot


def save_screenshot(image: Image.Image, project_dir: str) -> str:
    screenshots_dir = os.path.join(project_dir, "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filepath = os.path.join(screenshots_dir, f"{timestamp}.png")
    image.save(filepath, "PNG")
    return filepath
