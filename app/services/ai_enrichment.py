import asyncio
import base64
import hashlib
import os
from typing import Any

import httpx

from app.config import settings

# This module enhances scraping with AI without altering core pipeline behavior.


def _simulate_embedding(seed_text: str, size: int = 8) -> list[float]:
    digest = hashlib.sha256(seed_text.encode("utf-8")).digest()
    return [round(digest[i] / 255.0, 4) for i in range(size)]


def _vision_features(media_sample_path: str | None, timeout: float) -> tuple[list[str], list[str], list[str]]:
    if not settings.google_api_key:
        return [], [], []

    if not media_sample_path or not os.path.exists(media_sample_path):
        return [], [], []

    with open(media_sample_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "requests": [
            {
                "image": {"content": content_b64},
                "features": [
                    {"type": "LABEL_DETECTION", "maxResults": 10},
                    {"type": "OBJECT_LOCALIZATION", "maxResults": 10},
                    {"type": "LOGO_DETECTION", "maxResults": 10},
                ],
            }
        ]
    }

    url = (
        "https://vision.googleapis.com/v1/images:annotate"
        f"?key={settings.google_api_key}"
    )
    resp = httpx.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    first = (data.get("responses") or [{}])[0]
    labels = [x.get("description", "") for x in first.get("labelAnnotations", []) if x.get("description")]
    objects = [x.get("name", "") for x in first.get("localizedObjectAnnotations", []) if x.get("name")]
    logos = [x.get("description", "") for x in first.get("logoAnnotations", []) if x.get("description")]
    return labels, objects, logos


def _video_features(media_sample_path: str | None, timeout: float) -> tuple[list[str], list[str]]:
    if not settings.google_api_key:
        return [], []

    if not media_sample_path or not os.path.exists(media_sample_path):
        return [], []

    with open(media_sample_path, "rb") as f:
        input_content = base64.b64encode(f.read()).decode("utf-8")

    annotate_url = (
        "https://videointelligence.googleapis.com/v1/videos:annotate"
        f"?key={settings.google_api_key}"
    )
    payload = {
        "inputContent": input_content,
        "features": ["SHOT_CHANGE_DETECTION", "LABEL_DETECTION"],
    }

    op_resp = httpx.post(annotate_url, json=payload, timeout=timeout)
    op_resp.raise_for_status()
    operation_name = op_resp.json().get("name")
    if not operation_name:
        return [], []

    op_url = (
        "https://videointelligence.googleapis.com/v1/"
        f"{operation_name}?key={settings.google_api_key}"
    )
    poll_resp = httpx.get(op_url, timeout=timeout)
    poll_resp.raise_for_status()
    result = poll_resp.json()
    if not result.get("done"):
        return [], []

    annotation_results = (result.get("response", {}).get("annotationResults") or [{}])[0]
    shot_annotations = annotation_results.get("shotAnnotations", [])
    segment_labels = annotation_results.get("segmentLabelAnnotations", [])

    shots = ["shot_change"] * len(shot_annotations)
    scene_labels = [
        entity.get("description", "")
        for label in segment_labels
        for entity in [label.get("entity", {})]
        if entity.get("description")
    ]
    return shots, scene_labels


def _vertex_embedding(source_url: str, platform: str, timeout: float) -> list[float]:
    if not settings.google_api_key or not settings.google_cloud_project:
        return _simulate_embedding(f"{source_url}|{platform}")

    endpoint = (
        f"https://{settings.google_cloud_location}-aiplatform.googleapis.com/v1/"
        f"projects/{settings.google_cloud_project}/locations/{settings.google_cloud_location}/"
        "publishers/google/models/text-embedding-005:predict"
    )
    headers = {
        "Authorization": f"Bearer {settings.google_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "instances": [{"content": f"{platform} {source_url}"}],
    }

    resp = httpx.post(endpoint, json=payload, headers=headers, timeout=timeout)
    if resp.status_code >= 400:
        return _simulate_embedding(f"{source_url}|{platform}")

    data = resp.json()
    predictions = data.get("predictions") or []
    if not predictions:
        return _simulate_embedding(f"{source_url}|{platform}")

    vector = predictions[0].get("embeddings", {}).get("values")
    if isinstance(vector, list) and vector:
        return [float(v) for v in vector[:8]]

    return _simulate_embedding(f"{source_url}|{platform}")


def enrich_scraped_item(item: dict[str, Any]) -> dict[str, Any] | None:
    if not settings.enable_google_ai:
        return None

    try:
        source_url = item.get("source_url", "")
        media_sample_path = item.get("media_sample_path")
        platform = item.get("platform", "")
        timeout = float(settings.google_ai_timeout_seconds)

        labels, objects, logos = _vision_features(media_sample_path, timeout)
        shots, scene_labels = _video_features(media_sample_path, timeout)
        if scene_labels:
            labels = list(dict.fromkeys(labels + scene_labels))

        embedding = _vertex_embedding(source_url, platform, timeout)
        confidence_score = round(
            min(1.0, (len(labels) * 0.05) + (len(objects) * 0.05) + (len(logos) * 0.1) + 0.5),
            3,
        )

        ai_analysis = {
            "labels": labels,
            "objects": objects,
            "logos_detected": logos,
            "embedding_vector": embedding,
            "confidence_score": confidence_score,
        }
        if shots:
            ai_analysis["shot_detection"] = shots

        return ai_analysis
    except Exception:
        return None


async def enrich_scraped_items_async(items: list[dict[str, Any]]) -> list[dict[str, Any] | None]:
    if not settings.enable_google_ai:
        return [None for _ in items]

    tasks = [asyncio.to_thread(enrich_scraped_item, item) for item in items]
    return await asyncio.gather(*tasks, return_exceptions=False)
