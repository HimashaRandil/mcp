import os
import sys
import httpx
import json
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Add stderr logging for debugging
print("Starting MCP server...", file=sys.stderr)

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
print("Python path updated", file=sys.stderr)

# Try to import custom logger with error handling
try:
    from src.utils.logger.logging import logger as logging

    print("Custom logger imported successfully", file=sys.stderr)
except ImportError as e:
    print(f"Custom logger import failed: {e}", file=sys.stderr)
    print("Falling back to standard logging", file=sys.stderr)
    import logging

    logging.basicConfig(level=logging.INFO)
except Exception as e:
    print(f"Unexpected error importing logger: {e}", file=sys.stderr)
    import logging

    logging.basicConfig(level=logging.INFO)

print("Loading environment...", file=sys.stderr)
load_dotenv()
print("Environment loaded", file=sys.stderr)

print("Initializing FastMCP...", file=sys.stderr)
mcp = FastMCP()
print("FastMCP initialized", file=sys.stderr)

USER_AGENT = "docs-app/1.0"
SERPER_URL = "https://google.serper.dev/search"

docs_urls = {
    "langchain": "python.langchain.com/docs",
    "llama_index": "python.llama_index.com/docs",
    "openai": "platform.openai.com/docs",
}

# Check for required environment variables
serper_key = os.getenv("SERPER_API_KEY")
if not serper_key:
    print("WARNING: SERPER_API_KEY not found in environment", file=sys.stderr)
else:
    print("SERPER_API_KEY found", file=sys.stderr)


async def search_web(query: str) -> dict | None:
    print(f"Searching web: {query}", file=sys.stderr)
    payload = json.dumps({"q": query, "num": 2})

    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                SERPER_URL, headers=headers, data=payload, timeout=30.0
            )
            response.raise_for_status()
            if response.status_code == 200:
                print("Search successful", file=sys.stderr)
            else:
                print(
                    f"Search failed with status code: {response.status_code}",
                    file=sys.stderr,
                )
                return {"organic": []}
            return response.json()
        except httpx.TimeoutException:
            print("Search request timed out", file=sys.stderr)
            return {"organic": []}
        except Exception as e:
            print(f"Search error: {e}", file=sys.stderr)
            return {"organic": []}


async def fetch_url(url: str):
    print(f"Fetching URL: {url}", file=sys.stderr)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=30.0)
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text()
            print("URL fetched successfully", file=sys.stderr)
            return text
        except httpx.TimeoutException:
            print("Fetch request timed out", file=sys.stderr)
            return "Timeout error"
        except Exception as e:
            print(f"Fetch error: {e}", file=sys.stderr)
            return f"Error: {e}"


@mcp.tool()
async def get_docs(query: str, library: str):
    """
    Search the latest docs for a given query and library.
    Supports langchain, openai, and llama_index.

    Args:
        query: The query to search for (e.g. "Chroma DB")
        library: The library to search in (e.g. "langchain")

    Returns:
        Text from the docs
    """
    print(f"get_docs called: query={query}, library={library}", file=sys.stderr)

    if library not in docs_urls:
        error_msg = f"Library {library} not supported by this tool"
        print(error_msg, file=sys.stderr)
        raise ValueError(error_msg)

    search_query = f"site:{docs_urls[library]} {query}"
    results = await search_web(search_query)

    if not results or len(results.get("organic", [])) == 0:
        print("No results found", file=sys.stderr)
        return "No results found"

    text = ""
    for result in results["organic"]:
        page_text = await fetch_url(result["link"])
        text += page_text + "\n\n"

    print("Docs fetched successfully", file=sys.stderr)
    return text


if __name__ == "__main__":
    try:
        print("About to start FastMCP server...", file=sys.stderr)
        mcp.run(transport="stdio")
    except Exception as e:
        print(f"Fatal error in main: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
