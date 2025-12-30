import indb_data

def test_search(query):
    print(f"\nSearching for: '{query}'")
    results = indb_data.search_indb(query, max_results=5)
    if not results:
        print("No results found.")
        return
    for i, res in enumerate(results, 1):
        print(f"{i}. {res['description']} (Score: {res['score']})")

if __name__ == "__main__":
    # Test cases
    test_queries = [
        "Chicken Tikka",       # Exact/Substring
        "chiken tika",         # Typo
        "aloogobi",            # Missing space
        "paneer butter",       # Substring
        "massala",             # Typo
        "biryani"              # Common term
    ]
    
    for q in test_queries:
        test_search(q)
