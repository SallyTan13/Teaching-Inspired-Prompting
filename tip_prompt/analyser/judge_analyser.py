import openai
from tip_prompt.analyser.base_analyser import Analyser
from tip_prompt.types import *
from tip_prompt.spans.answer import *
from tip_prompt.spans.base import LINE_BREAK
from tip_prompt.quest import Question, QuestRef
from tip_prompt.utils.chat import chat_gpt3, chat_gpt4
from tip_prompt.spans.answer import BACKGROUND_KL_SPAN
import re
from typing import Optional, List
import collections

openai.api_key = "XXXX"
judge_claim = TextSpan("You should provide the answer (True / False)"
                        "to the True or False question delimited by triple backticks.", explain='判断题作答要求')

judge_reply_examples_chi = [
    TextSpan("Examples:\n", explain="title"),
    UNSOLVED_QUESTION_SPAN.fill_slots(slots={"question": "判断正误：比最大的三位数多100的数是1999。"}),
    TextSpan('thought: 首先我们要知道最大的三位数是多少，然后再计算最大的三位数加100，判断计算结果是否等于1999，如果不等于，则该说法错误，如果等于，则该说法正确。\n'
             'steps: \n'
             '1. 最大的三位数是999\n'
             '2. 比最大的三位数多100，即给999+100，结果是1099\n'
             '3. 计算结果是1099，不等于1999，所以该题目的答案是错误\n'
             'answer: 错误\n',
            explain='中文示例题1'),
    UNSOLVED_QUESTION_SPAN.fill_slots(slots={"question": "判断正误：余数都不大于商。"}),
    TextSpan('thought: 可以通过余数和除数以及商的关系来判断，也可以通过举例子来判断这个说法是否正确\n'
             'steps: \n'
             '1. 一般来说余数不能大于除数，但是余数和商没有绝对的大小关系\n'
             '2. 比如104除以33等于3余5，其中余数5就比商3大\n'
             '3. 再比如3除以4等于0余3，其中余数3比商0要大\n'
             '4. 因此根据反例和概念关系，我们可以判断该说法错误\n'
             '5. 所以，最终答案是错误\n'
             'answer: 错误\n',
            explain='中文示例题2')
]

judge_template_chi_prompts = [
    UserPrompt([UNSOLVED_QUESTION_SPAN], slots={"question": "判断正误：0.019中的‘9‘在百分位上。"}),
    AssistantPrompt([TextSpan('thought: 小数点右边第一位是十分位，第二位是百分位，第三位是千分位。\n'
                              'steps: \n'
                              '1. 确定小数点右边第二位为百分位。\n'
                              '2. 查看0.019的小数点右边第三位，发现是9。\n'
                              '3. 得出结论，0.019中的‘9’在千分位上。\n'
                              '4. 所以，题干中的说法错误。\n'
                              'answer: 错误\n',
                              explain='中文示例题3')])
]

judge_reply_examples_eng = [
    TextSpan("Examples:\n", explain="title"),
    UNSOLVED_QUESTION_SPAN.fill_slots(slots={"question": "True or False: The number that is 100 more than the largest three-digit number is 1999."}),
    TextSpan('thought: Firstly, we need to know what the largest three-digit number is, and then calculate the largest three-digit number plus 100 to determine whether the result is equal to 1999. If the result is not equal to 1999, then the statement is false. If it is equal to 1999, then the statement is true.\n'
             'steps: \n'
             '1. The largest three-digit number is 999.\n'
             '2. Adding 100 to 999 results in 1099.\n'
             '3. The result of the calculation is 1099, which is not equal to 1999. Therefore, the answer to this question is false.\n'
             'answer: False\n',
            explain='英文示例题1'),
    UNSOLVED_QUESTION_SPAN.fill_slots(slots={"question": "True or False: The remainder is never greater than the quotient."}),
    TextSpan('thought: This statement can be judged by the relationship between the remainder, divisor, and quotient, or by giving examples to see if the statement is true or false.\n'
             'steps: \n'
             '1. Generally, the remainder cannot be greater than the divisor, but there is no absolute relationship between the remainder and the quotient.\n'
             '2. For example, 104 divided by 33 equals 3 with a remainder of 5, where the remainder 5 is greater than the quotient 3.\n'
             '3. Another example is 3 divided by 4, which equals 0 with a remainder of 3, where the remainder 3 is greater than the quotient 0.\n'
             '4. Therefore, based on the counterexamples and concept relationships, we can conclude that this statement is false.\n'
             '5. Therefore, the final answer is false.\n'
             'answer: False\n',
            explain='英文示例题2')
]

