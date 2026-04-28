import yt_dlp

def crawl_youtube(keywords):
    results = []

    with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
        for kw in keywords:
            data = ydl.extract_info(f"ytsearch3:{kw}", download=False)
            for v in data['entries']:
                results.append({
                    "url": f"https://youtube.com/watch?v={v['id']}",
                    "title": v['title'],
                    "platform": "youtube"
                })

    return results


# def crawl_web(keywords):
#     results = []
#     for kw in keywords:
#         results.append({
#             "url": f"https://example.com/{kw}",
#             "title": kw,
#             "platform": "web"
#         })
#     return results

def crawl_all(metadata):
    keywords = metadata.get("keywords", []) + [metadata.get("title", "")]
    
    data = []
    data += crawl_youtube(keywords)
    
    unique = {}
    for item in data:
        unique[item["url"]] = item

    return list(unique.values())

    return data
    
    