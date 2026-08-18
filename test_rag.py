import sys
from rag_engine import TravelRAGEngine

# Ensure Windows terminal handles UTF-8 characters cleanly
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    print("========================================")
    print("     Travel RAG Engine - Test CLI      ")
    print("========================================")
    
    # 1. Initialize
    print("\n[1] Initializing RAG Engine...")
    engine = TravelRAGEngine()
    
    # 2. Ingest Data
    print("\n[2] Ingesting documents from data/ ...")
    ingest_res = engine.ingest_documents()
    print(f"Ingestion Result: {ingest_res}")
    
    # 3. Test Queries
    queries = [
        ("What are the best seafood places in Goa?", "Goa"),
        ("What is the best time to visit Bangalore?", "Bangalore"),
        ("Tell me about street food in Mumbai.", None)
    ]
    
    for q, dest in queries:
        print("\n" + "="*50)
        print(f"Query: '{q}' (Filter: {dest})")
        print("="*50)
        res = engine.generate_answer(q, destination_filter=dest)
        print(res["answer"])
        print("\nSources Used:")
        for s in res["sources"]:
            print(f"- {s['destination']} ({s['source']})")

if __name__ == "__main__":
    main()