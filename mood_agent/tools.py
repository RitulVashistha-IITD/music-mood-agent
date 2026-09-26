import requests


def search_songs(queries, limit: int = 1) -> dict:
    """Look up real songs on Apple's free iTunes catalog; return exact data.

    Call ONCE per request, passing ALL candidates as a list of "title artist"
    strings, e.g. ["The Middle Jimmy Eat World", "Brave Sara Bareilles"].

    Args:
        queries: List of "title artist" strings (a single string also works).
        limit: Results per query (default 1 = best match).
    Returns:
        {"results": {query: {"tracks": [...]}}}; each track has title, artist,
        apple_url (exact song page), preview_url (30s clip), artwork_url.
    """
    if isinstance(queries, str):
        queries = [queries]

    results = {}
    for q in queries:
        try:
            resp = requests.get(
                "https://itunes.apple.com/search",
                params={"term": q, "entity": "song", "limit": limit,
                        "country": "IN"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json().get("results", [])
        except Exception as e:
            results[q] = {"error": str(e), "tracks": []}
            continue

        tracks = [
            {
                "title": t.get("trackName"),
                "artist": t.get("artistName"),
                "apple_url": t.get("trackViewUrl"),
                "preview_url": t.get("previewUrl"),
                "artwork_url": t.get("artworkUrl100"),
            }
            for t in data if t.get("trackViewUrl")
        ]
        results[q] = {"tracks": tracks}
    return {"results": results}