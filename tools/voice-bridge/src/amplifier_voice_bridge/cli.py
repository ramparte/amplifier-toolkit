"""CLI for Amplifier Voice Bridge."""

import argparse
import sys


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Amplifier Voice Bridge - Remote voice control for Amplifier sessions"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start the voice bridge server")
    start_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    start_parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port to bind to (default: 8765)",
    )
    start_parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in mock mode (no Amplifier dependency)",
    )
    start_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    # Test command
    test_parser = subparsers.add_parser("test", help="Test the server connection")
    test_parser.add_argument(
        "--url",
        default="http://localhost:8765",
        help="Server URL to test",
    )
    test_parser.add_argument(
        "--prompt",
        default="Hello, this is a test.",
        help="Test prompt to send",
    )

    args = parser.parse_args()

    if args.command == "start":
        start_server(args)
    elif args.command == "test":
        test_connection(args)
    else:
        parser.print_help()
        sys.exit(1)


def start_server(args):
    """Start the voice bridge server."""
    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn not installed. Run: pip install uvicorn[standard]")
        sys.exit(1)

    print(f"Starting Amplifier Voice Bridge on {args.host}:{args.port}")
    print(f"Mock mode: {args.mock}")
    print()
    print("Endpoints:")
    print(f"  POST http://{args.host}:{args.port}/chat - Voice interaction")
    print(f"  GET  http://{args.host}:{args.port}/health - Health check")
    print(f"  GET  http://{args.host}:{args.port}/sessions - List sessions")
    print()
    print("For iOS Shortcut, use your Tailscale IP or MagicDNS hostname.")
    print()

    if args.mock:
        print("Running in MOCK mode - responses will be echoed back.")
        print("Use POST /mock/chat for testing.")
        print()

    uvicorn.run(
        "amplifier_voice_bridge.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def test_connection(args):
    """Test the server connection."""
    try:
        import httpx
    except ImportError:
        print("Error: httpx not installed. Run: pip install httpx")
        sys.exit(1)

    url = f"{args.url}/chat"
    print(f"Testing connection to {url}")
    print(f"Prompt: {args.prompt}")
    print()

    try:
        response = httpx.post(
            url,
            json={"prompt": args.prompt, "session": "default"},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        print("Success!")
        print(f"Response: {data.get('text', 'No text in response')}")
        print(f"Session: {data.get('session_id')}")
        print(f"Execution time: {data.get('execution_time', 0):.2f}s")
    except httpx.ConnectError:
        print(f"Error: Could not connect to {args.url}")
        print("Make sure the server is running.")
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        print(f"Error: Server returned {e.response.status_code}")
        print(f"Details: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
