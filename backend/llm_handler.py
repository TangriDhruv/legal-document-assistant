# backend/llm_handler.py
"""
SMART VERSION: Uses actual placeholder names from document
- Extract placeholders from document text
- Show them to user with descriptions
- When user provides value, match to ACTUAL placeholder name
- No name mismatch issues!
"""

import json
import re
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from config import settings

DEBUG = True

def debug_log(message: str, level: str = "INFO"):
    """Print debug messages"""
    if not DEBUG:
        return
    levels = {
        "INFO": "ℹ️ ",
        "SUCCESS": "✅ ",
        "WARNING": "⚠️ ",
        "ERROR": "❌ ",
        "DEBUG": "🔍 ",
        "LLM_CALL": "🤖 ",
        "LLM_RESPONSE": "💬 ",
        "JSON_PARSE": "📋 ",
        "EXTRACTION": "🎯 ",
        "MATCH": "🎯 "
    }
    prefix = levels.get(level, "→ ")
    print(f"{prefix} [LLM_HANDLER] {message}")


# Initialize with ultra-low temperature
llm = ChatOpenAI(
    model_name=settings.openai_model,
    temperature=0,
    max_tokens=settings.openai_max_tokens,
    api_key=settings.openai_api_key,
    top_p=0.1,
    frequency_penalty=2.0,
    presence_penalty=2.0
)

debug_log("ChatOpenAI initialized with temperature=0, top_p=0.1", "SUCCESS")


def find_matching_placeholder(
    user_input: str,
    unfilled_placeholders: List[Dict],
    context_from_doc: str = ""
) -> Optional[Dict]:
    """
    SMART MATCHING: Uses LLM to find which placeholder the user is talking about
    
    Examples:
      User: "The company is XYZ"
      Unfilled: ["Company Name", "Investor Name", "Date"]
      Returns: {"name": "Company Name", "context": "..."}
      
      User: "Date is 2025-05-10"
      Returns: {"name": "Date of Safe", "context": "..."}
    """
    
    if not unfilled_placeholders:
        return None
    
    # Single unfilled placeholder? Probably that one
    if len(unfilled_placeholders) == 1:
        debug_log(f"Only one unfilled: {unfilled_placeholders[0]['name']}", "MATCH")
        return unfilled_placeholders[0]
    
    # Multiple placeholders - use LLM to match context
    placeholders_list = "\n".join([
        f"- \"{p['name']}\": {p.get('description', 'Field')}"
        for p in unfilled_placeholders
    ])
    
    system_prompt = f"""You are a placeholder matcher. Given user input, identify which placeholder field they're describing.

Available unfilled fields:
{placeholders_list}

User input: "{user_input}"

Respond with ONLY the exact placeholder name they're describing (from the list above).
Respond with ONLY the name in quotes, nothing else.

Example responses:
"Company Name"
"Investor Name"
"Date of Safe"
"""
    
    try:
        debug_log(f"LLM matching input to placeholder...", "MATCH")
        
        response = llm.invoke([
            SystemMessage(content=system_prompt)
        ])
        
        matched_name = response.content.strip().strip('"').strip()
        debug_log(f"LLM matched to: {matched_name}", "MATCH")
        
        # Verify match is in our list
        for p in unfilled_placeholders:
            if p['name'].lower() == matched_name.lower():
                debug_log(f"✓ Verified match: {p['name']}", "MATCH")
                return p
        
        # If no exact match, return best guess (first unfilled)
        debug_log(f"⚠️ No exact match found, using first unfilled", "WARNING")
        return unfilled_placeholders[0]
        
    except Exception as e:
        debug_log(f"Matching error: {str(e)}, using first unfilled", "WARNING")
        return unfilled_placeholders[0]


async def analyze_placeholders(document_text: str) -> Dict[str, Any]:
    """Use OpenAI to analyze and describe placeholders"""
    
    debug_log("ANALYZE_PLACEHOLDERS CALLED", "LLM_CALL")
    
    try:
        system_prompt = """You are a legal document expert. Analyze [bracketed placeholders] and provide helpful descriptions.

Your response must be ONLY valid JSON (no exceptions):
{
  "placeholders": [
    {
      "name": "placeholder_name_without_brackets",
      "type": "text|currency|date|person|company|address",
      "description": "What information is needed here?"
    }
  ]
}

Rules:
- Use EXACT placeholder names from document
- Provide helpful, specific descriptions
- ENTIRE response is JSON only
- Start with { end with }"""
        
        user_message = f"Analyze these placeholders:\n\n{document_text[:2000]}"
        
        debug_log("Sending to LLM for analysis...", "LLM_CALL")
        
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])
        
        response_text = response.content
        debug_log(f"LLM response: {len(response_text)} chars", "LLM_RESPONSE")
        
        # Extract JSON
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            debug_log(f"✓ Placeholders analyzed", "SUCCESS")
            return result
        
    except Exception as e:
        debug_log(f"Error analyzing placeholders: {str(e)}", "ERROR")
    
    return {"placeholders": []}


