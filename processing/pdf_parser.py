import fitz
import json
from collections import defaultdict
import re

# --- Helper Functions (as you provided) ---
def normalize_font_size(size):
    return round(size, 1) if size else None

def round_coord(value, precision=1):
    return round(value, precision) if value is not None else None

def detect_line_case(text):
    if text.isupper():
        return "UPPER"
    elif text.istitle():
        return "TITLE"
    elif text.islower():
        return "LOWER"
    else:
        return "MIXED"

def has_special_prefix(text):
    text = text.strip()
    patterns = [
        r"^(\d+[\.\)])+",
        r"^[IVXLCDM]+\.",
        r"^[A-Z]\.",
        r"^[-–•:]",
        r"^(Section|Chapter|Article)\b"
    ]
    return any(re.match(p, text, re.IGNORECASE) for p in patterns)

def is_centered(x, page_width=595.0, tolerance=50):
    center = page_width / 2
    return abs(x - center) < tolerance

# --- Main Function ---
def extract_pdf_lines_cleaned_and_merged(pdf_path: str) -> list:
    """
    Parses a PDF file and extracts structured line-by-line data.
    Args:
        pdf_path: The file path to the PDF.
    Returns:
        A list of pages, each containing structured data about its lines.
    """
    doc = fitz.open(pdf_path)
    pages_data = []

    for page_num, page in enumerate(doc):
        y_line_map = defaultdict(list)
        try:
            blocks = page.get_text("dict")["blocks"]
        except Exception:
            continue # Skip page if text extraction fails

        for block in blocks:
            if block.get('type') != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue

                    y_key = round(span["bbox"][1], 1)
                    y_line_map[y_key].append({
                        "text": text,
                        "font_size": normalize_font_size(span.get("size")),
                        "font_name": span.get("font"),
                        "bold": "Bold" in span.get("font", ""),
                        "italic": "Italic" in span.get("font", "") or "Oblique" in span.get("font", ""),
                        "position_x": round(span["bbox"][0], 1),
                        "position_y": y_key,
                        "page_number": page_num + 1
                    })

        page_lines = []
        for y_key in sorted(y_line_map.keys()):
            line_spans = sorted(y_line_map[y_key], key=lambda s: s["position_x"])
            merged_text = " ".join([s["text"] for s in line_spans])
            font_sizes = [s["font_size"] for s in line_spans if s["font_size"] is not None]
            fonts = [s["font_name"] for s in line_spans if s["font_name"]]
            bold = any(s["bold"] for s in line_spans)
            italic = any(s["italic"] for s in line_spans)
            x = min([s["position_x"] for s in line_spans]) if line_spans else 0
            
            page_lines.append({
                "text": merged_text,
                "font_size": max(font_sizes) if font_sizes else None,
                "font_name": fonts[0] if fonts else None,
                "bold": bold,
                "italic": italic,
                "position_x": x,
                "position_y": y_key,
                "page_number": page_num + 1,
                "line_length": len(merged_text),
                "is_centered": is_centered(x),
                "line_case": detect_line_case(merged_text),
                "has_special_prefix": has_special_prefix(merged_text)
            })
        
        pages_data.append({
            "page_number": page_num + 1,
            "content": page_lines
        })
    
    doc.close()
    return pages_data
