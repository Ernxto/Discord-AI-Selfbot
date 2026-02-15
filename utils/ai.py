import sys
import asyncio
from openai import AsyncOpenAI as OpenAI
from os import getenv
from dotenv import load_dotenv
from datetime import datetime, date
import sqlite3
from utils.helpers import get_env_path, load_config, resource_path

# Model configurations
PRIMARY_MODEL_ID = "google/gemini-2.5-flash-lite"
PAID_FALLBACK_ID = "openai/gpt-oss-120b"

MODELS = [
    {
        "name": "Gemini 2.5 Flash Lite",
        "id": PRIMARY_MODEL_ID,
        "type": "paid",
        "daily_limit": float('inf'),
        "priority": 1
    },
    {
        "name": "GPT-OSS-120B",
        "id": PAID_FALLBACK_ID,
        "type": "paid",
        "daily_limit": float('inf'),
        "priority": 2
    }
]

# Database for tracking usage
DB_FILE = "config/model_usage.db"

# Initialize database on module load
_db_initialized = False

def _ensure_db_initialized():
    """Ensure database is initialized (called automatically)"""
    global _db_initialized
    if not _db_initialized:
        init_usage_db()
        _db_initialized = True

def init_usage_db():
    """Initialize database for tracking model usage"""
    conn = sqlite3.connect(resource_path(DB_FILE))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS usage (
            date TEXT,
            model_id TEXT,
            count INTEGER DEFAULT 0,
            PRIMARY KEY (date, model_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS costs (
            date TEXT PRIMARY KEY,
            paid_requests INTEGER DEFAULT 0,
            estimated_cost REAL DEFAULT 0.0
        )
    """)
    conn.commit()
    conn.close()

def get_model_usage(model_id):
    """Get today's usage count for a model"""
    _ensure_db_initialized()
    today = date.today().isoformat()
    conn = sqlite3.connect(resource_path(DB_FILE))
    c = conn.cursor()
    c.execute("SELECT count FROM usage WHERE date=? AND model_id=?", (today, model_id))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def increment_model_usage(model_id, is_paid=False):
    """Increment usage count for a model"""
    _ensure_db_initialized()
    today = date.today().isoformat()
    conn = sqlite3.connect(resource_path(DB_FILE))
    c = conn.cursor()
    
    # Update usage count
    c.execute("""
        INSERT INTO usage (date, model_id, count) 
        VALUES (?, ?, 1)
        ON CONFLICT(date, model_id) DO UPDATE SET count = count + 1
    """, (today, model_id))
    
    # Track paid usage costs
    if is_paid:
        c.execute("""
            INSERT INTO costs (date, paid_requests, estimated_cost)
            VALUES (?, 1, 0.00765)
            ON CONFLICT(date) DO UPDATE SET 
                paid_requests = paid_requests + 1,
                estimated_cost = estimated_cost + 0.00765
        """, (today,))
    
    conn.commit()
    conn.close()

def get_next_available_free_model(start_priority=0):
    """Get the next available free model based on priority
    
    Args:
        start_priority: Only return models with priority > this value
    
    Returns:
        Model dict or None if no free models available
    """
    for model in MODELS:
        if model["type"] == "paid":
            continue  # Skip paid models
        if model["priority"] <= start_priority:
            continue  # Skip models we've already tried
        
        usage = get_model_usage(model["id"])
        if usage < model["daily_limit"]:
            return model
    
    return None  # No free models available

def get_paid_model():
    """Get the paid model as last resort"""
    for model in MODELS:
        if model["type"] == "paid":
            return model
    return None

def get_usage_stats():
    """Get today's usage statistics"""
    _ensure_db_initialized()
    today = date.today().isoformat()
    stats = {"free": 0, "paid": 0, "cost": 0.0}
    
    conn = sqlite3.connect(resource_path(DB_FILE))
    c = conn.cursor()
    
    # Count free tier usage
    for model in MODELS:
        if model["type"] == "free":
            c.execute("SELECT count FROM usage WHERE date=? AND model_id=?", 
                     (today, model["id"]))
            result = c.fetchone()
            if result:
                stats["free"] += result[0]
    
    # Get paid usage and cost
    c.execute("SELECT paid_requests, estimated_cost FROM costs WHERE date=?", (today,))
    result = c.fetchone()
    if result:
        stats["paid"] = result[0]
        stats["cost"] = result[1]
    
    conn.close()
    return stats

# Initialize OpenRouter client
client = None

def init_ai():
    """Initialize OpenRouter client"""
    global client
    env_path = get_env_path()
    load_dotenv(dotenv_path=env_path)
    
    api_key = getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not found in config/.env")
        sys.exit(1)
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )
    
    # Initialize usage tracking
    init_usage_db()
    
    # Log current usage stats
    stats = get_usage_stats()
    print(f"[AI] Daily usage - Free: {stats['free']}/600, Paid: {stats['paid']}, Cost: ${stats['cost']:.2f}")

async def try_model_with_retries(model, prompt, instructions, history, max_attempts=3):
    """Try a specific model with multiple retries
    
    Args:
        model: The model dict to use
        prompt: The user prompt
        instructions: System instructions
        history: Conversation history
        max_attempts: Number of attempts (default 3)
    
    Returns:
        Response string if successful, None if all attempts failed
    """
    model_name = model["name"]
    model_id = model["id"]
    is_paid = model["type"] == "paid"
    
    for attempt in range(1, max_attempts + 1):
        print(f"[AI API] >>> {model_name} (attempt {attempt}/{max_attempts}) model_id='{model_id}' is_paid={is_paid}")
        
        try:
            # Prepare messages
            messages = [{"role": "system", "content": instructions}]
            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": prompt})
            
            # Call API with timeout
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=model_id,
                    messages=messages,
                    max_tokens=600,
                    temperature=0.7
                ),
                timeout=10
            )
            
            # Track usage
            increment_model_usage(model_id, is_paid)
            
            result = response.choices[0].message.content
            print(f"[AI] ✓ Success with {model_name}")
            return result
            
        except asyncio.TimeoutError:
            if attempt < max_attempts:
                print(f"[AI] ✗ Timeout with {model_name}, retrying...")
                await asyncio.sleep(1)
            else:
                print(f"[AI] ✗ Timeout with {model_name} after {max_attempts} attempts")
                return None
                
        except Exception as e:
            if attempt < max_attempts:
                print(f"[AI] ✗ Error with {model_name}: {str(e)[:50]}, retrying...")
                await asyncio.sleep(1)
            else:
                print(f"[AI] ✗ Error with {model_name} after {max_attempts} attempts: {str(e)[:50]}")
                return None

