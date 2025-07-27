import json
import re

# --- Helper Functions (as you provided) ---
def load_blocks(parsed_data):
    blocks = []
    for page in parsed_data:
        # Skip page 1 for heading extraction logic if needed, but often titles are there
        # if page["page_number"] == 1:
        #     continue
        for block in page["content"]:
            block = dict(block)
            block["page"] = page["page_number"]
            blocks.append(block)
    blocks.sort(key=lambda b: (b["page"], b["position_y"]))
    return blocks

def extract_title_from_page1(parsed_data):
    page1 = next((p for p in parsed_data if p["page_number"] == 1), None)
    if not page1:
        return ""
    blocks = page1["content"]
    blocks = sorted(blocks, key=lambda b: (-b.get("font_size", 0), b.get("position_y", 999)))
    for block in blocks:
        if block.get("text", "").strip():
            return block["text"].strip()
    return ""

def is_heading_like(block):
    text = block.get("text", "").strip()
    if not text or len(text) > 150:
        return False
    font_name = block.get("font_name", "").lower()
    bold = block.get("bold", False)
    font_size = block.get("font_size", 0)
    is_all_caps = text.isupper() and len(text) > 2
    is_title_case = text.istitle() and len(text.split()) > 1
    short = len(text.split()) <= 12
    no_punct_end = not text.endswith(('.', ',', ';'))

    score = 0
    if font_size >= 14: score += 2
    if bold or "bold" in font_name: score += 2
    if is_all_caps: score += 1
    if is_title_case: score += 1
    if short: score += 1
    if no_punct_end: score += 1
    
    return score >= 4

def get_font_sizes(blocks):
    heading_blocks = [b for b in blocks if is_heading_like(b)]
    font_sizes = {b["font_size"] for b in heading_blocks if b.get("font_size")}
    return sorted(list(font_sizes), reverse=True)

def find_headings(blocks, font_sizes, level=1, start_idx=0, end_idx=None, max_level=4):
    if end_idx is None:
        end_idx = len(blocks)
    if level > max_level or level > len(font_sizes):
        return []
    
    curr_size = font_sizes[level-1]
    indices = [i for i in range(start_idx, end_idx) if blocks[i].get("font_size") == curr_size and is_heading_like(blocks[i])]
    
    if not indices:
        return []
        
    outline = []
    for idx, i in enumerate(indices):
        outline.append({
            "level": f"H{level}",
            "text": blocks[i]["text"].strip(),
            "page": blocks[i]["page"]
        })
        next_i = indices[idx+1] if idx+1 < len(indices) else end_idx
        outline.extend(find_headings(blocks, font_sizes, level+1, i+1, next_i, max_level))
    return outline

# --- Main Function ---
def extract_outline(parsed_json_path: str, output_path: str):
    """
    Takes a parsed JSON file and generates a hierarchical outline.
    Args:
        parsed_json_path: Path to the intermediate JSON from the parser.
        output_path: Path to save the final outline JSON.
    """
    with open(parsed_json_path, 'r', encoding='utf-8') as f:
        parsed_data = json.load(f)
        
    blocks = load_blocks(parsed_data)
    if not blocks:
        result = {"title": "", "outline": []}
    else:
        font_sizes = get_font_sizes(blocks)
        outline = find_headings(blocks, font_sizes, max_level=4)
        title = extract_title_from_page1(parsed_data)
        result = {"title": title, "outline": outline}
        
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    print(f"✅ Outline saved to {output_path}")
