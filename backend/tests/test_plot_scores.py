from eval.plot_scores import histogram


def test_histogram_buckets_scores_by_label():
    rows = [
        {"label": "relevant", "score": 0.95},
        {"label": "irrelevant", "score": 0.1},
        {"label": "irrelevant", "score": 0.3},
        {"label": "partial", "score": None},
    ]

    counts = histogram(rows)

    assert counts["relevant"]["0.8-1.0"] == 1
    assert counts["irrelevant"]["0.0-0.2"] == 1
    assert counts["irrelevant"]["0.2-0.4"] == 1
    assert sum(counts["partial"].values()) == 0
