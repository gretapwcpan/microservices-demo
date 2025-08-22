"""
Gemini Service for quanBuy
Handles AI-powered features using Google's Gemini API
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from google.cloud import firestore
from google.cloud import pubsub_v1
import redis
import asyncio
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
app = FastAPI(title="quanBuy Gemini Service")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")  # Support 2.5-pro, 1.5-pro, etc.
GEMINI_API_ENDPOINT = os.getenv("GEMINI_API_ENDPOINT", None)  # Optional custom endpoint

if GEMINI_API_KEY and GEMINI_API_KEY != "mock_mode":
    try:
        # Configure with custom endpoint if provided
        if GEMINI_API_ENDPOINT:
            genai.configure(api_key=GEMINI_API_KEY, transport='rest', client_options={'api_endpoint': GEMINI_API_ENDPOINT})
        else:
            genai.configure(api_key=GEMINI_API_KEY)
        
        model = genai.GenerativeModel(GEMINI_MODEL)
        logger.info(f"Initialized Gemini with model: {GEMINI_MODEL}")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini: {e}")
        model = None
else:
    logger.warning("GEMINI_API_KEY not set or in mock mode, AI features will use fallbacks")
    model = None

# Initialize Redis for caching
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Initialize Firestore (only if not in local mode)
LOCAL_MODE = os.getenv("LOCAL_MODE", "false").lower() == "true"

if not LOCAL_MODE:
    try:
        db = firestore.Client()
        publisher = pubsub_v1.PublisherClient()
        PROJECT_ID = os.getenv("GCP_PROJECT_ID", "quanbuy-project")
        TOPIC_PATH = publisher.topic_path(PROJECT_ID, "search-events")
    except Exception as e:
        logger.warning(f"Could not initialize GCP services: {e}")
        LOCAL_MODE = True
        db = None
        publisher = None
else:
    db = None
    publisher = None
    logger.info("Running in LOCAL MODE - GCP services disabled")

# Request/Response Models
class MysterySearchRequest(BaseModel):
    user_id: str
    search_history: List[str] = []
    current_time: Optional[str] = None
    location: Optional[str] = None

class MysterySearchResponse(BaseModel):
    product_name: str
    reason: str
    description: str
    category: str
    price_range: str

class OracleSearchRequest(BaseModel):
    user_id: str
    feeling: str
    context: Optional[str] = None

class OracleSearchResponse(BaseModel):
    products: List[Dict[str, str]]
    insight: str

class DiscoveryStoryRequest(BaseModel):
    user_id: str
    searches: List[str]
    products_viewed: List[str]
    duration_minutes: int

class DiscoveryStoryResponse(BaseModel):
    story: str
    title: str
    mood: str

class SearchDNARequest(BaseModel):
    user_id: str
    search_history: List[str]
    timeframe_days: int = 30

class SearchDNAResponse(BaseModel):
    pattern: str
    personality_type: str
    insights: List[str]
    visual_dna: str  # Base64 encoded image or SVG

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "gemini-service"}

# Mystery Search - AI generates surprising discoveries
@app.post("/mystery-search", response_model=MysterySearchResponse)
async def mystery_search(request: MysterySearchRequest, background_tasks: BackgroundTasks):
    """Generate a surprising product discovery based on user's patterns"""
    
    if not model:
        # Fallback without Gemini
        return MysterySearchResponse(
            product_name="Artisan Mystery Box",
            reason="Every search deserves a surprise",
            description="A curated collection of handpicked treasures",
            category="discovery",
            price_range="$50-100"
        )
    
    # Check cache first
    cache_key = f"mystery:{request.user_id}:{datetime.now().strftime('%Y%m%d%H')}"
    cached = redis_client.get(cache_key)
    if cached:
        return MysterySearchResponse(**json.loads(cached))
    
    # Generate with Gemini
    prompt = f"""
    You are a mystical curator for quanBuy, a mindful marketplace.
    
    User's recent searches: {', '.join(request.search_history[-10:])}
    Current time: {request.current_time or datetime.now().strftime('%H:%M')}
    
    Generate a surprising, delightful product discovery that:
    1. They wouldn't search for directly
    2. Connects to their search patterns in an unexpected way
    3. Has a poetic, artistic quality
    
    Return a JSON with:
    - product_name: Unique, intriguing name
    - reason: Why this matches their soul (1 sentence)
    - description: Poetic description (2 sentences)
    - category: One word category
    - price_range: Estimated price range
    
    Be creative, mystical, and surprising.
    """
    
    try:
        response = model.generate_content(prompt)
        # Parse the response
        result_text = response.text.strip()
        if result_text.startswith('```json'):
            result_text = result_text[7:-3]
        
        result = json.loads(result_text)
        
        # Cache for 1 hour
        redis_client.setex(cache_key, 3600, json.dumps(result))
        
        # Publish event
        background_tasks.add_task(publish_event, "mystery_search", {
            "user_id": request.user_id,
            "product": result["product_name"]
        })
        
        return MysterySearchResponse(**result)
        
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        # Fallback response
        return MysterySearchResponse(
            product_name="Serendipity Stone",
            reason="Sometimes the universe chooses for you",
            description="A moment of unexpected discovery. Let curiosity guide you.",
            category="mystery",
            price_range="$30-80"
        )

