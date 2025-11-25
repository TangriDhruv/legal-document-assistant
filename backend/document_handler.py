# backend/document_handler.py
"""
Document processing module using python-docx
Handles extraction and manipulation of .docx files
"""

import re
from typing import List, Dict
from docx import Document


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
    
    Args:
        docx_path: Path to original .docx
        values: Dictionary of placeholder -> value mappings
        output_path: Path for completed .docx
    """
    doc = Document(docx_path)
    
    # Helper function to replace text in a paragraph while handling split runs
    def replace_text_in_paragraph(paragraph, placeholder_name, value):
        placeholder_text = f"[{placeholder_name}]"
        
        # Reconstruct paragraph text to check if placeholder exists
        full_text = paragraph.text
        
        if placeholder_text in full_text:
            # Handle the replacement by reconstructing runs
            # This is necessary because placeholders might span multiple runs
            
            # Combine all runs' text
            combined_text = "".join([run.text for run in paragraph.runs])
            
            if placeholder_text in combined_text:
                # Replace the placeholder in combined text
                new_text = combined_text.replace(placeholder_text, value or "")
                
                # Clear existing runs
                for run in paragraph.runs:
                    run.text = ""
                
                # Add the new text to the first run (or create one if no runs exist)
                if paragraph.runs:
                    paragraph.runs[0].text = new_text
                else:
                    paragraph.add_run(new_text)
    
    # Replace in paragraphs
    for paragraph in doc.paragraphs:
        for placeholder_name, value in values.items():
            replace_text_in_paragraph(paragraph, placeholder_name, value)
    
    # Replace in tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for placeholder_name, value in values.items():
                        replace_text_in_paragraph(paragraph, placeholder_name, value)
    
    # Save completed document
    doc.save(output_path)