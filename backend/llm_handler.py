# backend/llm_handler.py
"""
UPDATED: Added context-based type inference for placeholders
- Uses surrounding text to infer what each placeholder should be
- Matches user input to correct field even with poor placeholder names
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
        "MATCH": "🎯 ",
        "INFERENCE": "🧠 "
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


def infer_placeholder_type(
    placeholder_name: str,
    before_text: str,
    after_text: str,
    full_context: str
) -> Dict[str, Any]:
    """
    NEW: Use LLM to infer what type of field this is
    based on surrounding context
    
    Examples:
      "dated [FIELD1]" → type: date
      "amount [XXX]" → type: currency
      "between [A] and [B]" → type: person_name
    """
    
    debug_log(f"Inferring type for placeholder: [{placeholder_name}]", "INFERENCE")
    
    system_prompt = """You are a document analysis expert. Analyze the context around a placeholder and infer what type of information should go there.

Based on surrounding text, determine:
1. Field type (date, currency, person_name, company_name, address, email, phone, number, text, other)
2. Inferred descriptive name for this field
3. A helpful description for the user

You MUST respond with ONLY valid JSON (no other text):
{
  "type": "date|currency|person_name|company_name|address|email|phone|number|text|other",
  "inferred_name": "Clear, descriptive name for this field",
  "description": "What information is needed here?",
  "confidence": 0.95,
  "reasoning": "Why you inferred this type"
}"""

    user_message = f"""Analyze this placeholder in context:

Before: ...{before_text}
Placeholder: [{placeholder_name}]
After: {after_text}...

Full context: ...{full_context}...

What type of field is this? Infer from context clues."""

    try:
        debug_log(f"Sending to LLM for type inference...", "LLM_CALL")
        
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])
        
        response_text = response.content
        debug_log(f"LLM inference response: {len(response_text)} chars", "LLM_RESPONSE")
        
        # Extract JSON
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            debug_log(f"✓ Inferred: {result.get('inferred_name', placeholder_name)} (type: {result.get('type')})", "SUCCESS")
            
            return {
                "type": result.get("type", "text"),
                "inferred_name": result.get("inferred_name", placeholder_name),
                "description": result.get("description", f"Please provide: {placeholder_name.lower()}"),
                "inference_confidence": result.get("confidence", 0.8),
                "reasoning": result.get("reasoning", "")
            }
        
    except json.JSONDecodeError as e:
        debug_log(f"❌ JSON parse error in inference: {str(e)}", "ERROR")
    except Exception as e:
        debug_log(f"❌ Inference error: {str(e)}", "ERROR")
    
    # Fallback
    debug_log(f"⚠️  Using fallback for [{placeholder_name}]", "WARNING")
    return {
        "type": "text",
        "inferred_name": placeholder_name,
        "description": f"Please provide: {placeholder_name.lower()}",
        "inference_confidence": 0.0,
        "reasoning": "Inference failed, using basic description"
    }


def find_matching_placeholder(
    user_input: str,
    unfilled_placeholders: List[Dict],
    context_from_doc: str = ""
) -> Optional[Dict]:
    """
    UPDATED: Use both placeholder name AND inferred type for matching
    
    Examples:
      User: "The company is XYZ"
      Unfilled: [
        {name: "FIELD1", inferred_name: "Company Name", type: "company_name"},
        {name: "FIELD2", inferred_name: "Date", type: "date"}
      ]
      Returns: FIELD1 (matched by type and meaning)
      
      User: "January 15, 2025"
      Returns: FIELD2 (matched by date type)
    """
    
    if not unfilled_placeholders:
        return None
    
    # Single unfilled placeholder? Probably that one
    if len(unfilled_placeholders) == 1:
        debug_log(f"Only one unfilled: {unfilled_placeholders[0].get('inferred_name', unfilled_placeholders[0]['name'])}", "MATCH")
        return unfilled_placeholders[0]
    
    # Multiple placeholders - use LLM to match
    placeholders_list = "\n".join([
        f"- \"{p.get('inferred_name', p['name'])}\" "
        f"(Type: {p.get('type', 'text')}, "
        f"Original: [{p['name']}]): "
        f"{p.get('description', 'Field')}"
        for p in unfilled_placeholders
    ])
    
    system_prompt = f"""You are a field matcher. Given user input, identify which placeholder field they're describing.
