import json
from rank_bm25 import BM25Okapi
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding

def load_catalog():
    with open("catalog.json", "r") as f:
        return json.load(f)

def reciprocal_rank_fusion(bm25_results, vector_results, k=60):
    """
    Combines two lists of results using RRF.
    k is a constant (usually 60) that dampens the effect of high ranks.
    """
    rrf_scores = {}
    
    # Score BM25 results
    for rank, product in enumerate(bm25_results):
        pid = product["product_id"]
        if pid not in rrf_scores:
            rrf_scores[pid] = 0
        rrf_scores[pid] += 1 / (k + rank + 1)
        
    # Score Vector results
    for rank, product in enumerate(vector_results):
        pid = product["product_id"]
        if pid not in rrf_scores:
            rrf_scores[pid] = 0
        rrf_scores[pid] += 1 / (k + rank + 1)
        
    # Sort by the new RRF score (descending)
    sorted_pids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_pids

def main():
    print("Initializing Hybrid Engine (this takes a moment)...")
    catalog = load_catalog()
    
    # 1. Setup BM25
    corpus = []
    for p in catalog:
        text = f"{p['brand']} {p['generic_name']} {p['active_ingredients']} {p['category']} {p['label_uses']}"
        corpus.append(text.lower().split())
    bm25 = BM25Okapi(corpus)
    
    # 2. Setup Vector
    embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    client = QdrantClient(":memory:")
    client.create_collection("products", vectors_config=VectorParams(size=384, distance=Distance.COSINE))
    
    texts_to_embed = [f"{p['brand']} {p['generic_name']} {p['label_uses']}" for p in catalog]
    vectors = list(embedding_model.embed(texts_to_embed))
    
    points = [PointStruct(id=i, vector=vectors[i].tolist(), payload=p) for i, p in enumerate(catalog)]
    client.upsert("products", points=points)
    print("✅ Hybrid Engine Ready!\n")

    # --- TEST IT ---
    # A tricky query: Exact brand + concept (misspelled)
    query = "advill for head pain" 
    print(f"Searching for: '{query}'\n")
    
    # A. Get BM25 Results (Top 10)
    tokenized_query = query.lower().split()
    bm25_top = bm25.get_top_n(tokenized_query, catalog, n=10)
    
    # B. Get Vector Results (Top 10)
    query_vector = list(embedding_model.embed([query]))[0].tolist()
    vector_top_raw = client.query_points("products", query=query_vector, limit=10).points
    vector_top = [hit.payload for hit in vector_top_raw]
    
    # C. Fuse them!
    fused_results = reciprocal_rank_fusion(bm25_top, vector_top)
    
    # D. Print the final Hybrid results (Deduplicated by Brand)
    seen_brands = set()
    count = 0
    
    print("--- Top Hybrid Results ---")
    for pid, score in fused_results:
        # Find the full product data
        product = next(p for p in catalog if p["product_id"] == pid)
        
        # Deduplicate so we don't show 3 identical Advils
        if product["brand"] not in seen_brands:
            seen_brands.add(product["brand"])
            print(f"{count + 1}. {product['brand']} ({product['generic_name']}) | Hybrid Score: {score:.4f}")
            print(f"   Uses: {product['label_uses']}")
            count += 1
            
        if count >= 5: # Only show top 5 unique brands
            break

if __name__ == "__main__":
    main()