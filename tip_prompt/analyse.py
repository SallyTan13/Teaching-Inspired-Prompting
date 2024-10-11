from tip_prompt.quest import Question, QuestTypes
from tip_prompt.analyser.base_analyser import Analyser
from tip_prompt.analyser.judge_analyser import JudgeAnalyser
from tip_prompt.analyser.choice_analyser import ChoiceAnalyser
from tip_prompt.analyser.normal_analyser import SingleNormalAnalyser
from typing import Optional


def get_analyser(question: Question) -> Optional[Analyser]:
    """get analyser according to the type of the questions"""
    analyser = None
    if question.qtype == QuestTypes.JUDGE:
        analyser = JudgeAnalyser(question)
    elif question.qtype == QuestTypes.CHOICE:
        analyser = ChoiceAnalyser(question)
    elif question.qtype in [QuestTypes.OTHER, QuestTypes.BLANK, QuestTypes.NORMAL]:
        analyser = SingleNormalAnalyser(question)
    else:
        TypeError(f"Quest type is invalid, {question.qtype}")
    return analyser


def do_analysis(question: Question):
    analyser = get_analyser(question)
    if not analyser:
        raise TypeError(f"Quest type is invalid, {question.qtype}")
    analyser.run()


if __name__ == '__main__':
    import json

    jd = json.load(open("../examples/LLM_panda300/normal/0000.json"))
    q = Question.from_json(jd)
    print(q.quest_stem.text)
    do_analysis(q)
    print(q.generate_ref.to_json())
