# MCP Documentation Server

A Model Context Protocol (MCP) server that provides AI assistants with the ability to search and retrieve documentation from popular Python libraries including LangChain, LlamaIndex, and OpenAI.

## Features

- **Documentation Search**: Search through official documentation for supported libraries
- **Web Scraping**: Fetches and parses documentation content from official sources
- **MCP Integration**: Works seamlessly with MCP-compatible AI assistants
- **Error Handling**: Robust error handling with comprehensive logging
- **Environment Configuration**: Easy setup with environment variables

## Supported Libraries

- **LangChain** - `python.langchain.com/docs`
- **LlamaIndex** - `python.llama_index.com/docs`
- **OpenAI** - `platform.openai.com/docs`

## Project Structure

```
mcp/
├── src/
│   ├── claude_invoke/           # Claude AI integration utilities
│   │   └── invoke.py
│   ├── config/                  # Configuration files
│   ├── mcp_server/             # Main MCP server implementation
│   │   ├── main.py             # Main server entry point
│   │   ├── pyproject.toml      # Project dependencies
│   │   ├── uv.lock            # Lock file for dependencies
│   │   └── logs/              # Server logs
│   └── utils/
│       └── logger/            # Logging utilities
│           ├── logging_manager.py
│           └── logging.py
├── .env                       # Environment variables
├── .gitignore
└── README.md
```

## Prerequisites

- **Python 3.12+**
- **uv** (Python package manager)
- **Serper API Key** (for web search functionality)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd mcp
   ```

2. **Install dependencies**:
   ```bash
   cd src/mcp_server
   uv sync
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```env
   SERPER_API_KEY=your_serper_api_key_here
   ```

## Configuration

### For VS Code with Claude Desktop

1. **Configure the MCP server** using the Command Palette:
   - Open Command Palette (`Ctrl+Shift+P`)
   - Run `MCP: Add Server`
   - Enter the following configuration:
     - **Server Name**: `documentation`
     - **Command**: `uv`
     - **Arguments**:
       - `--directory`
       - `E:/CodeBase/GitHub/mcp`
       - `run`
       - `src/mcp_server/main.py`

2. **Enable MCP and Agent mode** in VS Code settings:
   ```json
   {
     "chat.mcp.enabled": true,
     "chat.agent.enabled": true
   }
   ```

### For Claude Desktop

Add to your Claude configuration file:

```json
{
  "mcpServer": {
    "documentation": {
      "command": "uv",
      "args": [
        "--directory",
        "E:/CodeBase/GitHub/mcp",
        "run",
        "src/mcp_server/main.py"
      ]
    }
  }
}
```

## Usage

Once configured, the MCP server provides the following tool:

### `get_docs(query: str, library: str)`

Search documentation for a specific library.

**Parameters**:
- `query`: Search query (e.g., "vector store", "embeddings")
- `library`: Library to search (`"langchain"`, `"llama_index"`, or `"openai"`)

**Example Usage**:
```
Can you search for information about Chroma vector database in LangChain?
```

The assistant will use the `get_docs` tool to search LangChain documentation and return relevant information.

## Development

### Running the Server Standalone

For testing and development:

```bash
cd E:/CodeBase/GitHub/mcp
uv run src/mcp_server/main.py
```

### Logging

The server includes comprehensive logging:
- **Console output**: Formatted logs to stderr for debugging
- **File logging**: Detailed logs saved to `src/mcp_server/logs/general/`
- **Structured logging**: JSON-formatted data logging for analysis

### Dependencies

Key dependencies (see `src/mcp_server/pyproject.toml`):
- **fastmcp**: MCP server framework
- **httpx**: HTTP client for web requests
- **beautifulsoup4**: HTML parsing
- **python-dotenv**: Environment variable management
- **loguru**: Advanced logging

## API Integration

The server uses the [Serper API](https://serper.dev/) for web search functionality. You'll need to:

1. Sign up for a Serper API account
2. Get your API key
3. Add it to your `.env` file

## Troubleshooting

### Common Issues

1. **Module not found errors**:
   - Ensure you're running from the project root directory
   - Check that all dependencies are installed with `uv sync`

2. **MCP server not appearing**:
   - Verify MCP is enabled in your settings
   - Check server status with `MCP: List Servers`
   - Try `MCP: Reset Cached Tools`

3. **API errors**:
   - Edit .env and add your actual API key
   - Get your API key from https://serper.dev/
   - Verify your `SERPER_API_KEY` is correctly set
   - Check network connectivity
   - Review logs in the `logs/general/` directory

### Debug Mode

The server includes extensive debug logging. Check the log files in `src/mcp_server/logs/general/` for detailed error information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions:
- Check the logs in `src/mcp_server/logs/general/`
- Review the troubleshooting section above
- Open an issue in the repository

---

**Note**: This MCP server is designed to work with AI assistants that support the Model Context Protocol. Make sure your AI assistant has MCP support enabled and properly configured.