judge_template_chi_prompts = [
    UserPrompt([UNSOLVED_QUESTION_SPAN], slots={"question": "判断正误：0.019中的‘9‘在百分位上。"}),
    AssistantPrompt([TextSpan('thought: 小数点右边第一位是十分位，第二位是百分位，第三位是千分位。\n'
                              'steps: \n'
                              '1. 确定小数点右边第二位为百分位。\n'
                              '2. 查看0.019的小数点右边第三位，发现是9。\n'
                              '3. 得出结论，0.019中的‘9’在千分位上。\n'
                              '4. 所以，题干中的说法错误。\n'
                              'answer: 错误\n',
                              explain='中文示例题3')])
]

judge_template_eng_prompts = [
    UserPrompt([UNSOLVED_QUESTION_SPAN], slots={"question": "True or False: The '9' in 0.019 is in the hundredths place."}),
    AssistantPrompt([TextSpan('thought: The first decimal place to the right of the decimal point is the tenths place, the second decimal place is the hundredths place, and the third decimal place is the thousandths place.\n'
                              'steps: \n'
                              '1. To determine the hundredths place, we need to look at the second decimal place to the right of the decimal point.\n'
                              '2. Looking at the third decimal place to the right of the decimal point in 0.019, we find that it is 9.\n'
                              '3. We can conclude that the "9" in 0.019 is in the thousandths place.\n'
                              '4. Therefore, the statement in the question is false.\n'
                              'answer: False\n',
                              explain='英文示例题3')])
]

judge_reply_format = TextSpan(
    "When you are certain that the answer is correct, you need to return the following content:\n"
    "thought: <It's necessary. Return your thinking process for solving this problem.>\n"
    "steps: <It's necessary. The steps for solving the question, with as much detail as possible.>\n"
    "answer: <It's necessary. If you believe that the statement in the question is correct, return 'True'. "
    "If you believe that the statement in the question is false, return 'False'.>\n"
    "Important: Your return format must be consistent with the 'Examples' \n"
    "Important: The content you return must include the keyword: thought, steps and answer."
    "and the content of every keyword cannot be empty. Besides, each keyword should be in English.\n",
    explain="返回格式"
)

chinese_to_english_span = Span("You need to translate the text declared by three single quotes below into English. \n"
                               "if the content is pure numbers or pure English characters, "
                               "please do not make any modifications and directly return the original content.\n"
                               "```"
                               "{text}\n"
                               "```", explain="翻译为英语")

english_to_chinese_span = Span("You only need to translate the content declared by three quotes into Chinese, "
                               "if the content is pure numbers or pure chinese characters, "
                               "please do not make any modifications and directly return the original content.\n"
                               "The following sentence needs to be translated into Chinese:"
                               "```"
                               "{text}\n"
                               "```", explain="翻译为中文")

def check_is_same_answer(ans_a: str, ans_b: str) -> bool:
    """Judge whether the generated answer is consistent with the question's answer."""
    if ans_a.lower() == ans_b.lower():
        return True
    else:
        return False


def normal_ans(ans):
    ans = ans.replace('×', 'False')
    ans = ans.replace('0', 'False')
    ans = ans.replace('1', 'True')
    ans = ans.replace('√', 'True')
    ans = ans.replace('正确', 'True')
    ans = ans.replace('错误', 'False')
    ans = ans.replace('A', 'True')
    ans = ans.replace('B', 'False')
    ans = ans.replace('true', 'True')
    ans = ans.replace('false', 'False')
    ans = ans.replace('对', 'True')
    ans = ans.replace('错', 'False')
    ans = ans.replace('真', 'True')
    ans = ans.replace('假', 'False')
    if ans == "T" or ans == "正":
        ans = "True"
    if ans == "F" or ans == "误":
        ans = "False"

    return ans


