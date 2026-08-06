"""Basic Scrapiq usage example.

Run the server first:
    cd scrapiq && scrapiq

Then in another terminal:
    python examples/basic.py
"""

import httpx


def main():
    base = "http://localhost:8001"

    # 1. Health check
    r = httpx.get(f"{base}/health")
    print("Health:", r.json())

    # 2. Extract clean markdown
    r = httpx.post(
        f"{base}/v1/extract",
        json={
            "url": "https://example.com",
            "format": "markdown",
        },
    )
    print("\nMarkdown extraction:")
    print(r.json())

    # 3. Extract structured fields
    r = httpx.post(
        f"{base}/v1/extract",
        json={
            "url": "https://news.ycombinator.com",
            "format": "json",
            "schema": {
                "properties": {
                    "title": {"type": "string"},
                    "headline": {"type": "string"},
                }
            },
        },
    )
    print("\nStructured extraction:")
    print(r.json())


if __name__ == "__main__":
    main()
