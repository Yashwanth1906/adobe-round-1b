

# Adobe Hackathon - Round 1B: Persona-Based Document Intelligence

## Challenge Goal

Given a persona and their task, automatically analyze a set of PDFs (3–10) and extract:
- Most relevant sections with ranked importance
- Sub-sections with refined summaries

## Use Case Example

Persona: Investment Analyst  
Job-to-be-done: "Analyze revenue trends, R&D investments, and market positioning strategies."  
Input: 3 tech company financial reports  
→ Output: Structured JSON with most relevant sections/subsections, ranked by importance.

## Approach Overview

We integrate structured parsing from Round 1A with semantic vector search and lightweight LLM-based summarization:

### 🔹 1. PDF Preprocessing
- Reuse Round 1A extractor to get:
  - Document title, headings (H1–H3), associated content

### 🔹 2. Vector Embedding
- Embed each heading’s text + content using Sentence Transformers
- Embed persona and job query

### 🔹 3. Semantic Matching
- Use cosine similarity to rank sections based on:
  - Relevance to persona and job
  - Combined query score

### 🔹 4. Refined Summarization
- For top-matching content blocks, use a small LLM (<1GB) like `phi-2` or `tiny-llama` to generate:
  - Clean, human-readable section summaries
  - Top-level analysis

### 🔹 5. JSON Output

```json
{
  "metadata": {
    "documents": [...],
    "persona": "...",
    "job_to_be_done": "...",
    "timestamp": "..."
  },
  "section_rankings": [
    {
      "document": "xyz.pdf",
      "page": 12,
      "section_title": "Revenue Analysis",
      "importance_rank": 1
    },
    ...
  ],
  "subsection_analysis": [
    {
      "document": "xyz.pdf",
      "page": 12,
      "refined_text": "Company revenue increased by 18% YoY...",
      "section_title": "Revenue Analysis"
    }
  ]
}