class JudgeAnalyser(Analyser):
    def __init__(self, question: Question, temperature: float = 0.5, language: str = "Chinese"):
        super().__init__(question, temperature)
        self.system = self.create_system_prompt()
        self.temperature = 0.5
        self.language = language

        if self.language == "Chinese":
            self.chi_system_messages = self.create_chi_messages()
        else:
            self.eng_system_messages = self.create_eng_messages()

    def create_system_prompt(self):
        """create system prompt"""
        pre_declaration_text_span = [SOLVE_MATH_TEACHER,
                                     judge_claim,
                                     LINE_BREAK]
        return SystemPrompt(pre_declaration_text_span)
    
    def create_chi_messages(self):
        sim_quest_text_span = self.create_sim_question_text_span()
        sim_question_text_span = [REFERENCE_SIM, LINE_BREAK] + sim_quest_text_span
        bgkl = self.create_background_text_span(self.language)
        reply_format_text_span = [judge_reply_format] + judge_reply_examples_chi
        if bgkl == []:
            message = [
                self.system,
                SystemPrompt(sim_question_text_span + reply_format_text_span),
                *judge_template_chi_prompts
            ]
        else:
            background_text_span = [BGKL_SPAN] + [BACKGROUND_KL_SPAN.fill_slots({"background": bgkl})]
            message = [
                self.system,
                SystemPrompt(sim_question_text_span + background_text_span + reply_format_text_span),
                *judge_template_chi_prompts
            ]
        return message
    
    def create_eng_messages(self):
        sim_quest_text_span = self.create_sim_question_text_span()
        sim_question_text_span = [REFERENCE_SIM, LINE_BREAK] + sim_quest_text_span
        bgkl = self.create_background_text_span(self.language)
        reply_format_text_span = [judge_reply_format] + judge_reply_examples_eng
        if bgkl == []:
            message = [
                self.system,
                SystemPrompt(sim_question_text_span + reply_format_text_span),
                *judge_template_eng_prompts
            ]
        else:
            background_text_span = [BGKL_SPAN] + [BACKGROUND_KL_SPAN.fill_slots({"background": bgkl})]
            message = [
                self.system,
                SystemPrompt(sim_question_text_span + background_text_span + reply_format_text_span),
                *judge_template_eng_prompts
            ]
        return message

    def convert_reply_to_questref(self, gpt_reply: str) -> Optional[QuestRef]:
        """parse the reply"""
        gpt_reply = gpt_reply.replace("思路：", "thought:")
        gpt_reply = gpt_reply.replace("步骤：", "steps:")
        gpt_reply = gpt_reply.replace("答案：", "answer:")

        # thought
        thought_m = re.search(r"(?:thought:)?((?:.|\n)+?)steps", gpt_reply)
        if thought_m:
            thought = thought_m.groups()[0]
        else:
            return
        
        # steps
        step_m = re.search(r"steps:((?:.|\n)+?)answer", gpt_reply)
        if step_m:
            steps = step_m.groups()[0]
            steps = steps.split('\n')
            steps = [s for s in steps if s]
        else:
            steps = []
        
        # answer
        analysis_ans_m = re.search(r"answer:\s+(\w)", gpt_reply).group(1)
        if analysis_ans_m:
            analysis_ans = normal_ans(analysis_ans_m[0].strip())
        else:
            return

        final_ans = analysis_ans
        analysis = f"解题思路：{thought}\n"
        if steps:
            analysis += f"详细步骤：\n"
            analysis += "\n".join(steps)
        
        return QuestRef(texts=[final_ans], analyses=[analysis])
    
    def get_ensemble_results(self) -> List[QuestRef]:
        results = []
        for _ in range(4):
            rsp_text = chat_gpt3(self.message,
                                 {'question': "True or False." + self.question.quest_stem.text},
                                 temperature=self.temperature)
            generate_ref = self.convert_reply_to_questref(rsp_text)
            if not generate_ref:
                continue
            results.append(generate_ref)
        return results
    
    def get_multi_analysis_info(self, message: List, chat_fun, iteration: int = 3, max_loop: int = 10):
        """Call chat_fun multiple times based on the message to get the answer."""
        analyses_info = []
        llm_history = []
        _message = message

        while iteration > 0 and max_loop > 0:
            max_loop -= 1

            rsp_text = chat_fun(_message,
                                temperature=self.temperature,
                                llm_history=llm_history)

            gen_analysis = self.convert_reply_to_questref(rsp_text)
            if not gen_analysis:
                continue

            analyses_info.append(gen_analysis)
            iteration -= 1

        
        self.message_debug.append(llm_history[0])
        return analyses_info
    
    def get_ensemble_questref(self, analyses_info: List) -> Optional[QuestRef]:
        """Ensemble"""
        if not analyses_info:
            return
        
        answers = [result.texts[0] for result in analyses_info]
        print("answers: ", answers)
        max_confident_ans = collections.Counter(answers).most_common(1)[0]

        print("max_confident_ans: ", max_confident_ans)
        if max_confident_ans[1] < len(analyses_info) // 2:
            analyses_info += self.do_analysis_by_chi(chat_gpt3)
            answers = [result.texts[0] for result in analyses_info]
            max_confident_ans = collections.Counter(answers).most_common(1)[0]
        
        answer = max_confident_ans[0]
        idx = answers.index(answer)

        return analyses_info[idx]
    
    def do_analysis_by_chi(self, chat_fun) -> List[QuestRef]:
        messages = self.chi_system_messages + [
            UserPrompt([UNSOLVED_QUESTION_SPAN.fill_slots({'question': "判断正误：" + self.question.quest_stem.text})])]
        return self.get_multi_analysis_info(messages, chat_fun, iteration=3, max_loop=4)
    
    def do_analysis_by_eng(self, chat_fun, iteration) -> List[QuestRef]:
        messages = self.eng_system_messages + [
            UserPrompt([UNSOLVED_QUESTION_SPAN.fill_slots({'question': "True or False." + self.question.quest_stem.text})])]
        return self.get_multi_analysis_info(messages, chat_fun, iteration=iteration, max_loop=iteration+1)
    
    def do_analysis_by_trans_to_eng(self, chat_fun) -> Optional[List[QuestRef]]:
        """translate"""
        eng_stem = chat_gpt3([UserPrompt([chinese_to_english_span])],
                             slots={'text': "判断正误：" + self.question.quest_stem.text})
        
        # similar questions
        sim_quest_text_span = []
        for sim_quest in self.question.similar_quests:
            sim_quest: Question
            analyses = "".join([analysis for analysis in sim_quest.quest_ref.analyses])
            answers = "".join([text for text in sim_quest.quest_ref.texts])
            stem = sim_quest.quest_stem.text
            eng_similar_stem = chat_gpt3([UserPrompt([chinese_to_english_span])],
                             slots={'text': stem})
            eng_similar_answers = chat_gpt3([UserPrompt([chinese_to_english_span])],
                             slots={'text': answers})
            eng_similar_analyses = chat_gpt3([UserPrompt([chinese_to_english_span])],
                             slots={'text': analyses})

            sim_quest_text_span.append(SIM_QUEST_SPAN.fill_slots({"sim_stem": eng_similar_stem,
                                                                  "sim_analysis": eng_similar_analyses,
                                                                  "sim_ans": eng_similar_answers}))
        sim_question_text_span = [REFERENCE_SIM, LINE_BREAK] + sim_quest_text_span
        print("eng_stem: ", eng_stem)
        bgkl = self.create_background_text_span("Chinese")
        example_reply_text_span = [judge_reply_format] + judge_reply_examples_eng
        if bgkl == []:
            message = [self.system,
                    SystemPrompt(example_reply_text_span + sim_question_text_span),
                    UserPrompt([UNSOLVED_QUESTION_SPAN.fill_slots({'question': eng_stem})])]
        else:
            eng_bgkl = chat_gpt3([UserPrompt([chinese_to_english_span])],
                             slots={'text': bgkl})
            print("eng_bgkl: ", eng_bgkl)
            background_text_span = [BGKL_SPAN] + [BACKGROUND_KL_SPAN.fill_slots({"background": eng_bgkl})]
            message = [self.system,
                    SystemPrompt(example_reply_text_span + sim_question_text_span + background_text_span),
                    UserPrompt([UNSOLVED_QUESTION_SPAN.fill_slots({'question': eng_stem})])]
        analyses_infos = self.get_multi_analysis_info(message, chat_fun, iteration=2, max_loop=3)
        if not analyses_infos:
            return
        # convert the analysis into Chinese
        if self.language == "Chinese":
            # English to Chinese
            for analysis_info in analyses_infos:
                analysis_info.analyses[0] = chat_gpt3([UserPrompt([english_to_chinese_span])],
                                                slots={'text': analysis_info.analyses[0]})
        return analyses_infos
    
    def run(self):
        if self.language == "Chinese":
            analyses_info = self.do_analysis_by_chi(chat_gpt4)
        else:
            analyses_info = self.do_analysis_by_eng(chat_gpt4, 3)

        answers = [result.texts[0] for result in analyses_info]
        ans_same = answers.count(answers[0]) == len(answers)
        if ans_same:
            self.question.generate_ref = self.get_ensemble_questref(analyses_info)
            return 
        
        if self.language == "Chinese":
            analyses_info += self.do_analysis_by_trans_to_eng(chat_gpt4)
        else:
            analyses_info += self.do_analysis_by_eng(chat_gpt4, 2)
        self.question.generate_ref = self.get_ensemble_questref(analyses_info)



if __name__ == '__main__':
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument('json_path')
    args = parser.parse_args()

    jd = json.load(open(args.json_path))
    q = Question.from_json(jd)
    print(q.quest_stem.text)
    print(q.quest_ref.to_json()['analyses'])
    analyser = JudgeAnalyser(q)
    analyser.run()
    print(q.generate_ref.to_json()['texts'])
    print(q.generate_ref.to_json()['analyses'])
