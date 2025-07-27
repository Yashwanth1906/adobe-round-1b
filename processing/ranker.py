import json
import os
import fitz
from sentence_transformers import SentenceTransformer, util
from datetime import datetime

# --- Helper Function for Text Extraction ---
def extract_text_for_sections(pdf_path, outline):
    doc = fitz.open(pdf_path)
    sections = []
    for i, heading in enumerate(outline):
        start_page_idx = heading["page"] - 1
        if 0 <= start_page_idx < len(doc):
            content = doc[start_page_idx].get_text("text")
        else:
            content = ""
        sections.append({
            "document_filename": os.path.basename(pdf_path),
            "section_title": heading["text"],
            "page": heading["page"],
            "text": content.strip()
        })
    doc.close()
    return sections

# --- Main Ranking Function ---
def run_persona_ranking(content_dir: str) -> dict:
    """
    Runs the persona-based ranking on the generated outlines.
    Args:
        content_dir: The path to the 'content' directory containing inputs.
    Returns:
        A dictionary containing the final ranked output.
    """
    # Define paths based on the content_dir
    pdf_dir = os.path.join(content_dir, 'pdfs')
    outline_dir = os.path.join(content_dir, 'parsed_outlines')
    input_json_path = os.path.join(content_dir, 'challenge1b_input.json')

    # Load inputs
    with open(input_json_path, 'r') as f:
        challenge_input = json.load(f)
    persona = challenge_input['persona']['role']
    job = challenge_input['job_to_be_done']['task']
    documents_metadata = challenge_input['documents']
    query = f"A {persona} is trying to {job}"

    # Initialize model
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Collect all sections
    all_sections = []
    for i, doc_meta in enumerate(documents_metadata):
        pdf_filename = doc_meta['filename']
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        outline_path = os.path.join(outline_dir, f"file{i}_outline.json")

        if not os.path.exists(outline_path):
            continue
            
        with open(outline_path, 'r') as f:
            outline_data = json.load(f).get("outline", [])
        
        clean_outline = [h for h in outline_data if len(h['text'].split()) > 1 and not h['text'].endswith(':')]
        extracted = extract_text_for_sections(pdf_path, clean_outline)
        all_sections.extend(extracted)

    # Perform ranking
    if not all_sections:
        return {}

    query_embedding = model.encode(query, convert_to_tensor=True)
    section_titles_to_embed = [section['section_title'] for section in all_sections]
    section_embeddings = model.encode(section_titles_to_embed, convert_to_tensor=True)
    similarities = util.pytorch_cos_sim(query_embedding, section_embeddings)[0].cpu().numpy()

    for i, section in enumerate(all_sections):
        section['score'] = float(similarities[i])
    globally_ranked_sections = sorted(all_sections, key=lambda x: x['score'], reverse=True)

    # Format output
    top_sections_for_output = []
    subsection_analysis_for_output = []
    used_documents = set()
    rank_counter = 1

    for section in globally_ranked_sections:
        if len(top_sections_for_output) >= 5:
            break
        if section['document_filename'] not in used_documents:
            used_documents.add(section['document_filename'])
            top_sections_for_output.append({
                "document": section['document_filename'],
                "section_title": section['section_title'],
                "importance_rank": rank_counter,
                "page_number": section['page']
            })
            subsection_analysis_for_output.append({
                "document": section['document_filename'],
                "refined_text": section['text'],
                "page_number": section['page']
            })
            rank_counter += 1

    final_output = {
        "metadata": {
            "input_documents": [doc['filename'] for doc in documents_metadata],
            "persona": persona,
            "job_to_be_done": job,
            "processing_timestamp": datetime.utcnow().isoformat()
        },
        "extracted_sections": top_sections_for_output,
        "subsection_analysis": subsection_analysis_for_output
    }
    
    return final_output
