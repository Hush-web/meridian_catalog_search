from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
from contextlib import asynccontextmanager

# Import our search engines
from rank_bm25 import BM25Okapi
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding

# --- GLOBAL STATE ---
# We load these once when the app starts
app_state = {}

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
    warning: Optional[str] = None # For restricted items
    is_restricted: bool

class SearchResponse(BaseModel):
    results: List[ProductResult]

# --- STARTUP LOGIC ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Load Data
    print("Loading catalog and pharmacies...")
    with open("catalog.json", "r") as f:
        app_state["catalog"] = json.load(f)
    with open("pharmacies.json", "r") as f:
        app_state["pharmacies"] = json.load(f)
        
    # 2. Setup BM25
    print("Building BM25 Index...")
    corpus = []
    for p in app_state["catalog"]:
        text = f"{p['brand']} {p['generic_name']} {p['active_ingredients']} {p['category']} {p['label_uses']}"
        corpus.append(text.lower().split())
    app_state["bm25"] = BM25Okapi(corpus)
    
    # 3. Setup Qdrant & Embeddings
    print("Building Qdrant Index...")
    embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    client = QdrantClient(":memory:")
    client.create_collection("products", vectors_config=VectorParams(size=384, distance=Distance.COSINE))
    
    texts_to_embed = [f"{p['brand']} {p['generic_name']} {p['label_uses']}" for p in app_state["catalog"]]
    vectors = list(embedding_model.embed(texts_to_embed))
    
    points = [PointStruct(id=i, vector=vectors[i].tolist(), payload=p) for i, p in enumerate(app_state["catalog"])]
    client.upsert("products", points=points)
    
    app_state["embedding_model"] = embedding_model
    app_state["qdrant"] = client
    
    print("✅ System Ready!")
    yield # The app is now running and accepting requests
    print("Shutting down...")

app = FastAPI(title="Meridian Catalog Search", lifespan=lifespan)

# --- ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "healthy"}

@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    # 1. Find the Pharmacy (Tenancy)
    pharmacy = next((p for p in app_state["pharmacies"] if p["pharmacy_id"] == request.pharmacy_id), None)
    if not pharmacy:
        raise HTTPException(status_code=404, detail="Pharmacy not found")
        
    # Create a quick lookup dict for their inventory
    inventory = {item["product_id"]: item for item in pharmacy["inventory"]}
    
    # 2. Run BM25
    tokenized_query = request.query.lower().split()
    bm25_top = app_state["bm25"].get_top_n(tokenized_query, app_state["catalog"], n=20)
    
    # 3. Run Vector
    query_vector = list(app_state["embedding_model"].embed([request.query]))[0].tolist()
    vector_top_raw = app_state["qdrant"].query_points("products", query=query_vector, limit=20).points
    vector_top = [hit.payload for hit in vector_top_raw]
    
    # 4. RRF Fusion
    rrf_scores = {}
    k = 60
    for rank, product in enumerate(bm25_top):
        pid = product["product_id"]
        rrf_scores[pid] = rrf_scores.get(pid, 0) + (1 / (k + rank + 1))
    for rank, product in enumerate(vector_top):
        pid = product["product_id"]
        rrf_scores[pid] = rrf_scores.get(pid, 0) + (1 / (k + rank + 1))
        
    sorted_pids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    
    # 5. Build Results (Apply Filters & Safety)
    results = []
    seen_brands = set()
    
    for pid, score in sorted_pids:
        # TENANCY: Skip if this pharmacy doesn't stock it
        if pid not in inventory:
            continue
            
        product = next(p for p in app_state["catalog"] if p["product_id"] == pid)
        inv_item = inventory[pid]
        
        # FILTERS
        if request.category and product["category"] != request.category:
            continue
        if request.in_stock_only and inv_item["stock"] <= 0:
            continue
            
        # DEDUPLICATION
        if product["brand"] in seen_brands:
            continue
        seen_brands.add(product["brand"])
        
        # SAFETY WARNING
        warning = None
        if product["restricted"]:
            warning = "Age restricted. Requires ID and in-store purchase."
            
        results.append(ProductResult(
            product_id=pid,
            brand=product["brand"],
            generic_name=product["generic_name"],
            price=inv_item["price"],
            stock=inv_item["stock"],
            warning=warning,
            is_restricted=product["restricted"]
        ))
        
        if len(results) >= 5: # Return top 5
            break
            
    return SearchResponse(results=results) 