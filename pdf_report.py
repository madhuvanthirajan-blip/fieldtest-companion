from pathlib import Path
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def create_pdf_report(record: dict, image_path: Path) -> Path:
    reports_dir = image_path.parent.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    output = reports_dir / f"{record['test_id']}_report.pdf"

    c = canvas.Canvas(str(output), pagesize=A4)
    W, H = A4

    # Header
    c.setFillColor(colors.HexColor("#0B1F33"))
    c.roundRect(35, H - 105, W - 70, 65, 14, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(52, H - 70, "FieldTest Companion")
    c.setFont("Helvetica", 9)
    c.drawString(52, H - 87, "Digital field-test prototype report")

    y = H - 135

    c.setFillColor(colors.HexColor("#222222"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(45, y, "PRESUMPTIVE RESULT")

    y -= 35
    result = record["classification"]

    if result == "POSITIVE":
        result_color = colors.HexColor("#C52D6B")
    elif result == "NEGATIVE":
        result_color = colors.HexColor("#718F18")
    else:
        result_color = colors.HexColor("#B27A00")

    c.setFillColor(result_color)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(45, y, result)

    c.setFillColor(colors.HexColor("#333333"))
    c.setFont("Helvetica", 11)
    c.drawString(45, y - 22, f"Confidence: {record['confidence']:.1f}%")

    # Image
    y -= 65
    if image_path.exists():
        try:
            img = ImageReader(str(image_path))
            iw, ih = img.getSize()
            max_w, max_h = W - 90, 220
            scale = min(max_w / iw, max_h / ih)
            dw, dh = iw * scale, ih * scale
            c.drawImage(
                img,
                45,
                y - dh,
                width=dw,
                height=dh,
                preserveAspectRatio=True,
                mask="auto",
            )
            y -= dh + 25
        except Exception:
            pass

    # Details
    c.setFillColor(colors.HexColor("#222222"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(45, y, "TEST DETAILS")
    y -= 20

    c.setFont("Helvetica", 9.5)

    rows = [
        ("Test ID", record["test_id"]),
        ("Operator ID", record["operator_id"]),
        ("Timestamp", record["timestamp_display"]),
    ]

    if record.get("latitude") is not None:
        rows.append(
            (
                "GPS",
                f"{record['latitude']:.6f}, {record['longitude']:.6f}"
            )
        )
    else:
        rows.append(("GPS", "Not available"))

    rows.extend([
        ("Calibration", record["calibration"]),
        ("Raw RGB", str(record["test_rgb_raw"])),
        ("Calibrated RGB", str(record["test_rgb_calibrated"])),
    ])

    for label, value in rows:
        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(45, y, f"{label}:")
        c.setFont("Helvetica", 9.5)
        c.drawString(145, y, str(value)[:85])
        y -= 16

    # Footer disclaimer
    c.setFillColor(colors.HexColor("#6A5312"))
    c.roundRect(45, 45, W - 90, 55, 8, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(57, 81, "IMPORTANT")
    c.setFont("Helvetica", 8)
    c.drawString(
        57, 67,
        "This is a presumptive field-test result and supporting digital record."
    )
    c.drawString(
        57, 55,
        "It does not replace laboratory confirmatory testing."
    )

    c.save()
    return output
