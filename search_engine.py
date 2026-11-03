import json
from rank_bm25 import BM25Okapi

def load_catalog():
    with open("catalog.json", "r") as f:
        return json.load(f)

def prepare_documents(catalog):
    corpus = []
    for product in catalog:
        # We combine the most important fields into one giant string
        # so the search engine can read it.
        text = f"{product['brand']} {product['generic_name']} {product['active_ingredients']} {product['category']} {product['label_uses']}"
        
        # BM25 needs a list of words (tokens), so we lowercase it and split by spaces
        tokens = text.lower().split()
        corpus.append(tokens)
    return corpus

def main():
    print("Loading catalog...")
    catalog = load_catalog()
    
    print("Preparing BM25 index...")
    corpus = prepare_documents(catalog)
    
    # Initialize the BM25 algorithm with our 300 products
    bm25 = BM25Okapi(corpus)
    
    # --- TEST IT ---
    # Let's search for a specific symptom
    query = "runny nose"
    print(f"\nSearching for: '{query}'")
    
    # Tokenize the query the exact same way we tokenized the products
    tokenized_query = query.lower().split()
    
    # Get the top 3 results
    top_docs = bm25.get_top_n(tokenized_query, catalog, n=3)
    
    # Print the results
    for doc in top_docs:
        print(f"- {doc['brand']} ({doc['generic_name']}) - ID: {doc['product_id']}")
        print(f"  Uses: {doc['label_uses']}")

if __name__ == "__main__":
    main()