# backend/main.py
"""
FastAPI application for Legal Document Assistant
OpenAI GPT-4 Mini + Langchain edition
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
        
        # Find placeholders
        placeholders = find_placeholders(document_text)
        
        # Analyze with OpenAI via Langchain
        analysis = await analyze_placeholders(document_text)
        
        # Merge LLM analysis with regex results
        for p in placeholders:
            llm_info = next(
                (x for x in analysis.get("placeholders", []) 
                 if x.get("name") == p["name"]),
                None
            )
            if llm_info:
                p["description"] = llm_info.get("description", p["description"])
                p["type"] = llm_info.get("type", "text")
        
        # Store session
        sessions[session_id] = {
            "file_path": file_path,
            "temp_dir": temp_dir,
            "original_filename": file.filename,
            "document_text": document_text,
            "placeholders": placeholders,
            "filled_values": {},
            "conversation_history": []
        }
        
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
    
    Args:
        - session_id: Session identifier from upload
        - message: User message
        - placeholders: Current placeholder state
    """
    
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session expired")
    
    session = sessions[request.session_id]
    
    try:
        # Get chat response from Langchain/OpenAI
        result = await chat_for_placeholders(
            request.message,
            session["placeholders"],
            session["conversation_history"]
        )
        
        # Update filled values with intelligent matching
        for placeholder_name, value in result.get("filled_values", {}).items():
            # Try exact match first
            matched = False
            for p in session["placeholders"]:
                if p["name"].lower().strip() == placeholder_name.lower().strip():
                    session["filled_values"][p["name"]] = value
                    p["filled"] = True
                    p["value"] = value
                    matched = True
                    break
            
            # If no exact match, try fuzzy matching (check if placeholder_name is contained in p["name"])
            if not matched:
                for p in session["placeholders"]:
                    if (placeholder_name.lower() in p["name"].lower() or 
                        p["name"].lower() in placeholder_name.lower()):
                        print(f"DEBUG: Fuzzy match found! '{p['name']}' <- '{value}'")
                        session["filled_values"][p["name"]] = value
                        p["filled"] = True
                        p["value"] = value
                        matched = True
                        break
            
            # Store with the LLM's key as well for logging
            if not matched:
                print(f"DEBUG: NO MATCH found for '{placeholder_name}'. Available placeholders:")
                for p in session["placeholders"]:
                    print(f"  - {p['name']} (filled: {p.get('filled', False)})")
                session["filled_values"][placeholder_name] = value
        
        return ChatResponse(
            assistant_message=result.get("assistant_message", ""),
            filled_values=result.get("filled_values", {}),
            placeholders=session["placeholders"],
            next_question=result.get("next_placeholder")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


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
        "total_count": len(session["placeholders"])
    }


@app.post("/download")
async def download_document(request: DownloadRequest):
    """
    Generate and download completed document
    
    Checks that all placeholders are filled before generating
    Expects session_id in request body
    """
    
    # Get session_id from request
    actual_session_id = request.session_id
    
    if not actual_session_id or actual_session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session expired or invalid")
    
    session = sessions[actual_session_id]
    
    # Check if all placeholders are filled
    unfilled = [p for p in session["placeholders"] if not p.get("filled")]
    if unfilled:
        
        raise HTTPException(
            status_code=400,
            detail=f"Please fill remaining fields: {', '.join(p['name'] for p in unfilled)}"
        )
    
    try:
        
        # Generate completed document
        output_path = f"{session['temp_dir']}/completed.docx"
        fill_placeholders(
            session["file_path"],
            session["filled_values"],
            output_path
        )
        
        
        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"completed_{session['original_filename']}"
        )
        
    except Exception as e:
       
        raise HTTPException(status_code=500, detail=f"Download error: {str(e)}")


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