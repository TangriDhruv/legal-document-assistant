# backend/document_handler.py
"""
Document processing module using python-docx
FIXED: Properly replaces placeholders while preserving formatting
"""

import re
from typing import List, Dict
from docx import Document
from docx.shared import RGBColor, Pt
from docx.enum.text import WD_COLOR_INDEX


def extract_document_text(docx_path: str) -> str:
    """
    Extract plain text from .docx file
    
    Args:
        docx_path: Path to .docx file
        
    Returns:
        Plain text from all paragraphs
    """
    doc = Document(docx_path)
    text_parts = []
    
    # Extract from paragraphs
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text_parts.append(paragraph.text)
    
    # Extract from tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    text_parts.append(cell.text)
    
    return "\n".join(text_parts)


def find_placeholders(text: str) -> List[Dict]:
    """
    Find all [Bracketed] placeholders in document text
    
    Args:
        text: Document text to search
        
    Returns:
        List of placeholder dictionaries with name, context, etc.
    """
    pattern = r'\[([^\]]+)\]'
    matches = re.finditer(pattern, text)
    
    placeholders = []
    seen = set()
    
    for match in matches:
        placeholder_name = match.group(1).strip()
        
        # Skip duplicates
        if placeholder_name in seen:
            continue
        seen.add(placeholder_name)
        
        start, end = match.span()
        
        # Extract context (100 chars before and after)
        context_start = max(0, start - 100)
        context_end = min(len(text), end + 100)
        context = text[context_start:context_end].strip()
        
        placeholders.append({
            "name": placeholder_name,
            "context": context,
            "filled": False,
            "value": None,
            "type": "text",
            "description": f"Please provide: {placeholder_name.lower()}"
        })
    
    return placeholders


def fill_placeholders(
    docx_path: str, 
    values: Dict[str, str], 
    output_path: str
) -> None:
    """
    Replace [Placeholder] with actual values in .docx
    Preserves original formatting
    
    FIXED VERSION: Properly handles placeholder replacement
    
    Args:
        docx_path: Path to original .docx
        values: Dictionary of placeholder -> value mappings
                Keys MUST match exact placeholder names from document
        output_path: Path for completed .docx
    """
    
    print(f"\n{'='*70}")
    print(f"📄 FILL_PLACEHOLDERS starting...")
    print(f"Input file: {docx_path}")
    print(f"Values to fill: {values}")
    print(f"Output file: {output_path}")
    print(f"{'='*70}\n")
    
    doc = Document(docx_path)
    
    # Track what we've filled
    replacements_made = {placeholder: False for placeholder in values.keys()}
    
    def replace_in_paragraph(paragraph, values_dict):
        """Replace placeholders in a paragraph, handling split runs"""
        
        # Get combined text to check what's in this paragraph
        full_text = paragraph.text
        
        # Check which placeholders are in this paragraph
        placeholders_here = [
            (name, val) for name, val in values_dict.items() 
            if f"[{name}]" in full_text
        ]
        
        if not placeholders_here:
            return
        
        # Combine all run texts
        combined_text = "".join([run.text for run in paragraph.runs])
        
        # Replace all placeholders in the combined text
        for placeholder_name, replacement_value in placeholders_here:
            placeholder_str = f"[{placeholder_name}]"
            if placeholder_str in combined_text:
                combined_text = combined_text.replace(
                    placeholder_str, 
                    replacement_value or ""
                )
                replacements_made[placeholder_name] = True
                print(f"  ✓ Replaced [{placeholder_name}] in paragraph")
        
        # Clear existing runs and set new text
        for run in paragraph.runs:
            run.text = ""
        
        if paragraph.runs:
            paragraph.runs[0].text = combined_text
        else:
            paragraph.add_run(combined_text)
    
    # Replace in paragraphs
    print("🔄 Processing paragraphs...")
    for i, paragraph in enumerate(doc.paragraphs):
        if any(f"[{name}]" in paragraph.text for name in values.keys()):
            print(f"  Found placeholders in paragraph {i}")
            replace_in_paragraph(paragraph, values)
    
    # Replace in tables
    print("🔄 Processing tables...")
    for table_idx, table in enumerate(doc.tables):
        for row_idx, row in enumerate(table.rows):
            for cell_idx, cell in enumerate(row.cells):
                for para_idx, paragraph in enumerate(cell.paragraphs):
                    if any(f"[{name}]" in paragraph.text for name in values.keys()):
                        print(f"  Found placeholders in table[{table_idx}] row[{row_idx}] cell[{cell_idx}] para[{para_idx}]")
                        replace_in_paragraph(paragraph, values)
    
    # Save document
    doc.save(output_path)
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"✅ Document saved to: {output_path}")
    print(f"\nReplacement summary:")
    for placeholder_name, was_replaced in replacements_made.items():
        status = "✓ REPLACED" if was_replaced else "✗ NOT FOUND"
        print(f"  [{placeholder_name}]: {status}")
    print(f"{'='*70}\n")
    
    # Warn if nothing was replaced
    if not any(replacements_made.values()):
        print("⚠️  WARNING: No placeholders were replaced!")
        print("   Check that placeholder names in values match document exactly.")