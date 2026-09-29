"""Weighted totals, winners and weight sensitivity. Mirrored in templates/report.html JS."""

TOLERANCE = 1e-6


def normalize(criteria):
    total = sum(c["weight"] for c in criteria)
    return {c["id"]: c["weight"] / total for c in criteria}


def weighted_totals(criteria, scores):
    weights = normalize(criteria)
    totals = {}
    for s in scores:
        totals[s["option"]] = totals.get(s["option"], 0.0) + weights[s["criterion"]] * s["score"]
    return totals


def winners(totals):
    best = max(totals.values())
    return sorted(k for k, v in totals.items() if abs(v - best) < TOLERANCE)


def sensitivity(criteria, scores, delta=0.1):
    base = winners(weighted_totals(criteria, scores))
    weights = normalize(criteria)
    report = []
    for cid in weights:
        flips = []
        for shift in (-delta, delta):
            shifted = [{"id": k, "weight": max(v + (shift if k == cid else 0.0), 0.0)} for k, v in weights.items()]
            if sum(c["weight"] for c in shifted) == 0:
                continue
            now = winners(weighted_totals(shifted, scores))
            if now != base:
                flips.append({"shift": shift, "winners": now})
        report.append({"criterion": cid, "flips": flips})
    return report
