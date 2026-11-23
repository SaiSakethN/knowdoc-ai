"""Generate a scanned-style PDF fixture for container OCR verification, not a user document."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

output = Path("artifacts/ocr")
output.mkdir(parents=True, exist_ok=True)
image = Image.new("RGB", (1800, 1200), "white")
font_path = Path("C:/Windows/Fonts/arial.ttf")
font = ImageFont.truetype(str(font_path), 64) if font_path.exists() else ImageFont.load_default(size=64)
draw = ImageDraw.Draw(image)
draw.text((100, 180), "KNOWDOC INDEXING GUIDE", fill="black", font=font)
draw.text((100, 340), "GIN indexes support text search.", fill="black", font=font)
document = canvas.Canvas(str(output / "scanned.pdf"), pagesize=(900, 600))
document.drawImage(ImageReader(image), 0, 0, width=900, height=600)
document.save()
print("Created image-only parser fixture: artifacts/ocr/scanned.pdf")
