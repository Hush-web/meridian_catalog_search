from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
import time

# Import the logic we extracted for the evaluation harness
from search_service import SearchService

# --- GLOBAL STATE ---
# We use app.state to hold our service and cache
# This avoids global variables and is the FastAPI best practice

# --- PYDANTIC MODELS ---
class SearchRequest(BaseModel):
    query: str
    pharmacy_id: str
    category: Optional[str] = None
    in_stock_only: bool = False

class ProductResult(BaseModel):
    product_id: str
    brand: str
    generic_name: str
    price: float
    stock: int
    warning: Optional[str] = None
    is_restricted: bool

class SearchResponse(BaseModel):
    results: List[ProductResult]

class AutocompleteResponse(BaseModel):
    suggestions: List[str]


# --- STARTUP LOGIC (LIFESPAN) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading Search Service...")
    # This loads the catalog, builds BM25, and populates Qdrant
    app.state.search_service = SearchService()
    
    # Initialize the Cache
    app.state.cache = {}
    
    print("✅ System Ready!")
    yield
    print("Shutting down...")


app = FastAPI(
    title="Meridian Catalog Search", 
    description="Hybrid Search API for Pharmacy Catalogs",
    lifespan=lifespan
)

# --- CACHING HELPER FUNCTIONS ---
def get_from_cache(key):
    if key in app.state.cache:
        result, timestamp = app.state.cache[key]
        # Cache is valid for 60 seconds (to handle inventory updates)
        if time.time() - timestamp < 60:
            return result
        else:
            del app.state.cache[key] # Expired
    return None

def save_to_cache(key, result):
    app.state.cache[key] = (result, time.time())


# --- ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "healthy", "cached_queries": len(app.state.cache)}

@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    # 1. CHECK CACHE
    # We build a unique key based on the query and all filters
    cache_key = f"{request.pharmacy_id}:{request.query}:{request.category}:{request.in_stock_only}"
    cached_result = get_from_cache(cache_key)
    
    if cached_result:
        print(f"⚡ CACHE HIT for: '{request.query}'")
        return cached_result

    # 2. RUN HYBRID SEARCH (Using the SearchService)
    # We fetch 20 results so we have room to apply filters without running out
    raw_results = app.state.search_service.hybrid_search(
        query=request.query, 
        pharmacy_id=request.pharmacy_id, 
        limit=20
    )

    # 3. APPLY FILTERS & SAFETY
    inventory = app.state.search_service.get_inventory(request.pharmacy_id)
    if inventory is None:
        raise HTTPException(status_code=404, detail="Pharmacy not found")

    results = []
    seen_brands = set()
    
    for p in raw_results:
        pid = p["product_id"]
        
        # TENANCY: Double check they stock it (hybrid_search does this, but safety first)
        if pid not in inventory:
            continue
            
        inv_item = inventory[pid]
        
        # FILTERS
        if request.category and p["category"] != request.category:
            continue
        if request.in_stock_only and inv_item["stock"] <= 0:
            continue
            
        # DEDUPLICATION
        if p["brand"] in seen_brands:
            continue
        seen_brands.add(p["brand"])
        
        # SAFETY WARNINGS
        warning = None
        if p["restricted"]:
            warning = "Age restricted. Requires ID and in-store purchase."
            
        results.append(ProductResult(
            product_id=pid,
            brand=p["brand"],
            generic_name=p["generic_name"],
            price=inv_item["price"],
            stock=inv_item["stock"],
            warning=warning,
            is_restricted=p["restricted"]
        ))
        
        if len(results) >= 5: # Return top 5 unique brands
            break

    final_response = SearchResponse(results=results)
    
    # 4. SAVE TO CACHE
    save_to_cache(cache_key, final_response)
    
    return final_response


@app.get("/autocomplete", response_model=AutocompleteResponse)
def autocomplete(query: str, pharmacy_id: str):
    inventory = app.state.search_service.get_inventory(pharmacy_id)
    if inventory is None:
        raise HTTPException(status_code=404, detail="Pharmacy not found")
        
    suggestions = set()
    # Simple substring match for autocomplete
    for p in app.state.search_service.catalog:
        if p["product_id"] not in inventory:
            continue # Tenancy check
            
        if query.lower() in p["brand"].lower() or query.lower() in p["generic_name"].lower():
            suggestions.add(f"{p['brand']} ({p['generic_name']})")
            
    return AutocompleteResponse(suggestions=list(suggestions)[:5])