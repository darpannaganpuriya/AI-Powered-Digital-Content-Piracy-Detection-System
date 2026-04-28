def hamming(h1, h2):
    distance = 0
    min_len = min(len(h1), len(h2))
    for i in range(min_len):
        if h1[i] != h2[i]:
            distance += 1
    distance += abs(len(h1) - len(h2))
    return distance


def compute_similarity(original_hash, hashes):
    similarities = []
    for h in hashes:
        hamming_distance = hamming(original_hash, h)
        similarity = 1 - (hamming_distance / 64)
        similarities.append(similarity)
    return max(similarities) if similarities else 0.0


def match_against_reference(reference_hash: str, hashes: list[str]) -> float:
    return compute_similarity(reference_hash, hashes)
