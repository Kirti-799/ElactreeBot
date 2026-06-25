from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import json
from google import genai
from google.genai import types

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --- 1. DYNAMIC JSON DATABASE LOADING ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.json")

FORMATTED_CATALOG = ""

try:
    with open(DB_PATH, "r", encoding="utf-8") as file:
        raw_db = json.load(file)
    
    catalog_lines = []
    for item in raw_db:
        p_name = item.get("product_name", "N/A")
        c_name = item.get("category_name", "N/A")
        url = item.get("url", "#")
        catalog_lines.append(f"• Product: [{p_name}] | Category: [{c_name}] | Link: {url}")
        
    FORMATTED_CATALOG = "\n".join(catalog_lines)
    
    # This will print in green in your terminal if it works perfectly
    print(f"\033[92mSUCCESS: Loaded {len(raw_db)} catalog items from database.json into AI Context.\033[0m")

except FileNotFoundError:
    print(f"\033[91mCRITICAL ERROR: Could not find database.json at {DB_PATH}\033[0m")
    FORMATTED_CATALOG = "ERROR: FILE_MISSING"
except json.JSONDecodeError as e:
    print(f"\033[91mCRITICAL ERROR: Your database.json has a formatting error: {e}\033[0m")
    FORMATTED_CATALOG = "ERROR: INVALID_JSON"
except Exception as e:
    print(f"\033[91mCRITICAL ERROR: {e}\033[0m")
    FORMATTED_CATALOG = "ERROR: UNKNOWN"

# --- 2. CONFIGURATION DATA ---
COMPANY_EMAIL = "sales@elactree.com"
COMPANY_PHONE = "+1 (800) 555-0199"

# --- 3. THE PROACTIVE SALES INSTRUCTION ---
SYSTEM_RULESET = f"""
You are ElactreeBot, the expert, premium virtual sales agent for Elactree. Your job is to drive interest toward our product catalog while being warm, helpful, and highly conversational.

*** THE ELACTREE MASTER INVENTORY ***
{FORMATTED_CATALOG}

YOUR SALES BEHAVIOR MANDATES:

1. PROACTIVE RELATION MATCHING:
   - When users mention terms related to a product's utility, features, or environment, immediately map it to our closest inventory item.
   - If they say: "display", "tv", "screen", "board", "presentation", "classroom", or "meeting" -> Connect it directly to the "Interactive flat Panel" category and feature the product [RE04FV].
   - If they say: "power", "protection", "voltage", "safety", "ups", "breaker", or "surge" -> Connect it to the "Surge Protectors" category.

2. LINK INJECTION MANDATE:
   - Every single time you mention a product or category that exists in our inventory, you MUST include its markdown link exactly as formatted in the catalog data.
   - Example: "For collaborative setups, I highly recommend our [RE04FV](/product/benq-board-re8604fv-essential-series) which is a top-tier Interactive flat Panel."

3. UNRELATED INQUIRIES (The Elegant Pivot):
   - If a user asks for something completely outside our domain (like 'kitchen appliances' or a direct competitor like 'Samsung TVs'), do not be rigid or robotic. 
   - Say: "While we don't carry that specific item, Elactree specializes in premium corporate hardware like Interactive Flat Panels and power protection solutions. I'd love to help you explore those options!"

4. CONTACT TRIGGERS:
   - If they mention "email", "phone", "contact", or "support", politely provide our contact details:
     "I'd be glad to put you in touch with a human expert! You can email us at {COMPANY_EMAIL} or give our support line a call at {COMPANY_PHONE}."
"""

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # Safety trap if the JSON failed to load
    if "ERROR:" in FORMATTED_CATALOG:
        return ChatResponse(response="I apologize, but I am currently undergoing a brief inventory update. Please check back in a few minutes or reach out to our team directly!")

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=request.message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_RULESET,
                temperature=0.4
            )
        )
        return ChatResponse(response=response.text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Service Error: {str(e)}")