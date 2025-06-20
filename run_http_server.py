#!/usr/bin/env python3
"""
Flexible MCP Server
-------------------
Runs as HTTP server for standalone use, or stdio for Claude Desktop integration.
"""
import os
import sys
import signal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the MCP server
from advanced_mcp_server import mcp

def signal_handler(sig, frame):
    """Handle graceful shutdown on SIGINT"""
    print("\nShutting down MCP server gracefully...", file=sys.stderr)
    sys.exit(0)

def main():
    """Run the MCP server in appropriate mode"""
    # Register signal handler for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Detect if we're being called by Claude Desktop (stdin is a pipe)
    # or if MCP_TRANSPORT is explicitly set to stdio
    transport = os.environ.get("MCP_TRANSPORT", "auto")
    
    if transport == "stdio" or (transport == "auto" and not sys.stdin.isatty()):
        # Running in stdio mode (Claude Desktop)
        print("🔌 Starting MCP Server in STDIO mode for Claude Desktop...", file=sys.stderr)
        
        # Set up API keys info
        if os.environ.get("OPENWEATHER_API_KEY"):
            print("✅ OpenWeather API key found", file=sys.stderr)
        else:
            print("⚠️ No OpenWeather API key found. Using mock weather data.", file=sys.stderr)
            
        if os.environ.get("OPENAI_API_KEY"):
            print("✅ OpenAI API key found", file=sys.stderr)
        else:
            print("⚠️ No OpenAI API key found. Web search will use basic fallback.", file=sys.stderr)
        
        try:
            # Run with stdio transport for Claude Desktop
            mcp.run(transport="stdio")
        except Exception as e:
            print(f"❌ Error in stdio mode: {e}", file=sys.stderr)
            return 1
    
    else:
        # Running in HTTP server mode
        host = os.environ.get("MCP_HOST", "localhost")
        port = int(os.environ.get("MCP_PORT", 8000))
        transport_mode = "streamable-http"
        
        print(f"🚀 Starting MCP HTTP Server...", file=sys.stderr)
        print(f"📡 Host: {host}", file=sys.stderr)
        print(f"🔌 Port: {port}", file=sys.stderr)
        print(f"🌐 URL: http://{host}:{port}", file=sys.stderr)
        print(f"🔧 Transport: {transport_mode}", file=sys.stderr)
        
        # Set up API keys info
        if os.environ.get("OPENWEATHER_API_KEY"):
            print("✅ OpenWeather API key found", file=sys.stderr)
        else:
            print("⚠️ No OpenWeather API key found. Using mock weather data.", file=sys.stderr)
            
        if os.environ.get("OPENAI_API_KEY"):
            print("✅ OpenAI API key found", file=sys.stderr)
        else:
            print("⚠️ No OpenAI API key found. Web search will use basic fallback.", file=sys.stderr)
        
        print(f"🌍 Server running at: http://{host}:{port}", file=sys.stderr)
        print("="*60, file=sys.stderr)
        
        try:
            # Run the server with HTTP transport
            mcp.run(
                transport=transport_mode,
                host=host,
                port=port
            )
        except Exception as e:
            print(f"❌ Error starting HTTP server: {e}", file=sys.stderr)
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 