# Oracle Mode - Search by feeling
@app.post("/oracle-search", response_model=OracleSearchResponse)
async def oracle_search(request: OracleSearchRequest):
    """Convert feelings/moods into product discoveries"""
    
    if not model:
        # Fallback
        return OracleSearchResponse(
            products=[
                {
                    "name": "Calming Essence",
                    "description": "Find your center",
                    "match_reason": "Aligns with your current energy"
                }
            ],
            insight="Your search reflects your inner state"
        )
    
    prompt = f"""
    You are the Oracle of quanBuy, translating emotions into discoveries.
    
    User's feeling: "{request.feeling}"
    Context: {request.context or 'General mood'}
    
    Match this emotional state to 3 products that would address, complement, or transform this feeling.
    Consider color psychology, materials, textures, and purpose.
    
    Return JSON with:
    - products: Array of 3 items, each with:
      - name: Product name
      - description: How it relates to the feeling
      - match_reason: Mystical explanation
    - insight: One profound sentence about their emotional search
    
    Be poetic, insightful, and therapeutic.
    """
    
    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        if result_text.startswith('```json'):
            result_text = result_text[7:-3]
        
        result = json.loads(result_text)
        return OracleSearchResponse(**result)
        
    except Exception as e:
        logger.error(f"Oracle error: {e}")
        return OracleSearchResponse(
            products=[
                {
                    "name": "Emotional Compass",
                    "description": "Navigate your feelings",
                    "match_reason": "Every feeling points somewhere"
                }
            ],
            insight="Your emotions are your guide"
        )

# Discovery Story Generator
@app.post("/discovery-story", response_model=DiscoveryStoryResponse)
async def generate_discovery_story(request: DiscoveryStoryRequest):
    """Generate a narrative about the user's search journey"""
    
    if not model:
        return DiscoveryStoryResponse(
            story="Your journey through the marketplace of dreams continues...",
            title="Today's Discovery",
            mood="contemplative"
        )
    
    prompt = f"""
    Create a short, poetic narrative about this search journey:
    
    Searches performed: {', '.join(request.searches)}
    Products viewed: {', '.join(request.products_viewed)}
    Time spent: {request.duration_minutes} minutes
    
    Style: Mystical and philosophical, like Rumi meets a fortune cookie
    
    Return JSON with:
    - story: 2-3 sentence narrative
    - title: 2-4 word title
    - mood: One word describing the journey's mood
    
    Make it shareable and memorable.
    """
    
    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        if result_text.startswith('```json'):
            result_text = result_text[7:-3]
        
        result = json.loads(result_text)
        
        # Save to Firestore (if not in local mode)
        if db and not LOCAL_MODE:
            doc_ref = db.collection('discovery_stories').document()
            doc_ref.set({
                'user_id': request.user_id,
                'story': result['story'],
                'title': result['title'],
                'mood': result['mood'],
                'created_at': datetime.now(),
                'searches': request.searches,
                'duration': request.duration_minutes
            })
        
        return DiscoveryStoryResponse(**result)
        
    except Exception as e:
        logger.error(f"Story generation error: {e}")
        return DiscoveryStoryResponse(
            story="Each search is a step on an infinite path of discovery.",
            title="Endless Journey",
            mood="mysterious"
        )

