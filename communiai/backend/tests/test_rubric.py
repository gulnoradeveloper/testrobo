from app.services.evaluation.rubric import RUBRICS, aggregate, aggregate_readiness, get_rubric, weakest_criteria


def _c(code, score, assessed=True):
    return {"code": code, "score": score, "assessed": assessed, "evidence": "dalil"}


def test_rubric_max_is_100():
    r = get_rubric("1.0")
    assert r.max_total == 100
    assert [c.max_score for c in r.criteria] == [20, 20, 20, 15, 15, 10]


def test_full_marks_and_levels():
    r = RUBRICS["1.0"]
    full = [[_c("K1", 20), _c("K2", 20), _c("K3", 20), _c("K4", 15), _c("K5", 15)]]
    agg = aggregate(r, full, [_c("K6", 10)])
    assert agg["total_score"] == 100 and agg["max_applicable_score"] == 100 and agg["coverage"] == 1.0
    assert agg["level"] == "Yetuk"
    assert r.level_for(86) == "Yetuk" and r.level_for(85.9) == "Mas'uliyatli"
    assert r.level_for(71) == "Mas'uliyatli" and r.level_for(70.9) == "Shakllanayotgan"
    assert r.level_for(56) == "Shakllanayotgan" and r.level_for(55.9) == "Intiluvchan"


def test_unassessed_is_not_zero():
    r = RUBRICS["1.0"]
    agg = aggregate(r, [[_c("K1", 10), _c("K2", 10), _c("K3", 0, assessed=False), _c("K4", 15), _c("K5", 15)]])
    crit = {c["code"]: c for c in agg["criteria"]}
    assert crit["K3"]["assessed"] is False and crit["K3"]["score"] is None
    assert crit["K6"]["status_label"] == "Hali baholanmagan"
    assert agg["max_applicable_score"] == 70  # K3 (20) and K6 (10) excluded
    assert agg["total_score"] == 50
    assert agg["coverage"] == 0.7
    assert agg["percent"] == round(100 * 50 / 70, 1)


def test_average_across_answers_and_clamping():
    r = RUBRICS["1.0"]
    agg = aggregate(r, [[_c("K1", 10)], [_c("K1", 20)], [_c("K1", 99)]])
    k1 = agg["criteria"][0]
    assert k1["score"] == round((10 + 20 + 20) / 3, 1)  # 99 clamped to 20
    assert k1["observations"] == 3


def test_ai_cannot_inject_k6_via_answers():
    r = RUBRICS["1.0"]
    agg = aggregate(r, [[_c("K1", 10), _c("K6", 10)]])
    assert {c["code"]: c for c in agg["criteria"]}["K6"]["assessed"] is False


def test_weakest_and_comparability():
    r = RUBRICS["1.0"]
    answers = [[_c("K1", 18), _c("K2", 10), _c("K3", 6), _c("K4", 12), _c("K5", 12)]]
    a1, a2 = aggregate(r, answers), aggregate(r, answers)
    assert a1 == a2  # same evaluations -> same results (deterministic backend scoring)
    assert weakest_criteria(a1) == ["K3", "K2"]


def test_readiness_is_separate():
    assert aggregate_readiness([]) ["assessed"] is False
    agg = aggregate_readiness([{"assessed": True, "score": 7}, {"assessed": True, "score": 9},
                               {"assessed": False, "score": 0}])
    assert agg["percent"] == 80.0 and agg["observations"] == 2


def test_empty_aggregate():
    agg = aggregate(RUBRICS["1.0"], [])
    assert agg["max_applicable_score"] == 0 and agg["level"] == "Baholanmagan"
