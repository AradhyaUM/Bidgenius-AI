import os
from exa_py import Exa

client = Exa(api_key=os.getenv("EXA_API_KEY"))

def search_tenders(query):
    result = client.search_and_contents(
        query,
        type="auto",
        include_domains=["gov.in", "etenders.gov.in"],
        text={"max_characters": 10000},
        num_results=5
    )
    return result.results