async def chat_for_placeholders(
    message: str,
    placeholders: List[Dict],
    conversation_history: List[Dict]
) -> Dict[str, Any]:
    """
    SMART VERSION:
    1. Identify which placeholder user is talking about (using LLM context matching)
    2. Send THAT exact placeholder name to LLM
    3. Get value filled
    4. Update with actual placeholder name from document
    """
    
    debug_log("=" * 80, "LLM_CALL")
    debug_log("CHAT_FOR_PLACEHOLDERS CALLED", "LLM_CALL")
    debug_log("=" * 80, "LLM_CALL")
    
    debug_log(f"User message: '{message}'", "DEBUG")
    
    # Get unfilled/filled
    unfilled = [p for p in placeholders if not p.get("filled")]
    filled = [p for p in placeholders if p.get("filled")]
    
    # SMART MATCHING: Figure out which placeholder they're talking about
    matched_placeholder = find_matching_placeholder(message, unfilled)
    
    if not matched_placeholder:
        debug_log("No unfilled placeholders remaining", "WARNING")
        return {
            "assistant_message": "All fields are filled!",
            "filled_values": {},
            "next_placeholder": None
        }
    
    # Build filled list
    filled_str = "\n".join([
        f'"{p["name"]}" = "{p.get("value", "")}"'
        for p in filled
    ]) or "None"
    
    # CRITICAL: Use EXACT placeholder names from document
    unfilled_str = "\n".join([f'"{p["name"]}"' for p in unfilled])
    
    system_prompt = f"""You are a document filling assistant. Extract values from user input and assign to the EXACT placeholder names provided.

FILLED FIELDS:
{filled_str}

UNFILLED FIELDS (use EXACT names):
{unfilled_str}

Current focus: "{matched_placeholder['name']}"
Description: {matched_placeholder.get('description', 'Field')}

USER SAID: "{message}"

═══════════════════════════════════════════════════════════════════════════════
TASK:
1. Extract the value user provided for "{matched_placeholder['name']}"
2. Return it with the EXACT placeholder name from above
3. Respond with ONLY valid JSON

MANDATORY JSON FORMAT (no exceptions):
{{
  "assistant_message": "Brief acknowledgment",
  "filled_values": {{"{matched_placeholder['name']}": "value_extracted"}},
  "next_placeholder": null
}}

CRITICAL RULES:
- Use the EXACT placeholder name: "{matched_placeholder['name']}"
- If they provided a value, include it in filled_values
- If no value, use empty: "filled_values": {{}}
- Your ENTIRE response is JSON
- Start with {{ end with }}
- NO plain text, NO explanations outside JSON

EXAMPLES:
User: "Company Name is ABC Corp"
{{"assistant_message": "Got it, company is ABC Corp.", "filled_values": {{"{matched_placeholder['name']}": "ABC Corp"}}, "next_placeholder": null}}

User: "What's next?"
{{"assistant_message": "Please provide the value", "filled_values": {{}}, "next_placeholder": null}}"""
    
    # Add to history
    conversation_history.append({
        "role": "user",
        "content": message
    })
    
    # Build messages
    messages = [SystemMessage(content=system_prompt)]
    
    for msg in conversation_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    
    debug_log(f"Calling LLM with matched placeholder: {matched_placeholder['name']}", "LLM_CALL")
    
    try:
        response = llm.invoke(messages)
        response_text = response.content
        
        debug_log(f"LLM response: {len(response_text)} chars", "LLM_RESPONSE")
        debug_log(f"\nFULL RESPONSE:\n{response_text}\n", "LLM_RESPONSE")
        
        # Extract JSON
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            debug_log(f"✓ JSON parsed successfully", "SUCCESS")
            
            # Ensure required fields exist
            if "assistant_message" not in result:
                result["assistant_message"] = "Got it"
            if "filled_values" not in result:
                result["filled_values"] = {}
            if "next_placeholder" not in result:
                result["next_placeholder"] = None
            
            # Log extracted values
            filled_values = result.get("filled_values", {})
            debug_log(f"Extracted {len(filled_values)} values", "EXTRACTION")
            for field_name, value in filled_values.items():
                debug_log(f"  '{field_name}' → '{value}'", "EXTRACTION")
        else:
            debug_log(f"❌ No JSON found in response", "ERROR")
            result = {
                "assistant_message": response_text[:200],
                "filled_values": {},
                "next_placeholder": None
            }
            
    except json.JSONDecodeError as e:
        debug_log(f"❌ JSON parse error: {str(e)}", "ERROR")
        result = {
            "assistant_message": "Error processing response",
            "filled_values": {},
            "next_placeholder": None
        }
    except Exception as e:
        debug_log(f"❌ Error: {str(e)}", "ERROR")
        result = {
            "assistant_message": "Error",
            "filled_values": {},
            "next_placeholder": None
        }
    
    # Add to history
    conversation_history.append({
        "role": "assistant",
        "content": result.get("assistant_message", "")
    })
    
    debug_log(f"Returning result", "SUCCESS")
    
    return result


def set_model(model_name: str) -> ChatOpenAI:
    """Change the LLM model at runtime"""
    global llm
    debug_log(f"Switching model to: {model_name}", "INFO")
    llm = ChatOpenAI(
        model_name=model_name,
        temperature=0,
        max_tokens=settings.openai_max_tokens,
        api_key=settings.openai_api_key,
        top_p=0.1,
        frequency_penalty=2.0,
        presence_penalty=2.0
    )
    return llm