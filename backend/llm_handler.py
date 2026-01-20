# backend/llm_handler.py
"""
IMPROVED VERSION: Better placeholder matching and next placeholder prompting
- Smarter matching using semantic analysis
- Explicit next placeholder with details
- Better value extraction
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
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
        "MATCH": "🎯 ",
    }
    prefix = levels.get(level, "→ ")
    print(f"{prefix} [LLM_HANDLER] {message}")


# Initialize LLM
llm = ChatOpenAI(
    model_name=settings.openai_model,
    temperature=0,
    max_tokens=settings.openai_max_tokens,
    api_key=settings.openai_api_key,
    top_p=0.1,
    frequency_penalty=2.0,
    presence_penalty=2.0
)

debug_log("ChatOpenAI initialized with temperature=0", "SUCCESS")


def calculate_match_score(user_text: str, placeholder: Dict) -> float:
    """
    Calculate match score between user input and placeholder
    Higher score = better match
    
    Uses multiple signals:
    - Exact placeholder name match
    - Partial name match
    - Type-specific keywords
    - Description keywords
    """
    user_text_lower = user_text.lower()
    placeholder_name = placeholder['name'].lower()
    placeholder_desc = placeholder.get('description', '').lower()
    placeholder_type = placeholder.get('type', '').lower()
    
    score = 0.0
    
    # === HIGHEST PRIORITY: Exact field name match ===
    if placeholder_name in user_text_lower:
        score += 100
        debug_log(f"  {placeholder['name']}: +100 (exact name match)", "DEBUG")
    
    # === Name part matches ===
    name_parts = placeholder_name.split()
    for part in name_parts:
        if len(part) > 2 and part in user_text_lower:
            score += 25
            debug_log(f"  {placeholder['name']}: +25 (name part '{part}' matched)", "DEBUG")
    
    # === Type-specific keyword matching ===
    type_keywords = {
        'currency': ['dollar', 'amount', '$', 'cost', 'price', 'fee', 'payment', 'paid', 'invest'],
        'date': ['date', 'when', 'day', 'month', 'year', '/', '-', 'january', 'february', 'march',
                 '2024', '2025', '2023', 'january', 'february', 'january 1', 'dec', 'nov'],
        'person_name': ['name', 'person', 'mr', 'ms', 'john', 'jane', 'smith', 'founder', 'investor'],
        'company_name': ['company', 'corp', 'inc', 'ltd', 'llc', 'organization', 'business', 'group', 'co'],
        'address': ['address', 'street', 'city', 'state', 'zip', 'road', 'ave', 'blvd', '123', 'ny', 'ca'],
        'email': ['email', 'contact', '@', '.com', '.org', '.net'],
        'phone': ['phone', 'number', 'call', 'contact', '(', ')', 'cell', 'mobile'],
    }
    
    if placeholder_type and placeholder_type in type_keywords:
        for keyword in type_keywords[placeholder_type]:
            if keyword in user_text_lower:
                score += 15
                debug_log(f"  {placeholder['name']}: +15 (keyword '{keyword}' for type {placeholder_type})", "DEBUG")
    
    # === Description keyword matching ===
    desc_words = [w for w in placeholder_desc.split() if len(w) > 3]
    for word in desc_words:
        if word in user_text_lower:
            score += 5
            debug_log(f"  {placeholder['name']}: +5 (description word '{word}')", "DEBUG")
    
    return score


def find_best_placeholder_match(
    user_input: str,
    unfilled_placeholders: List[Dict]
) -> Optional[Tuple[Dict, float]]:
    """
    Find the best matching placeholder for user input
    Returns (placeholder, confidence_score)
    
    Scoring approach:
    1. Exact field name mention (100 points)
    2. Field name parts (25 points each)
    3. Type-specific keywords (15 points each)
    4. Description keywords (5 points each)
    """
    
    if not unfilled_placeholders:
        return None
    
    # Single unfilled? Return it
    if len(unfilled_placeholders) == 1:
        debug_log(f"Only one unfilled: {unfilled_placeholders[0]['name']}", "MATCH")
        return (unfilled_placeholders[0], 1.0)
    
    # Calculate scores for all placeholders
    debug_log(f"Scoring {len(unfilled_placeholders)} placeholders for input: '{user_input}'", "DEBUG")
    
    scores = {}
    for placeholder in unfilled_placeholders:
        score = calculate_match_score(user_input, placeholder)
        scores[placeholder['name']] = (placeholder, score)
        debug_log(f"  {placeholder['name']}: {score:.0f} points", "DEBUG")
    
    # Find best match
    best_match = max(scores.values(), key=lambda x: x[1])
    
    placeholder, score = best_match
    confidence = min(score / 100, 1.0)  # Normalize to 0-1
    
    debug_log(f"Best match: {placeholder['name']} (confidence: {confidence:.2f})", "MATCH")
    
    return (placeholder, confidence)


def find_next_unfilled_placeholder(
    current_placeholder: Dict,
    unfilled_placeholders: List[Dict]
) -> Optional[Dict]:
    """
    Find the next unfilled placeholder after current one
    """
    placeholder_names = [p['name'] for p in unfilled_placeholders]
    
    if current_placeholder['name'] not in placeholder_names:
        # Current is filled, return first unfilled
        return unfilled_placeholders[0] if unfilled_placeholders else None
    
    current_idx = placeholder_names.index(current_placeholder['name'])
    
    if current_idx < len(unfilled_placeholders) - 1:
        return unfilled_placeholders[current_idx + 1]
    
    return None


async def analyze_placeholders(document_text: str) -> Dict[str, Any]:
    """Use OpenAI to analyze and describe placeholders"""
    
    debug_log("ANALYZE_PLACEHOLDERS CALLED", "INFO")
    
    try:
        system_prompt = """You are a legal document expert. Analyze [bracketed placeholders] and provide helpful descriptions.

