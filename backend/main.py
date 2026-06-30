from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. DYNAMIC JSON DATABASE LOADING ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.json")

raw_db = []

try:
    with open(DB_PATH, "r", encoding="utf-8") as file:
        raw_db = json.load(file)
    print(f"\033[92mSUCCESS: Loaded {len(raw_db)} catalog items from database.json into Local Context.\033[0m")
except Exception as e:
    print(f"\033[91mCRITICAL ERROR loading database.json: {e}\033[0m")

# --- 2. CONFIGURATION DATA ---
COMPANY_EMAIL = "support@elactree.com"
COMPANY_PHONE = "+91-8851-593329"

# --- 3. THE LOCAL CATALOG SEARCH ROUTER ---
def search_local_catalog(user_message: str) -> list:
    msg = user_message.lower().strip()
    
    # Intent mapping of common synonyms to database terms
    intent_mappings = {
        "screen": ["interactive flat panel", "commercial digital signage", "active led", "curved gaming monitor"],
        "display": ["interactive flat panel", "commercial digital signage", "active led", "curved gaming monitor"],
        "tv": ["commercial tvs", "commercial digital signage"],
        "board": ["interactive flat panel"],
        "whiteboard": ["interactive flat panel"],
        "classroom": ["interactive flat panel"],
        "meeting": ["interactive flat panel", "ptz & conference room cameras", "conference room microphones & speakers"],
        "mic": ["microphones", "speakerphone"],
        "audio": ["microphones", "speakerphone"],
        "sound": ["microphones", "speakerphone"],
        "speaker": ["microphones", "speakerphone"],
        "camera": ["ptz & conference room cameras", "zoom rooms system"],
        "zoom": ["zoom rooms system", "ptz & conference room cameras"],
        "led": ["active led"],
        "outdoor": ["outdoor"],
        "indoor": ["indoor"],
        "monitor": ["computer monitors", "curved gaming monitor"],
        "gaming": ["curved gaming monitor"],
        "signage": ["commercial digital signage"],
        "ad": ["commercial digital signage"],
        "advertisement": ["commercial digital signage"],
        "benq": ["re04fv", "rp04"],
        "philips": ["pse0401", "speakerphones & microphones"],
        "meetingbar": ["meetingbar-a50-zoom-rooms-appliance", "zoom rooms system"],
        "flip": ["flip 2.0"],
        "blaze": ["blaze"]
    }
    
    STOP_WORDS = {
        "show", "me", "some", "for", "a", "an", "the", "is", "do", "you", "have", 
        "any", "how", "to", "what", "find", "get", "recommend", "need", "want", 
        "please", "can", "give", "list", "are", "about", "your", "our", "with", "in"
    }
    
    COMPETITORS = {"samsung", "lg", "poly", "cisco", "dell", "sony", "logitech", "epson"}
    
    # Extract clean tokens from message (remove punctuation)
    cleaned_msg = re.sub(r'[^\w\s]', ' ', msg)
    words = cleaned_msg.split()
    
    # Filter out stop words
    filtered_words = [w for w in words if w not in STOP_WORDS]
    
    # Force competitor inquiries straight to Condition B (no match)
    if any(comp in filtered_words for comp in COMPETITORS):
        return []
        
    matched_items = []
    candidates = []
    
    for item in raw_db:
        p_name = item.get("product_name", "").lower()
        c_name = item.get("category_name", "").lower()
        title = item.get("title", "").lower()
        
        is_direct_match = False
        for word in filtered_words:
            w_singular = word[:-1] if (word.endswith('s') and len(word) > 3) else word
            
            # Substring checks are restricted for terms length > 2
            if len(w_singular) > 2:
                if (w_singular in p_name or w_singular in c_name or w_singular in title or
                    p_name in w_singular or c_name in w_singular or title in w_singular):
                    is_direct_match = True
                    break
            else:
                # Require exact full word match for very short query terms (like 'tv')
                p_words = p_name.split()
                c_words = c_name.split()
                t_words = title.split()
                if (w_singular in p_words or w_singular in c_words or w_singular in t_words):
                    is_direct_match = True
                    break
                
        if is_direct_match:
            candidates.append(item)
            continue
            
        # B. Intent Mapping Matches
        matched_by_intent = False
        for word in filtered_words:
            w_singular = word[:-1] if (word.endswith('s') and len(word) > 3) else word
            if w_singular in intent_mappings:
                for target_keyword in intent_mappings[w_singular]:
                    if (target_keyword in p_name or target_keyword in c_name or target_keyword in title):
                        matched_by_intent = True
                        break
            if matched_by_intent:
                break
                
        if matched_by_intent:
            candidates.append(item)
            
    # Deduplicate matches by product id
    seen_ids = set()
    for item in candidates:
        item_id = item.get("id")
        if item_id not in seen_ids:
            seen_ids.add(item_id)
            matched_items.append(item)
            
    return matched_items

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # Safety check for database loading
    if not raw_db:
        return ChatResponse(response="I apologize, but I am currently undergoing a brief inventory update. Please check back in a few minutes or reach out to our team directly!")

    msg_lower = request.message.lower().strip()

    # 1. Contact / Support Handling
    if any(k in msg_lower for k in ["email", "phone", "contact", "support"]):
        return ChatResponse(response=f"You can reach Elactree support via email at {COMPANY_EMAIL} or call us at {COMPANY_PHONE}.")

    # 2. Local Catalog Matching
    matched_products = search_local_catalog(request.message)

    if matched_products:
        response_blocks = []
        for prod in matched_products:
            p_name = prod.get("product_name", "N/A")
            c_name = prod.get("category_name", "N/A")
            url = prod.get("url", "#")
            
            # Format using exact requested key-value layout
            block = (
                f"**Product Found:** {p_name}\n"
                f"\u2022 **Category:** {c_name}\n"
                f"\u2022 **Product Link:** [Click Here to View Page]({url})\n"
                f"\u2022 **Specialty:** High-performance hardware solution tailored for your requirements."
            )
            response_blocks.append(block)
            
        final_response = "\n\n".join(response_blocks)
        return ChatResponse(response=final_response)

    # 3. Fallback to Custom API Hook (Condition B)
    # TODO: Insert your custom cloud API search or vector retrieval call here later
    return ChatResponse(response="Notice: The requested item was not found in our immediate catalog. [Custom API Request Integration Point]")