async def generate_response(prompt, instructions, history=None, model_override=None):
    """Generate response using Gemma 3 27B, with paid fallback"""
    if not client:
        init_ai()
    
    print(f"[AI DEBUG] NEW REQUEST - prompt: {prompt[:50]}...")
    
    # Try primary model first
    model = next((m for m in MODELS if m["id"] == PRIMARY_MODEL_ID), None)
    if model:
        print(f"[AI] >>> USING: {model['name']}")
        result = await try_model_with_retries(model, prompt, instructions, history, max_attempts=3)
        if result is not None:
            return result
    
    # Fallback to GPT-OSS-120B (paid)
    fallback = next((m for m in MODELS if m["id"] == PAID_FALLBACK_ID), None)
    if fallback:
        print(f"[AI] >>> PRIMARY FAILED, USING FALLBACK: {fallback['name']}")
        result = await try_model_with_retries(fallback, prompt, instructions, history, max_attempts=3)
        if result is not None:
            return result
    
    print("[AI] ✗ All models failed")
    return None

async def generate_response_image(prompt, instructions, image_url, history=None, model_override=None):
    """Generate response with image (uses vision-capable model)"""
    return await generate_response(
        f"{prompt} [Image: {image_url}]",
        instructions,
        history,
        model_override
    )

def limit_response(text, max_sentences=2, max_words=30):
    """Limit response to max sentences and max words
    
    Args:
        text: The response text to limit
        max_sentences: Maximum number of sentences (default 2)
        max_words: Maximum number of words (default 30)
    
    Returns:
        Limited response text
    """
    # Split into sentences
    sentences = text.split('.')
    # Filter empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Take only first max_sentences
    limited = ' '.join(sentences[:max_sentences])
    
    # If still too long, limit by words
    words = limited.split()
    if len(words) > max_words:
        limited = ' '.join(words[:max_words])
    
    # Clean up
    limited = limited.strip()
    # Add period if doesn't end with punctuation
    if limited and limited[-1] not in '.!?':
        limited += '.'
    
    return limited
