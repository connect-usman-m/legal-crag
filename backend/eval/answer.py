def answer_correct(grade: str, abstained: bool, acceptable_abstain: bool) -> bool:
    return grade == "correct" or (grade == "abstained" and abstained and acceptable_abstain)
