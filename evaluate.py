import json
import time
from search_service import SearchService

def calculate_mrr(results, expected_brand):
    """Mean Reciprocal Rank: 1/rank of the first correct hit."""
    for rank, product in enumerate(results):
        if product["brand"].lower() == expected_brand.lower():
            return 1.0 / (rank + 1)
    return 0.0

def evaluate():
    print("Initializing Search Service...")
    engine = SearchService()
    
    with open("eval_queries.json", "r") as f:
        queries = json.load(f)
        
    print(f"Loaded {len(queries)} test queries.\n")
    
    # Metrics
    bm25_recall, vector_recall, hybrid_recall = 0, 0, 0
    bm25_mrr, vector_mrr, hybrid_mrr = 0.0, 0.0, 0.0
    
    # Timing
    bm25_times, vector_times, hybrid_times = [], [], []
    
    PHARMACY = "pharm_1" # Test everything against one pharmacy
    
    print(f"{'Query':<25} | {'BM25':<5} | {'Vector':<6} | {'Hybrid':<6}")
    print("-" * 50)
    
    for item in queries:
        q = item["query"]
        expected = item["expected_brand"]
        
        # --- BM25 ---
        t0 = time.perf_counter()
        r_bm25 = engine.bm25_search(q, PHARMACY, limit=10)
        bm25_times.append((time.perf_counter() - t0) * 1000)
        
        # --- VECTOR ---
        t0 = time.perf_counter()
        r_vec = engine.vector_search(q, PHARMACY, limit=10)
        vector_times.append((time.perf_counter() - t0) * 1000)
        
        # --- HYBRID ---
        t0 = time.perf_counter()
        r_hyb = engine.hybrid_search(q, PHARMACY, limit=10)
        hybrid_times.append((time.perf_counter() - t0) * 1000)
        
        # --- CALCULATE METRICS ---
        # Recall@10 (Did it find the brand in the top 10?)
        hit_bm25 = 1 if any(p["brand"].lower() == expected.lower() for p in r_bm25) else 0
        hit_vec = 1 if any(p["brand"].lower() == expected.lower() for p in r_vec) else 0
        hit_hyb = 1 if any(p["brand"].lower() == expected.lower() for p in r_hyb) else 0
        
        bm25_recall += hit_bm25
        vector_recall += hit_vec
        hybrid_recall += hit_hyb
        
        # MRR
        bm25_mrr += calculate_mrr(r_bm25, expected)
        vector_mrr += calculate_mrr(r_vec, expected)
        hybrid_mrr += calculate_mrr(r_hyb, expected)
        
        print(f"{q[:23]:<25} | {hit_bm25:<5} | {hit_vec:<6} | {hit_hyb:<6}")

    total = len(queries)
    
    print("\n" + "="*50)
    print("FINAL EVALUATION RESULTS")
    print("="*50)
    
    print(f"Recall@10 (Higher is better):")
    print(f"  BM25:   {bm25_recall / total * 100:.1f}%")
    print(f"  Vector: {vector_recall / total * 100:.1f}%")
    print(f"  Hybrid: {hybrid_recall / total * 100:.1f}%")
    
    print(f"\nMRR (Mean Reciprocal Rank - Higher is better):")
    print(f"  BM25:   {bm25_mrr / total:.3f}")
    print(f"  Vector: {vector_mrr / total:.3f}")
    print(f"  Hybrid: {hybrid_mrr / total:.3f}")
    
    print(f"\nAverage Latency (ms):")
    print(f"  BM25:   {sum(bm25_times) / total:.2f} ms")
    print(f"  Vector: {sum(vector_times) / total:.2f} ms")
    print(f"  Hybrid: {sum(hybrid_times) / total:.2f} ms")

if __name__ == "__main__":
    evaluate()