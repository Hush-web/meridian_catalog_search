import json
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding

def load_catalog():
    with open("catalog.json", "r") as f:
        return json.load(f)

def main():
    print("Loading catalog...")
    catalog = load_catalog()

    # 1. Initialize the Embedding Model 
    # (This downloads a small 130MB model to your PC the first time)
    print("Loading embedding model...")
    embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

    # 2. Initialize Qdrant in-memory
    print("Initializing Qdrant...")
    client = QdrantClient(":memory:")
    
    # 3. Create a collection (384 dimensions for this specific model)
    client.create_collection(
        collection_name="products",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )

    # 4. Prepare the data
    print("Embedding 300 products (this takes a few seconds)...")
    texts_to_embed = []
    for product in catalog:
        # We combine the brand, generic name, and uses so the AI understands the context
        text = f"{product['brand']} {product['generic_name']} {product['label_uses']}"
        texts_to_embed.append(text)

    # Convert all 300 texts into vectors (lists of numbers)
    vectors = list(embedding_model.embed(texts_to_embed))

    # 5. Upload to Qdrant
    points = []
    for i, product in enumerate(catalog):
        points.append(
            PointStruct(
                id=i, 
                vector=vectors[i].tolist(),
                payload=product # Store the whole product dict
            )
        )
    
    client.upsert(collection_name="products", points=points)
    print("✅ Qdrant is ready!")

    # --- TEST IT ---
    # Notice we are searching for a concept that might NOT be in the text
    query = "allergy medicine"
    print(f"\nSearching for: '{query}'")
    
    # Embed the query
    query_vector = list(embedding_model.embed([query]))[0].tolist()
    
    # Search Qdrant
    results = client.query_points(
        collection_name="products",
        query=query_vector,
        limit=3
    ).points

    # Print the top 3 results
    for res in results:
        product = res.payload
        print(f"- {product['brand']} ({product['generic_name']}) | Score: {res.score:.4f}")
        print(f"  Uses: {product['label_uses']}")

if __name__ == "__main__":
    main()