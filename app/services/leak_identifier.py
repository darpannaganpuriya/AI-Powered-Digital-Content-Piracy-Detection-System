from app.models.schemas import LeakResult


def identify_leak(watermark_id: str | None, platform: str) -> LeakResult:
    watermark = (watermark_id or "").lower()

    if "broadcaster" in watermark:
        leak_type = "BROADCASTER_LEAK"
        leak_severity = "HIGH"
    elif "user_" in watermark:
        leak_type = "USER_LEAK"
        leak_severity = "MEDIUM"
    elif "platform_" in watermark:
        leak_type = "PLATFORM_LEAK"
        leak_severity = "HIGH"
    else:
        leak_type = "UNKNOWN"
        leak_severity = "LOW"

    region_map = {
        "youtube": "Global",
        "hotstar": "India",
        "telegram": "India/Russia",
    }
    region = region_map.get(platform.lower(), "Unknown")

    return LeakResult(
        leak_type=leak_type,
        watermark_id=watermark_id,
        platform=platform,
        region=region,
        leak_severity=leak_severity,
    )
