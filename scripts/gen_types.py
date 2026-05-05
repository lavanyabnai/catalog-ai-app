#!/usr/bin/env python3
"""Start the API server briefly, generate OpenAPI TypeScript types, then stop.

Cross-platform replacement for the `pkill`-based approach in the Makefile.
Usage: python scripts/gen_types.py
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "apps" / "api"
OUT_FILE = str(ROOT / "packages" / "shared" / "types.ts")
PORT = 8001
URL = f"http://localhost:{PORT}/openapi.json"


def main() -> int:
    print(f"Starting API server on :{PORT}...")
    server = subprocess.Popen(
        ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(PORT)],
        cwd=API_DIR,
    )
    try:
        # Give the server time to start
        time.sleep(4)
        print(f"Generating TypeScript types from {URL}...")
        result = subprocess.run(
            ["pnpm", "dlx", "openapi-typescript", URL, "-o", OUT_FILE],
            cwd=ROOT,
        )
        return result.returncode
    finally:
        print("Stopping API server...")
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    sys.exit(main())
