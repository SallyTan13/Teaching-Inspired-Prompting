from tip_prompt.quest import Question
from tip_prompt.spans.answer import SIM_QUEST_SPAN
from tip_prompt.utils.background_util import get_bgkl_chi, get_bgkl_eng

import abc


class Analyser(abc.ABC):
    def __init__(self, question: Question, temperature: float = 0.):
        self.question = question
        self.temperature = temperature
        self.message_debug = []

    @abc.abstractmethod
    def run(self):
        raise NotImplemented

    def create_sim_question_text_span(self, quest_num):
        """create the similar question span"""
        sim_quest_text_span = []
        num = 0
        print("quest_num: ", quest_num)
        for sim_quest in self.question.similar_quests:
            if num >= int(quest_num):
                break
            sim_quest: Question
            analyses = "".join([analysis for analysis in sim_quest.quest_ref.analyses])
            answers = "".join([text for text in sim_quest.quest_ref.texts])
            if sim_quest.quest_stem.options != None:
                options = [o.bullet + '.' + o.text for o in sim_quest.quest_stem.options]
                options = " ".join(options)
                sim_quest_text_span.append(SIM_QUEST_SPAN.fill_slots({"sim_stem": sim_quest.quest_stem.text + options,
                                                                      "sim_analysis": analyses,
                                                                      "sim_ans": answers}))
            else:
                sim_quest_text_span.append(SIM_QUEST_SPAN.fill_slots({"sim_stem": sim_quest.quest_stem.text,
                                                                      "sim_analysis": analyses,
                                                                      "sim_ans": answers}))
            num += 1
        if int(quest_num) > len(self.question.similar_quests):
            diff_num = int(quest_num) - len(self.question.similar_quests)
            for _ in range(diff_num):
                sim_quest = self.question.similar_quests[-1]
                sim_quest: Question
                analyses = "".join([analysis for analysis in sim_quest.quest_ref.analyses])
                answers = "".join([text for text in sim_quest.quest_ref.texts])
                if sim_quest.quest_stem.options != None:
                    options = [o.bullet + '.' + o.text for o in sim_quest.quest_stem.options]
                    options = " ".join(options)
                    sim_quest_text_span.append(SIM_QUEST_SPAN.fill_slots({"sim_stem": sim_quest.quest_stem.text + options,
                                                                        "sim_analysis": analyses,
                                                                        "sim_ans": answers}))
                else:
                    sim_quest_text_span.append(SIM_QUEST_SPAN.fill_slots({"sim_stem": sim_quest.quest_stem.text,
                                                                        "sim_analysis": analyses,
                                                                        "sim_ans": answers}))
            

        return sim_quest_text_span
    
    def create_background_text_span(self, language):
        """create the background span"""
        if self.question.quest_stem.options != None:
            options = [o.bullet + '.' + o.text for o in self.question.quest_stem.options]
            options = " ".join(options)
            quest_stem = self.question.quest_stem.text + options
        else:
            quest_stem = self.question.quest_stem.text
        if language == "Chinese":
            bgkl = get_bgkl_chi(quest_stem)
        else:
            bgkl = get_bgkl_eng(quest_stem)
        return bgkl
        


