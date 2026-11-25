from eval.answer import answer_correct


def test_correct_grade_is_correct():
    assert answer_correct("correct", False, False) is True


def test_abstention_is_correct_only_when_acceptable():
    assert answer_correct("abstained", True, True) is True
    assert answer_correct("abstained", True, False) is False


def test_other_grades_are_incorrect():
    assert answer_correct("partial", True, True) is False
    assert answer_correct("incorrect", False, True) is False
