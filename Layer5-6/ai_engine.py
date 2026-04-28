def detect_piracy(title, similarity, ownership_verified):
    title = title.lower()

    if similarity > 0.9:
        return "PIRACY", 0.95

    elif similarity > 0.75:
        if "full" in title or "free" in title or "live" in title:
            return "PIRACY", 0.9
        return "SUSPICIOUS", 0.7

    elif similarity > 0.5:
        return "POSSIBLE", 0.6

    else:
        return "SAFE", 0.5