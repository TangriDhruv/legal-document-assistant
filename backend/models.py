# backend/models.py
"""
Pydantic models for data validation
UPDATED: Added inferred_name and type fields
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class Placeholder(BaseModel):
    """Represents a [Placeholder] field in the document"""
    name: str = Field(..., description="Placeholder name without brackets")
    context: str = Field(..., description="Text surrounding the placeholder")
    before: Optional[str] = Field(default=None, description="Text before placeholder")
    after: Optional[str] = Field(default=None, description="Text after placeholder")
    filled: bool = Field(default=False, description="Whether placeholder has been filled")
    value: Optional[str] = Field(default=None, description="The filled value")
    type: Optional[str] = Field(default="text", description="Field type: text, date, currency, person_name, company_name, address, email, phone, number")
    description: Optional[str] = Field(default=None, description="User-friendly description")
    inferred_name: Optional[str] = Field(default=None, description="Name inferred from context (if different from name)")
    inference_confidence: Optional[float] = Field(default=None, description="Confidence score of inference (0-1)")


class DocumentMetadata(BaseModel):
    """Metadata about uploaded document"""
    filename: str
    total_placeholders: int
    filled_count: int = 0


class ChatRequest(BaseModel):
    """Request for chat endpoint"""
    session_id: str = Field(..., description="Session UUID")
    message: str = Field(..., description="User message")
    placeholders: List[Placeholder] = Field(default=[], description="Current placeholder state")


class ChatResponse(BaseModel):
    """Response from chat endpoint"""
    assistant_message: str = Field(..., description="AI response to user")
    filled_values: Dict[str, str] = Field(default={}, description="New values filled")
    placeholders: List[Placeholder] = Field(..., description="Updated placeholder list")
    next_question: Optional[str] = Field(default=None, description="Suggested next placeholder to fill")


class UploadResponse(BaseModel):
    """Response from upload endpoint"""
    session_id: str = Field(..., description="Unique session identifier")
    filename: str = Field(..., description="Uploaded filename")
    placeholders: List[Placeholder] = Field(..., description="Detected placeholders")


class StatusResponse(BaseModel):
    """Response from status endpoint"""
    session_id: str
    placeholders: List[Placeholder]
    progress: str = Field(..., description="e.g., '3/7'")
    completed: bool = Field(..., description="All placeholders filled?")


class DownloadRequest(BaseModel):
    """Request for download endpoint"""
    session_id: str = Field(..., description="Session UUID")
    placeholders: Optional[List[Placeholder]] = Field(default=None, description="Current placeholder state")