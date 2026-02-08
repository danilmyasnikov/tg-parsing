"""Entry point for running the web UI."""

import uvicorn


def main():
    """Run the web UI server."""
    uvicorn.run(
        "webui.backend.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
