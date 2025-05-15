import os
import httpx
import json
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from bs4 import BeautifulSoup

from src.utils.logger.logging import logger as logging

load_dotenv()

mcp = FastMCP()

USER_AGENT = "docs-app/1.0"
SERPER_URL = "https://google.serper.dev/search"

docs_urls = {
    "langchain": "python.langchain.com/docs",
    "llama_index": "python.llama_index.com/docs",
    "openai": "platform.openai.com/docs",
}


async def search_web(query: str) -> dict | None:
    logging.info("Searching the web...")
    payload = json.dumps({"q": query, "num": 2})

    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            logging.info("Sending search request...")
            logging.debug(f"Payload: {payload}")
            response = await client.post(
                SERPER_URL, headers=headers, data=payload, timeout=30.0
            )
            response.raise_for_status()
            if response.status_code == 200:
                logging.info("Search successful.")
            else:
                logging.error(f"Search failed with status code: {response.status_code}")
                return {"organic": []}
            return response.json()
        except httpx.TimeoutException:
            logging.error("Search request timed out.")
            return {"organic": []}


async def fetch_url(url: str):
    logging.info("Fetching URL...")
    logging.debug(f"Fetching URL: {url}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=30.0)
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text()
            logging.info("URL fetched successfully.")
            return text
        except httpx.TimeoutException:
            logging.error("Fetch request timed out.")
            return "Timeout error"


@mcp.tool()
async def get_docs(query: str, library: str):
    """
    Search the latest docs for a given query and library.
    Supports langchain, openai, and llama-index.

    Args:
    query: The query to search for (e.g. "Chroma DB")
    library: The library to search in (e.g. "langchain")

    Returns:
    Text from the docs
    """

    logging.info("Getting docs...")
    if library not in docs_urls:
        logging.error(f"Library {library} not supported.")
        raise ValueError(f"Library {library} not supported by this tool")

    query = f"site:{docs_urls[library]} {query}"
    results = await search_web(query)
    if len(results["organic"]) == 0:
        logging.error("No results found.")
        return "No results found"

    text = ""
    for result in results["organic"]:
        text += await fetch_url(result["link"])

    logging.info("Docs fetched successfully.")
    logging.debug(f"Fetched text: {text}")
    return text


if __name__ == "__main__":
    mcp.run(trannsport="stdio")
