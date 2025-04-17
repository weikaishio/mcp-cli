from mcp.server.fastmcp import FastMCP
import argparse
import logging
import socket
import sys
import time

mcp = FastMCP("我的MCP Server", host="0.0.0.0", port=8000)

def setup_logging(verbose):
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        stream=sys.stdout
    )


@mcp.tool()
def greet(name: str) -> str:
    logging.debug(f"greet called with name={name}")
    return f"你好，{name}！"


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    setup_logging(args.verbose)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", 8000))
            logging.info("Port 8000 is available")
    except socket.error as e:
        logging.error("Port binding failed: %s", str(e))
        exit(1)

    time.sleep(1)

    try:
        logging.info("Starting MCP server...")
        mcp.run()
    except Exception as e:
        logging.error("Critical error: %s", str(e), exc_info=True)
        exit(1)