Match using:
1. Field TYPE (date, currency, person_name, etc.)
2. Meaning of the user's input
3. Context clues

Available unfilled fields:
{placeholders_list}

User input: "{user_input}"

Respond with ONLY the inferred field name (not original name) in quotes.
Example responses:
"Company Name"
"Agreement Date"
"Investment Amount"
"""
    
    try:
        debug_log(f"LLM matching input to placeholder (using types)...", "MATCH")
        
        response = llm.invoke([
            SystemMessage(content=system_prompt)
        ])
        
        matched_name = response.content.strip().strip('"').strip()
        debug_log(f"LLM matched to: {matched_name}", "MATCH")
        
        # Find by inferred_name first, then by name
        for p in unfilled_placeholders:
            inferred = p.get('inferred_name', p['name'])
            if inferred.lower() == matched_name.lower() or p['name'].lower() == matched_name.lower():
                debug_log(f"✓ Verified match: {p['name']} ({inferred})", "MATCH")
                return p
        
        # If no exact match, return best guess (first unfilled)
        debug_log(f"⚠️ No exact match found, using first unfilled", "WARNING")
        return unfilled_placeholders[0]
        
    except Exception as e:
        debug_log(f"Matching error: {str(e)}, using first unfilled", "WARNING")
        return unfilled_placeholders[0]


async def chat_for_placeholders(
    message: str,
    placeholders: List[Dict],
    conversation_history: List[Dict]
) -> Dict[str, Any]:
    """
    UPDATED: Use inferred types in matching
    
    Process:
    1. Identify which placeholder user is talking about (using types)
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
    
    # Smart matching using inferred types
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
        f'"{p.get("inferred_name", p["name"])}" = "{p.get("value", "")}"'
        for p in filled
    ]) or "None"
    
    # Use inferred names in prompts for clarity
    unfilled_str = "\n".join([
        f'"{p.get("inferred_name", p["name"])}" (Type: {p.get("type", "text")})'
        for p in unfilled
    ])
    
    matched_display_name = matched_placeholder.get("inferred_name", matched_placeholder["name"])
    matched_original_name = matched_placeholder["name"]
    
    system_prompt = f"""You are a document filling assistant. Extract values from user input and assign to the exact placeholder names provided.

FILLED FIELDS:
{filled_str}

UNFILLED FIELDS:
{unfilled_str}

Current focus: "{matched_display_name}"
Type: {matched_placeholder.get("type", "text")}
Description: {matched_placeholder.get("description", "Field")}
Original placeholder name: [{matched_original_name}]

USER SAID: "{message}"

═══════════════════════════════════════════════════════════════════════════════
TASK:
1. Extract the value user provided for "{matched_display_name}"
2. Return it with the EXACT original placeholder name: [{matched_original_name}]
3. Respond with ONLY valid JSON

MANDATORY JSON FORMAT:
{{
  "assistant_message": "Brief acknowledgment",
  "filled_values": {{"{matched_original_name}": "value_extracted"}},
  "next_placeholder": null
}}

CRITICAL RULES:
- Use the EXACT placeholder name: "{matched_original_name}"
- If they provided a value, include it
- If no value provided, use empty: "filled_values": {{}}
- Your ENTIRE response is JSON only
- Start with {{ end with }}

EXAMPLES:
User: "Company Name is ABC Corp"
{{"assistant_message": "Got it, company is ABC Corp.", "filled_values": {{"{matched_original_name}": "ABC Corp"}}, "next_placeholder": null}}

User: "What's next?"
{{"assistant_message": "Please provide the value for {matched_display_name}", "filled_values": {{}}, "next_placeholder": null}}"""
    
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
    
    debug_log(f"Calling LLM with matched placeholder: {matched_original_name} ({matched_display_name})", "LLM_CALL")
    
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