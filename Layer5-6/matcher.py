def hamming(h1, h2):
    return sum(c1 != c2 for c1, c2 in zip(h1, h2))


def compute_similarity(original_hash, hashes):
    scores = []

    for h in hashes:
        dist = hamming(original_hash, h)
        similarity = 1 - (dist / 64)   # normalize
        scores.append(similarity)

    return max(scores)   # best match