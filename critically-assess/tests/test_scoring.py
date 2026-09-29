import scoring

CRIT = [{"id": "cost", "weight": 0.5}, {"id": "speed", "weight": 0.5}]
SCORES = [
    {"option": "A", "criterion": "cost", "score": 5},
    {"option": "A", "criterion": "speed", "score": 1},
    {"option": "B", "criterion": "cost", "score": 3},
    {"option": "B", "criterion": "speed", "score": 4},
]


def test_weighted_totals():
    assert scoring.weighted_totals(CRIT, SCORES) == {"A": 3.0, "B": 3.5}


def test_weights_that_do_not_sum_to_one_are_normalized():
    doubled = [{"id": "cost", "weight": 2}, {"id": "speed", "weight": 2}]
    assert scoring.weighted_totals(doubled, SCORES) == scoring.weighted_totals(CRIT, SCORES)


def test_tie_returns_every_winner():
    assert scoring.winners({"A": 3.5, "B": 3.5, "C": 1.0}) == ["A", "B"]


def test_sensitivity_stable_for_small_shifts():
    assert all(r["flips"] == [] for r in scoring.sensitivity(CRIT, SCORES, delta=0.1))


def test_sensitivity_detects_winner_flip():
    # cost 0.5 -> 0.8, renormalized: A = 3.46, B = 3.38, so A overtakes B
    report = {r["criterion"]: r["flips"] for r in scoring.sensitivity(CRIT, SCORES, delta=0.3)}
    assert report["cost"] and report["cost"][0]["winners"] == ["A"]


def test_all_zero_weights_tie_instead_of_crashing():
    zero = [{"id": "cost", "weight": 0}, {"id": "speed", "weight": 0}]
    assert scoring.winners(scoring.weighted_totals(zero, SCORES)) == ["A", "B"]