# Search DNA Analysis
@app.post("/search-dna", response_model=SearchDNAResponse)
async def analyze_search_dna(request: SearchDNARequest):
    """Analyze search patterns to create a user's 'Search DNA'"""
    
    if not model:
        return SearchDNAResponse(
            pattern="Explorer",
            personality_type="The Curious Wanderer",
            insights=["You seek the unexpected"],
            visual_dna="<svg>...</svg>"  # Placeholder
        )
    
    prompt = f"""
    Analyze these search patterns to determine the user's 'Search DNA':
    
    Search history (last {request.timeframe_days} days): {', '.join(request.search_history)}
    
    Identify:
    1. Their search pattern (Explorer, Hunter, Dreamer, Collector, etc.)
    2. Personality type (creative title)
    3. Three key insights about their search behavior
    4. A visual pattern description (for generating art later)
    
    Return JSON with:
    - pattern: One word pattern type
    - personality_type: Creative 2-4 word title
    - insights: Array of 3 insights
    - visual_dna: Description of visual pattern (colors, shapes, flow)
    
    Be insightful and poetic.
    """
    
    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        if result_text.startswith('```json'):
            result_text = result_text[7:-3]
        
        result = json.loads(result_text)
        
        # Generate simple SVG based on pattern
        visual_dna = generate_dna_visual(result['pattern'])
        result['visual_dna'] = visual_dna
        
        # Cache DNA for quick retrieval
        redis_client.setex(
            f"dna:{request.user_id}",
            86400,  # 24 hours
            json.dumps(result)
        )
        
        return SearchDNAResponse(**result)
        
    except Exception as e:
        logger.error(f"DNA analysis error: {e}")
        return SearchDNAResponse(
            pattern="Seeker",
            personality_type="The Eternal Seeker",
            insights=[
                "Your searches reveal depth",
                "You value authenticity",
                "Discovery is your journey"
            ],
            visual_dna="<svg>...</svg>"
        )

# Helper function to generate DNA visual
def generate_dna_visual(pattern: str) -> str:
    """Generate a simple SVG representation of search DNA"""
    colors = {
        "Explorer": ["#D4A574", "#8B5A3C"],
        "Hunter": ["#704241", "#8B5A3C"],
        "Dreamer": ["#F5E6D3", "#D4A574"],
        "Collector": ["#8B5A3C", "#704241"],
        "default": ["#D4A574", "#8B5A3C"]
    }
    
    pattern_colors = colors.get(pattern, colors["default"])
    
    svg = f"""
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <radialGradient id="dna-gradient">
                <stop offset="0%" style="stop-color:{pattern_colors[0]};stop-opacity:0.8" />
                <stop offset="100%" style="stop-color:{pattern_colors[1]};stop-opacity:0.3" />
            </radialGradient>
        </defs>
        <circle cx="100" cy="100" r="80" fill="url(#dna-gradient)" />
        <circle cx="100" cy="100" r="60" fill="none" stroke="{pattern_colors[0]}" stroke-width="0.5" opacity="0.5" />
        <circle cx="100" cy="100" r="40" fill="none" stroke="{pattern_colors[1]}" stroke-width="0.5" opacity="0.5" />
    </svg>
    """
    return svg.strip()

# Publish events to Pub/Sub
async def publish_event(event_type: str, data: dict):
    """Publish events for analytics and triggers"""
    if LOCAL_MODE or not publisher:
        logger.info(f"LOCAL MODE: Would publish event: {event_type}")
        return
        
    try:
        message = json.dumps({
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        })
        
        future = publisher.publish(TOPIC_PATH, message.encode('utf-8'))
        logger.info(f"Published event: {event_type}")
    except Exception as e:
        logger.error(f"Failed to publish event: {e}")

# Collaborative search suggestions
@app.post("/collaborative-suggestions")
async def get_collaborative_suggestions(room_id: str, participants: List[str]):
    """Generate AI suggestions for collaborative search rooms"""
    
    if not model:
        return {
            "suggestions": ["vintage treasures", "mindful living", "artisan crafts"],
            "theme": "Collective Discovery"
        }
    
    prompt = f"""
    A group of {len(participants)} people are searching together on quanBuy.
    Generate 3 search suggestions that would create interesting discoveries for the group.
    Also suggest a theme for their search session.
    
    Return JSON with:
    - suggestions: Array of 3 search terms
    - theme: A poetic theme for their session
    
    Make it collaborative and exciting.
    """
    
    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        if result_text.startswith('```json'):
            result_text = result_text[7:-3]
        
        return json.loads(result_text)
        
    except Exception as e:
        logger.error(f"Collaborative suggestions error: {e}")
        return {
            "suggestions": ["hidden gems", "sustainable finds", "local artisans"],
            "theme": "Discover Together"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
