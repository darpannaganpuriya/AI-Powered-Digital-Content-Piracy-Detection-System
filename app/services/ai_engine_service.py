SIMILARITY_THRESHOLD = 0.6


def detect_piracy(title, similarity, ownership_verified):
    title_lower = title.lower()

    if similarity > 0.9:
        return "PIRACY", 0.95
    if similarity > 0.75 and (
        "full" in title_lower or "free" in title_lower or "live" in title_lower
    ):
        return "PIRACY", 0.9
    if similarity > 0.75:
        return "SUSPICIOUS", 0.7
    if similarity > 0.5:
        return "POSSIBLE", 0.6
    return "SAFE", 0.5
