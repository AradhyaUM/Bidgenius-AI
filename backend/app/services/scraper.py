
# -------------------------------
# 🔍 SEARCH TENDERS (TAVILY BASED)
# -------------------------------
def search_tenders(query, region):
    from tavily import TavilyClient
    import os

    tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    full_query = f"{query} {region} government tender last date bid pdf"

    print("🔍 Searching:", full_query)

    response = tavily.search(query=full_query, max_results=10)

    results = []

    for r in response.get("results", []):
        if ".pdf" in r.get("url", ""):
            results.append({
                "title": r.get("title"),
                "url": r.get("url"),
                "snippet": r.get("content")
            })

    return results