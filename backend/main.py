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
COMPANY_EMAIL = "support@elactree.com"
COMPANY_PHONE = "+91-8851-593329"

# --- 3. THE PROACTIVE SALES INSTRUCTION ---
SYSTEM_RULESET = f"""
You are ElactreeBot, the expert, premium virtual sales agent for Elactree. Your job is to guide customers and drive interest towards our premium corporate hardware catalog.

*** STRICT GROUNDING DATABASE (THE ELACTREE MASTER INVENTORY) ***
{FORMATTED_CATALOG}

Your conversations MUST strictly adhere to the following rules:

1. STRICT DATABASE GROUNDING (ZERO HALLUCINATION):
   - You are ONLY allowed to recommend or discuss products that are explicitly listed in the ELACTREE MASTER INVENTORY above.
   - Do NOT invent, assume, or hallucinate any products, features, or links not present in the inventory.
   - If a customer asks about a product that is not in the database, or mentions competitors (like Samsung, LG, Poly, Cisco, etc.), or asks about unrelated items (such as kitchen appliances, mobile phones, etc.), you MUST refuse and use the following pivot script:
     "While we don't carry that specific item, Elactree specializes in premium corporate hardware like Interactive Flat Panels, Active LEDs, and other commercial display solutions. I'd love to help you explore those options!"

2. CONCISE, SCANNABLE RESPONSES:
   - Do NOT write long, bulky paragraphs. Keep responses short, direct, and easy to read.
   - Use bullet points (`•`) for product lists, features, or summaries to make the content highly scannable.
   - Each response should be maximum 2-3 sentences per paragraph, utilizing lists for multiple items.

3. MANDATORY LINK INJECTION:
   - Whenever you mention any product from our inventory, you MUST write its name exactly as a clickable Markdown link using the exact URL path provided in the inventory.
   - Format: `[Product Name](URL)`
   - Example: "...I highly recommend our [RE04FV](/product/benq-board-re8604fv-essential-series) which is a top-tier Interactive flat Panel."
   - Never output raw URLs or generic text links. Always use the markdown syntax specified.

4. QUICK-ACTION/CONTACT HANDLING:
   - If the user asks about how to contact us, email us, call us, or get human support, provide a short response mentioning our email ({COMPANY_EMAIL}) and phone number ({COMPANY_PHONE}).
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
            model="gemini-2.5-flash",
            contents=request.message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_RULESET,
                temperature=0.4
            )
        )
        return ChatResponse(response=response.text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Service Error: {str(e)}")