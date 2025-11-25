# backend/llm_handler.py
"""
Langchain + OpenAI integration module
Uses Langchain for abstraction so you can easily switch models
Supports GPT-4 Mini but can be changed to other models
"""

import json
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from config import settings


# Initialize Langchain ChatOpenAI
# Easy to switch model: just change the model_name parameter
llm = ChatOpenAI(
    model_name=settings.openai_model,  # "gpt-4-mini" or any other OpenAI model
    temperature=settings.openai_temperature,
    max_tokens=settings.openai_max_tokens,
    api_key=settings.openai_api_key
)


async def analyze_placeholders(document_text: str) -> Dict[str, Any]:
    """
    Use OpenAI via Langchain to analyze placeholders
    Determines field types and provides descriptions
    
    Args:
        document_text: Text from the document
        
    Returns:
        Dict with placeholder analysis
    """
    
    
    try:
        # Call Langchain/OpenAI
        response = llm.invoke([
            SystemMessage(content="""You are a legal document expert. Analyze the document and identify all [bracketed placeholders].
For each placeholder, determine:
1. What type of information it needs
2. A helpful description

Return ONLY a valid JSON object (no markdown, no extra text) with this structure:
{{
  "placeholders": [
    {{"name": "placeholder name without brackets", "type": "text|currency|date", "description": "helpful description"}}
  ]
}}"""),
            HumanMessage(content=f"Analyze this document text (first 3000 chars):\n\n{document_text[:3000]}")
        ])
        
        response_text = response.content
        
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            return json.loads(json_str)
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
    except Exception as e:
        print(f"Error analyzing placeholders: {e}")
    
    # Fallback
    return {"placeholders": []}


async def chat_for_placeholders(
    message: str,
    placeholders: List[Dict],
    conversation_history: List[Dict]
) -> Dict[str, Any]:
    """
    Multi-turn conversation using Langchain for intelligent placeholder filling
    
    Args:
        message: User message
        placeholders: List of placeholder objects
        conversation_history: List of previous messages
        
    Returns:
        Dict with assistant response and filled values
    """
    
    # Get unfilled and filled placeholders
    unfilled = [p for p in placeholders if not p.get("filled")]
    filled = [p for p in placeholders if p.get("filled")]
    
    # Build placeholder list for prompt (fixed UTF-8 encoding)
    unfilled_list = "\n".join([
        f'"{p["name"]}" - {p.get("description", "Required field")}'
        for p in unfilled
    ])
    
    filled_list = "\n".join([
        f'"{p["name"]}" = "{p.get("value", "")}"'
        for p in filled
    ]) if filled else "None yet"
    
    # Build system prompt with clearer instructions
    system_prompt = f"""You are a helpful legal document assistant. Your job is to help users fill document placeholders with accurate information.

ALREADY FILLED PLACEHOLDERS:
{filled_list}

REMAINING PLACEHOLDERS TO FILL:
{unfilled_list}

CRITICAL INSTRUCTIONS:
1. When user provides information, identify which placeholder it's for
2. MUST use the EXACT placeholder name from the "REMAINING PLACEHOLDERS" list above
3. Extract the value they provided
4. Ask clarifying questions if ambiguous
5. Be conversational and helpful

IMPORTANT: When you extract values, copy the EXACT placeholder name from the list above. Do not modify or shorten names.

Always respond with ONLY valid JSON (no markdown, no extra text, no backticks):
{{
  "assistant_message": "Your conversational response",
  "filled_values": {{"EXACT_NAME": "the value they provided"}},
  "next_placeholder": "next placeholder name or null"
}}

EXAMPLE:
User: "The company is ABC Corp and investor is John Smith"
If "Company Name" and "Investor Name" are in the remaining placeholders:
{{
  "assistant_message": "Great! I've noted that the company is ABC Corp and the investor is John Smith. What's next?",
  "filled_values": {{"Company Name": "ABC Corp", "Investor Name": "John Smith"}},
  "next_placeholder": null
}}"""
    
    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": message
    })
    
    # Convert conversation history to Langchain format
    messages = [SystemMessage(content=system_prompt)]
    
    for msg in conversation_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    
    try:
        # Call Langchain/OpenAI
        response = llm.invoke(messages)
        response_text = response.content
        
        # Extract JSON
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
        else:
            result = {
                "assistant_message": response_text,
                "filled_values": {},
                "next_placeholder": None
            }
            
    except json.JSONDecodeError:
        result = {
            "assistant_message": response_text,
            "filled_values": {},
            "next_placeholder": None
        }
    except Exception as e:
        print(f"Error in chat: {e}")
        result = {
            "assistant_message": f"Error: {str(e)}",
            "filled_values": {},
            "next_placeholder": None
        }
    
    # Add assistant response to history
    conversation_history.append({
        "role": "assistant",
        "content": result.get("assistant_message", "")
    })
    
    return result


# Optional: Helper function to switch models at runtime
def set_model(model_name: str) -> ChatOpenAI:
    """
    Change the LLM model at runtime
    
    Usage:
        set_model("gpt-4-turbo")  # Switch to GPT-4 Turbo
        set_model("gpt-3.5-turbo")  # Switch to GPT-3.5 Turbo
    """
    global llm
    llm = ChatOpenAI(
        model_name=model_name,
        temperature=settings.openai_temperature,
        max_tokens=settings.openai_max_tokens,
        api_key=settings.openai_api_key
    )
    return llm