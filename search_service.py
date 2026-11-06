import json
from rank_bm25 import BM25Okapi
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding

class SearchService:
    def __init__(self, catalog_path="catalog.json", pharmacies_path="pharmacies.json"):
        with open(catalog_path, "r") as f:
            self.catalog = json.load(f)
        with open(pharmacies_path, "r") as f:
            self.pharmacies = json.load(f)
            
        # Setup BM25
        self.corpus = []
        for p in self.catalog:
            text = f"{p['brand']} {p['generic_name']} {p['active_ingredients']} {p['category']} {p['label_uses']}"
            self.corpus.append(text.lower().split())
        self.bm25 = BM25Okapi(self.corpus)
        
        # Setup Vector
        self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        self.qdrant = QdrantClient(":memory:")
        self.qdrant.create_collection("products", vectors_config=VectorParams(size=384, distance=Distance.COSINE))
        
        texts_to_embed = [f"{p['brand']} {p['generic_name']} {p['label_uses']}" for p in self.catalog]
        vectors = list(self.embedding_model.embed(texts_to_embed))
        points = [PointStruct(id=i, vector=vectors[i].tolist(), payload=p) for i, p in enumerate(self.catalog)]
        self.qdrant.upsert("products", points=points)

    def get_inventory(self, pharmacy_id):
        pharmacy = next((p for p in self.pharmacies if p["pharmacy_id"] == pharmacy_id), None)
        if not pharmacy:
            return None
        return {item["product_id"]: item for item in pharmacy["inventory"]}

    def bm25_search(self, query, pharmacy_id, limit=10):
        inventory = self.get_inventory(pharmacy_id)
        tokenized_query = query.lower().split()
        # Get more results to allow for tenancy filtering
        raw_results = self.bm25.get_top_n(tokenized_query, self.catalog, n=50)
        
        results = []
        for p in raw_results:
            if p["product_id"] in inventory:
                results.append(p)
        return results[:limit]

    def vector_search(self, query, pharmacy_id, limit=10):
        inventory = self.get_inventory(pharmacy_id)
        query_vector = list(self.embedding_model.embed([query]))[0].tolist()
        raw_results = self.qdrant.query_points("products", query=query_vector, limit=50).points
        
        results = []
        for hit in raw_results:
            p = hit.payload
            if p["product_id"] in inventory:
                results.append(p)
        return results[:limit]

    def hybrid_search(self, query, pharmacy_id, limit=10):
        inventory = self.get_inventory(pharmacy_id)
        
        # Get 50 from each to fuse
        tokenized_query = query.lower().split()
        bm25_top = self.bm25.get_top_n(tokenized_query, self.catalog, n=50)
        
        query_vector = list(self.embedding_model.embed([query]))[0].tolist()
        vector_top_raw = self.qdrant.query_points("products", query=query_vector, limit=50).points
        vector_top = [hit.payload for hit in vector_top_raw]
        
        # RRF Fusion
        rrf_scores = {}
        k = 60
        for rank, product in enumerate(bm25_top):
            pid = product["product_id"]
            rrf_scores[pid] = rrf_scores.get(pid, 0) + (1 / (k + rank + 1))
        for rank, product in enumerate(vector_top):
            pid = product["product_id"]
            rrf_scores[pid] = rrf_scores.get(pid, 0) + (1 / (k + rank + 1))
            
        sorted_pids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for pid, score in sorted_pids:
            if pid in inventory:
                product = next(p for p in self.catalog if p["product_id"] == pid)
                results.append(product)
                if len(results) >= limit:
                    break
        return results