# backend/main.py
"""
FastAPI application for Legal Document Assistant
Fixed version: Properly tracks placeholder filling and handles downloads
"""

import os
import uuid
from typing import Dict
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models import ChatRequest, ChatResponse, UploadResponse, StatusResponse, Placeholder, DownloadRequest
from document_handler import extract_document_text, find_placeholders, fill_placeholders
from llm_handler import analyze_placeholders, chat_for_placeholders
from config import settings

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Legal Document Assistant",
    description="Upload documents and fill placeholders with AI assistance",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage
sessions: Dict[str, Dict] = {}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "model": settings.openai_model,
        "service": "Legal Document Assistant"
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and parse a .docx file
    
    Returns:
        - session_id: Unique session identifier
        - filename: Uploaded filename
        - placeholders: List of detected placeholders
    """
    
    # Validate file type
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="Only .docx files supported")
    
    # Validate file size
    if file.size and file.size > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large (max {settings.max_file_size_mb}MB)"
        )
    
    # Create session
    session_id = str(uuid.uuid4())
    temp_dir = f"/tmp/docassist_{session_id}"
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Save file
        file_path = f"{temp_dir}/{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Extract text
        document_text = extract_document_text(file_path)
        
        # Find placeholders (EXACT NAMES FROM DOCUMENT)
        placeholders = find_placeholders(document_text)
        
        # Generate initial message
        placeholders_str = ", ".join([p["name"] for p in placeholders[:5]])
        more = f" and {len(placeholders) - 5} more" if len(placeholders) > 5 else ""
        
        initial_message = f"""I've loaded your document "{file.filename}". 

I found {len(placeholders)} fields that need to be filled:
{placeholders_str}{more}

You can provide information for these fields one at a time, or all together. How would you like to proceed?"""
        
        # Store session with EXACT placeholder names
        sessions[session_id] = {
            "file_path": file_path,
            "temp_dir": temp_dir,
            "original_filename": file.filename,
            "document_text": document_text,
            "placeholders": placeholders,  # EXACT names from document
            "filled_values": {},  # Will be filled with exact names
            "conversation_history": []
        }
        
        print(f"✓ Uploaded document with {len(placeholders)} placeholders:")
        for p in placeholders:
            print(f"  - [{p['name']}]")
        
        return UploadResponse(
            session_id=session_id,
            filename=file.filename,
            placeholders=placeholders
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Handle chat message for filling placeholders
    
    FIX: Properly updates placeholders list with exact names
    """
    
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session expired")
    
    session = sessions[request.session_id]
    
    try:
        # Get chat response from LLM
        result = await chat_for_placeholders(
            request.message,
            session["placeholders"],
            session["conversation_history"]
        )
        
        # CRITICAL FIX: Update placeholders with exact names from filled_values
        filled_values = result.get("filled_values", {})
        
        print(f"\n📝 Chat response filled_values: {filled_values}")
        
        # Update session placeholders AND filled_values with exact names
        for field_name, value in filled_values.items():
            # Find the exact placeholder in our list
            for p in session["placeholders"]:
                if p["name"].lower() == field_name.lower():
                    # Update the placeholder object
                    p["filled"] = True
                    p["value"] = value
                    
                    # Store with EXACT placeholder name
                    session["filled_values"][p["name"]] = value
                    
                    print(f"✓ UPDATED: [{p['name']}] = '{value}'")
                    break
            else:
                # If no exact match found, try the field name as-is
                # This shouldn't happen if LLM is working correctly
                session["filled_values"][field_name] = value
                print(f"⚠️  No exact match for '{field_name}', storing as-is")
        
        # Log filled count
        filled_count = sum(1 for p in session["placeholders"] if p.get("filled"))
        total_count = len(session["placeholders"])
        print(f"📊 Progress: {filled_count}/{total_count} fields filled")
        
        return ChatResponse(
            assistant_message=result.get("assistant_message", ""),
            filled_values=session["filled_values"],  # Return all filled values
            placeholders=session["placeholders"],    # Return updated placeholders
            next_question=result.get("next_placeholder")
        )
        
    except Exception as e:
        print(f"❌ Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.post("/download")
async def download_document(request: DownloadRequest):
    """
    Generate and download completed document
    
    FIX: Uses session["filled_values"] with EXACT placeholder names
    """
    
    session_id = request.session_id
    
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session expired or invalid")
    
    session = sessions[session_id]
    
    # Check if all placeholders are filled
    unfilled = [p for p in session["placeholders"] if not p.get("filled")]
    if unfilled:
        unfilled_names = ", ".join([p["name"] for p in unfilled])
        raise HTTPException(
            status_code=400,
            detail=f"Please fill remaining fields: {unfilled_names}"
        )
    
    try:
        print(f"\n🔄 Downloading document...")
        print(f"File path: {session['file_path']}")
        print(f"Filled values: {session['filled_values']}")
        
        # Generate completed document
        output_path = f"{session['temp_dir']}/completed.docx"
        
        # CRITICAL: Pass filled_values with EXACT placeholder names
        fill_placeholders(
            session["file_path"],
            session["filled_values"],  # Has exact names as keys
            output_path
        )
        
        print(f"✓ Document completed: {output_path}")
        
        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"completed_{session['original_filename']}"
        )
        
    except Exception as e:
        print(f"❌ Download error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download error: {str(e)}")


@app.get("/debug/{session_id}")
async def debug_session(session_id: str):
    """Debug endpoint to see current session state"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    return {
        "session_id": session_id,
        "filename": session["original_filename"],
        "placeholders": session["placeholders"],
        "filled_values": session["filled_values"],
        "conversation_history_length": len(session["conversation_history"]),
        "filled_count": sum(1 for p in session["placeholders"] if p.get("filled")),
        "total_count": len(session["placeholders"]),
        "unfilled_placeholders": [p["name"] for p in session["placeholders"] if not p.get("filled")]
    }


@app.get("/status/{session_id}", response_model=StatusResponse)
async def get_status(session_id: str):
    """Get current session status"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    placeholders = session["placeholders"]
    filled_count = sum(1 for p in placeholders if p.get("filled"))
    total_count = len(placeholders)
    
    return StatusResponse(
        session_id=session_id,
        placeholders=placeholders,
        progress=f"{filled_count}/{total_count}",
        completed=filled_count == total_count
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)