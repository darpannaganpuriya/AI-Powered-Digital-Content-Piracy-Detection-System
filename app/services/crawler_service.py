from typing import List

import yt_dlp


def crawl_youtube(keywords):
    results = []
    for kw in keywords:
        with yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True}) as ydl:
            search_result = ydl.extract_info(f"ytsearch3:{kw}", download=False)
            for entry in search_result.get("entries", []):
                url = entry.get("url")
                if url and not url.startswith("http"):
                    url = f"https://www.youtube.com/watch?v={url}"
                results.append(
                    {
                        "url": url,
                        "title": entry.get("title", ""),
                        "platform": "youtube",
                    }
                )
    return results


def crawl_all(metadata):
    keywords = metadata.get("keywords", [])
    title = metadata.get("title", "")
    all_keywords = list(keywords)
    if title:
        all_keywords.append(title)
    return crawl_youtube(all_keywords)


def crawl_for_content(metadata: dict) -> List[dict]:
    return crawl_all(metadata)