Your response must be ONLY valid JSON (no exceptions):
{
  "placeholders": [
    {
      "name": "placeholder_name_without_brackets",
      "type": "text|currency|date|person_name|company_name|address|email|phone",
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
        
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])
        
        response_text = response.content
        
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
    IMPROVED VERSION:
    1. Better matching using semantic scoring
    2. Extract ALL values user provides
    3. Suggest NEXT placeholder with full details
    """
    
    debug_log("=" * 80, "INFO")
    debug_log("CHAT_FOR_PLACEHOLDERS CALLED", "INFO")
    debug_log("=" * 80, "INFO")
    
    debug_log(f"User message: '{message}'", "DEBUG")
    
    # Get unfilled/filled
    unfilled = [p for p in placeholders if not p.get("filled")]
    filled = [p for p in placeholders if p.get("filled")]
    
    if not unfilled:
        debug_log("No unfilled placeholders remaining", "WARNING")
        return {
            "assistant_message": "All fields are now filled! Ready to download your document.",
            "filled_values": {},
            "next_placeholder": None
        }
    
    # SMART MATCHING: Find best placeholder match
    match_result = find_best_placeholder_match(message, unfilled)
    
    if not match_result:
        return {
            "assistant_message": "I couldn't identify which field you're trying to fill. Please be more specific.",
            "filled_values": {},
            "next_placeholder": None
        }
    
    matched_placeholder, match_confidence = match_result
    
    # Build unfilled list for prompt
    unfilled_str = "\n".join([f'"{p["name"]}" (Type: {p.get("type", "text")})' for p in unfilled])
    
    # Build filled list
    filled_str = "\n".join([
        f'"{p["name"]}" = "{p.get("value", "")}"'
        for p in filled
    ]) or "None yet"
    
    # IMPROVED SYSTEM PROMPT: More explicit about value extraction
    system_prompt = f"""You are a document filling assistant. Your job is to extract values from user input and match them to placeholder fields.

KEY INSTRUCTION: Extract the VALUE and determine which PLACEHOLDER it belongs to, even if user didn't explicitly mention the field name.

FILLED FIELDS:
{filled_str}

UNFILLED FIELDS:
{unfilled_str}

CURRENT FOCUS (most likely field being described): "{matched_placeholder['name']}"
Type: {matched_placeholder.get('type', 'text')}
Description: {matched_placeholder.get('description', 'Field')}

USER MESSAGE: "{message}"

═══════════════════════════════════════════════════════════════════════════════
YOUR TASK:
1. Extract the value(s) the user provided
2. Determine which placeholder field(s) they belong to
3. Use EXACT placeholder names as keys
4. Suggest which field to fill NEXT (by name)

CRITICAL JSON FORMAT (no exceptions):
{{
  "assistant_message": "Acknowledge what was provided, then suggest next field",
  "filled_values": {{"Placeholder Name": "exact value from user"}},
  "next_placeholder": "Name of next unfilled field (or null if all done)"
}}

RULES:
- Acknowledge what user provided
- If they filled current field, say "Got it" then ask for NEXT field
- next_placeholder should be a NAME from UNFILLED FIELDS list
- If user value could match current focus field, use it
- Extract values EXACTLY as user stated (don't paraphrase)
- For next field, include: "Next, please provide: **[Field Name]**"
- ENTIRE response is ONLY JSON
- No text outside JSON
- Start with {{ end with }}

EXAMPLES:

User: "The company is ABC Corporation"
{{"assistant_message": "Got it, company is ABC Corporation. Next, please provide: **Purchase Amount**", "filled_values": {{"Company Name": "ABC Corporation"}}, "next_placeholder": "Purchase Amount"}}

User: "We paid $5000 for it"
{{"assistant_message": "Recorded $5000. Next, please provide: **Company Name**", "filled_values": {{"Purchase Amount": "$5000"}}, "next_placeholder": "Company Name"}}

User: "Company ABC and amount $1000"
{{"assistant_message": "Got it - ABC as company and $1000 as payment. All done!", "filled_values": {{"Company Name": "ABC", "Purchase Amount": "$1000"}}, "next_placeholder": null}}"""
    
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
    
    debug_log(f"Calling LLM with matched placeholder: {matched_placeholder['name']}", "INFO")
    
    result = None
    try:
        response = llm.invoke(messages)
        response_text = response.content
        
        debug_log(f"LLM response: {len(response_text)} chars", "DEBUG")
        
        # Extract JSON
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            debug_log(f"✓ JSON parsed successfully", "SUCCESS")
            
            # Ensure required fields
            if "assistant_message" not in result:
                result["assistant_message"] = "Got it"
            if "filled_values" not in result:
                result["filled_values"] = {}
            if "next_placeholder" not in result:
                result["next_placeholder"] = None
            
            # Log extracted values
            filled_values = result.get("filled_values", {})
            debug_log(f"Extracted {len(filled_values)} values", "INFO")
            for field_name, value in filled_values.items():
                debug_log(f"  '{field_name}' → '{value}'", "INFO")
            
            if result.get("next_placeholder"):
                debug_log(f"Next placeholder: {result['next_placeholder']}", "INFO")
            else:
                debug_log(f"All fields complete", "SUCCESS")
            
            return result
        else:
            debug_log(f"❌ No JSON found in response", "ERROR")
            debug_log(f"Raw response: {response_text[:200]}", "DEBUG")
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
    finally:
        # Add response to history
        if result:
            conversation_history.append({
                "role": "assistant",
                "content": result.get("assistant_message", "")
            })
    
    debug_log(f"Returning result", "SUCCESS")
    
    return result if result else {"assistant_message": "Error", "filled_values": {}, "next_placeholder": None}


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