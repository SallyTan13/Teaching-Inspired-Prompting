import openai
from tip_prompt.analyser.base_analyser import Analyser
from tip_prompt.types import *
from tip_prompt.spans.answer import *
from tip_prompt.spans.base import LINE_BREAK
from tip_prompt.quest import Question, QuestRef
from tip_prompt.utils.chat import chat_gpt3, chat_gpt4
from tip_prompt.utils.calcu_python_util import do_python, extract_python_code
from tip_prompt.spans.answer import BACKGROUND_KL_SPAN
import Levenshtein
import re
from typing import Optional, List

openai.api_key = "XXXX"

NUM_P = re.compile(r"\(?(\d+\.?\d*)\)?")

normal_chi_examples = [
    TextSpan("Examples:\n", explain="title"),
    UNSOLVED_QUESTION_SPAN.fill_slots({"question": "小明今年5岁，爸爸今年25岁。爸爸30岁时，小明多少岁？"}),
    TextSpan("thought:\n"
             "当爸爸30岁时，表示此时过去了30-25=5年，此时小明应该是5+5=10岁。\n"
             "steps:\n"
             "1. 我们需要找出爸爸从现在（25岁）到30岁还需要多少年。这个可以通过用30减去25来得到，即：30-25=5。所以，爸爸还需要5年才能到30岁。\n"
             "2. 我们知道小明现在是5岁，那么在接下来的5年里，他的年龄会增加。因为每过1年，他的年龄就会增加1岁，所以在5年里，他的年龄会增加5岁。\n"
             "3. 我们把小明现在的年龄（5岁）加上接下来5年的增加（5岁），就可以得到爸爸30岁时，小明的年龄。即：5+5=10。\n"
             "answer:\n"
             "10岁\n"
             "code:\n"
             "```python\n"
             "def solution(xiaoming=5, dad=25, dad_future=30):\n"
             "    past_year = dad_future - data\n"
             "    xiaoming_future = xiaoming + past_year\n"
             "    print(xiaoming_future)\n"
             "```\n", explain="示例题1")
]

normal_eng_examples = [
    TextSpan("Examples:\n", explain="title"),
    UNSOLVED_QUESTION_SPAN.fill_slots({"question": "Little Ming is 5 years old this year, "
                                                   "and his father is 25 years old this year. "
                                                   "How old will Little Ming be when his father is 30 years old?"}),
    TextSpan("thought:\n"
             "When the father is 30 years old, 5 years have passed since he was 25. "
             "At this time, Little Ming should be 10 years old (5 + 5).\n"
             "steps:\n"
             "1. We need to figure out how many years it will take for the father to reach 30 years old "
             "from now (25 years old). This can be obtained by subtracting 25 from 30, that is, 30-25=5. "
             "Therefore, the father still needs 5 years to reach 30 years old.\n"
             "2. We know that Little Ming is now 5 years old, so his age will increase in the next 5 years. "
             "Since his age increases by 1 year every year, in 5 years his age will increase by 5 years.\n"
             "3. If we add Little Ming's current age of 5 to the increase of 5 years in the next 5 years, "
             "we can get Little Ming's age when his father is 30 years old. That is, 5+5=10.\n"
             "answer:\n"
             "10\n"
             "code:\n"
             "```python\n"
             "def solution(ming=5, dad=25, dad_future=30):\n"
             "    past_year = dad_future - data\n"
             "    ming_future = ming + past_year\n"
             "    print(ming)\n"
             "```\n", explain="Normal Example in eng.")
]

normal_template_chi_prompts = [
    UserPrompt([UNSOLVED_QUESTION_SPAN], slots={"question": "小明第二天看了30页，第一天比第二天多看了一页书，那么第一天他看了几页书？"}),
    AssistantPrompt([TextSpan("thought:\n"
                              "因为小明第二天看了30页，第一天比第二天多看了1页，所以小明第一天看了30+1=31页\n"
                              "steps:\n"
                              "1. 第一天小明看的书比第二天多1页。\n"
                              "2. 第二天小明看了30页。\n"
                              "3. 那么，第一天小明看的书页数就是第二天的书页数再加1页。\n"
                              "4. 于是，第一天小明看了30页+1页=31页。\n"
                              "answer:\n"
                              "31页\n"
                              "code:\n"
                              "```python\n"
                              "def solution(first_day_minus_second_day=1, second_day=30):\n"
                              "    first_day = second_day + first_day_minus_second_day\n"
                              "    print(first_day)\n"
                              "```\n", explain="示例题2")])
]

normal_template_eng_prompts = [
    UserPrompt([UNSOLVED_QUESTION_SPAN], slots={"question": "Xiaoming read 30 pages on the second day, "
                                                "and read one more page than the second day on the first day. "
                                                "How many pages did he read on the first day?"}),
    AssistantPrompt([TextSpan("thought:\n"
                              "Since Xiaoming read 30 pages on the second day and read one more page than the second day on the first day, "
                              "Xiaoming read 31 pages on the first day.\n"
                              "steps:\n"
                              "1. Xiaoming read one more page on the first day than on the second day.\n"
                              "2. Xiaoming read 30 pages on the second day.\n"
                              "3. Therefore, the number of pages Xiaoming read on the first day is one more than that of the second day.\n"
                              "4. Thus, Xiaoming read 30 pages + 1 page on the first day, which is equal to 31 pages.\n"
                              "answer:\n"
                              "31 pages\n"
                              "code:\n"
                              "```python\n"
                              "def solution(first_day_minus_second_day=1, second_day=30):\n"
                              "    first_day = second_day + first_day_minus_second_day\n"
                              "    print(first_day)\n"
                              "```\n", explain="英文示例题2")])
]

normal_reply_format = TextSpan(
    "When you are certain that the answer is correct, you need to return the following content:\n"
    "thought: [Return your thinking process for solving this problem.]\n"
    "steps: [Return the detailed solution steps.]\n"
    "answer: [The answer to the question. If there are multiple questions in the problem,"
    " the answer format should be: (1) Answer to the first question. (2) Answer to the second question....]\n"
    "code: [Valid Python code corresponding to steps, and this function needs to be named as 'solution' and "
    "print the final result at the end.]\n"
    "Important: Your return format must be consistent with the 'Examples' \n"
    "Important: The content you return must include fore keywords: thought, steps, answer, and code, "
    "and the content of every keyword cannot be empty. Besides, every keyword should in English.\n"
    "Important: Even if the question is very simple, you must still return the Python code.\n"
    "Please make sure that the code you return can be directly executed by Python 3.\n",
    explain="应用题返回格式"
)

reform_analysis_task = TextSpan("Your task is to answer the math problem below and "
                                "return your complete thought process and detailed solution steps.\n"
                                "Please note that I will provide you with the corresponding correct answer, "
                                "and your reasoning result must be consistent with the correct answer.",
                                explain="任务说明")

answer_again_text_span = TextSpan("Your previous answer seems to have some problems, "
                                  "and I don't quite understand it. "
                                  "Please answer it again and keep the format consistent with the previous one.",
                                  explain="再次回答")

chinese_to_english_span = Span("You need to translate the text declared by three single quotes below into English. \n"
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


class Normal_Analysis_Info:
    def __init__(self, thought: str, steps: List[str], code_ans: str, ans: str):
        self.thought = thought.strip()
        self.steps = steps
        self.ans = ans.strip()
        self.code_ans = code_ans.strip()
        self.is_same = False

    def get_analysis(self):
        analysis = f"解题思路：{self.thought}\n"
        if self.steps:
            analysis += f"详细步骤：\n"
            analysis += "\n".join(self.steps)
        return analysis

    def to_json(self):
        jd = {'thought': self.thought,
              'steps': self.steps,
              'ans': self.ans,
              'code_ans': self.code_ans}
        return jd


def calcu_similar_score(str_a, str_b):
    max_len = max(len(str_a), len(str_b), 0)
    if max_len == 0:
        return 0
    return (max_len - Levenshtein.distance(str_a, str_b)) / max_len


def convert_reply_to_normal_info(gpt_reply: str) -> Optional[Normal_Analysis_Info]:
    """parse the reply"""
    gpt_reply = gpt_reply.replace("思路：", "thought:")
    gpt_reply = gpt_reply.replace("步骤：", "steps:")
    gpt_reply = gpt_reply.replace("答案：", "answer:")
    gpt_reply = gpt_reply.replace("代码：", "code:")

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
    analysis_ans_m = re.search(r"answer:((?:.|\n)+?)code", gpt_reply)
    if analysis_ans_m:
        analysis_ans = analysis_ans_m.groups()[0]
    else:
        return

    # python answer
    code_strs = extract_python_code(gpt_reply)
    if not code_strs:
        code_ans = analysis_ans
    else:
        code_answers = []
        for code_str in code_strs:
            code_answers.append(do_python(code_str))
        code_ans = "\n".join(code_answers)

    return Normal_Analysis_Info(thought=thought, steps=steps, ans=analysis_ans, code_ans=code_ans)


def extract_num(text: str):
    all_nums = NUM_P.findall(text)
    normalized_num = []
    for num in all_nums:
        normalized_num.append(str(round(float(num), 3)))
    return ",".join(normalized_num)


def check_is_same_answer(ans_a: str, ans_b: str) -> bool:
    """check whether step-by-step answer is consistent with the python answer"""
    sim_score = calcu_similar_score(ans_a, ans_b)
    if sim_score > 0.5:
        return True

    ans_a_nums = NUM_P.findall(ans_a)
    ans_b_nums = NUM_P.findall(ans_b)
    if len(ans_a_nums) != len(ans_b_nums):
        return False
    for ans_a_num, ans_b_num in zip(ans_a_nums, ans_b_nums):
        ans_a_num = round(float(ans_a_num), 3)
        ans_b_num = round(float(ans_b_num), 3)
        if abs(ans_a_num - ans_b_num) > 1e-4:
            return False
    return True


class SingleNormalAnalyser(Analyser):

    def __init__(self, question: Question, temperature: float = 0.5, language: str = "Chinese"):
        super().__init__(question, temperature)
        self.system = self.create_system_prompt()
        self.language = language

        if self.language == "Chinese":
            self.chi_system_messages = self.create_chi_system_messages()
        else:
            self.eng_system_messages = self.create_eng_system_messages()

    def create_system_prompt(self):
        """create system prompt"""
        pre_declaration_text_span = [SOLVE_MATH_TEACHER,
                                     IGNORE_TYPO,
                                     ANSWER_SIMPLE,
                                     ]
        return SystemPrompt(pre_declaration_text_span)

    def create_chi_system_messages(self):
        """create Chinese prompt"""
        sim_question_text_span = [REFERENCE_SIM] + self.create_sim_question_text_span()
        example_reply_text_span = [normal_reply_format] + normal_chi_examples
        bgkl = self.create_background_text_span(self.language)
        if bgkl == []:
            messages = [self.system,
                        SystemPrompt(sim_question_text_span +
                                     example_reply_text_span +
                                     [REPLY_CHINESE]),
                        *normal_template_chi_prompts,
                    ]
        else:
            background_text_span = [BGKL_SPAN] + [BACKGROUND_KL_SPAN.fill_slots({"background": bgkl})]
            messages = [self.system,
                        SystemPrompt(sim_question_text_span +
                                     example_reply_text_span +
                                     background_text_span +
                                     [REPLY_CHINESE]),
                        *normal_template_chi_prompts,
                    ]
        return messages
    
    def create_eng_system_messages(self):
        """create English prompt"""
        sim_question_text_span = [REFERENCE_SIM] + self.create_sim_question_text_span()
        example_reply_text_span = [normal_reply_format] + normal_eng_examples
        bgkl = self.create_background_text_span(self.language)
        print("bgkl: ", bgkl)
        if bgkl == []:
            messages = [self.system,
                        SystemPrompt(sim_question_text_span +
                                     example_reply_text_span),
                        *normal_template_eng_prompts,
                    ]
        else:
            background_text_span = [BGKL_SPAN] + [BACKGROUND_KL_SPAN.fill_slots({"background": bgkl})]
            messages = [self.system,
                        SystemPrompt(sim_question_text_span +
                                     example_reply_text_span +
                                     background_text_span),
                        *normal_template_eng_prompts,
                    ]
        return messages

    def reform_analysis_content(self, answer: str):
        """generate analysis"""
        new_message = [SystemPrompt([reform_analysis_task]),
                       UserPrompt(
                           [TextSpan(f"Question: {self.question.quest_stem.text}", explain="title"),
                            TextSpan(f"Correct Answer: {answer}", explain="title"),
                            TextSpan("Analysis: ", explain="title")])
                       ]
        messages = self.chi_system_messages + new_message

        for _ in range(2):
            rsp_text = chat_gpt3(messages)
            print("reform_analysis_content: ", rsp_text)
            gen_analysis = convert_reply_to_normal_info(rsp_text)
            if not gen_analysis:
                continue
            if check_is_same_answer(gen_analysis.ans, answer):
                return "下面是根据code生成的解析：\n" + gen_analysis.get_analysis()

    def get_ensemble_questref(self, analyses_info: List[Normal_Analysis_Info]) -> Optional[QuestRef]:
        """Ensemble"""
        if not analyses_info:
            return
        same_ans_cands = {}
        analyse_ans_cands = {}  # step-by-step answers
        code_ans_cands = {}  # code answers
        for idx, analysis_info in enumerate(analyses_info):
            
            a_ans = extract_num(str(analysis_info.ans))
            analyse_ans_cands.setdefault(a_ans, [])
            analyse_ans_cands[a_ans].append(idx)
            
            if analysis_info.code_ans:
                c_ans = extract_num(str(analysis_info.code_ans))
                code_ans_cands.setdefault(c_ans, [])
                code_ans_cands[c_ans].append(idx)

            if analysis_info.is_same:
                same_ans_cands.setdefault(a_ans, [])
                same_ans_cands[a_ans].append(idx)
        print("1st analyses_ans_cands: ", analyse_ans_cands)
        # most frequent answer
        top_analysis_cand = sorted(analyse_ans_cands.items(), key=lambda x: len(x[1]), reverse=True)[0]
        max_occur_ans_num = len(top_analysis_cand[1])
        use_code_ans = False  # 是否选择code结果
        if code_ans_cands:
            top_code_ans_cand = sorted(code_ans_cands.items(), key=lambda x: len(x[1]), reverse=True)[0]
            if check_is_same_answer(top_code_ans_cand[0], top_analysis_cand[0]):
                max_occur_ans_num += len(top_analysis_cand[1])
            elif len(top_code_ans_cand[1]) > max_occur_ans_num:
                max_occur_ans_num = len(top_code_ans_cand[1])
                use_code_ans = True
        print("same_ans_cands: ", same_ans_cands.items())
        # Return the most frequent result among consistent answers
        if same_ans_cands:
            top_analysis_cand = sorted(same_ans_cands.items(), key=lambda x: len(x[1]), reverse=True)[0]
            if len(top_analysis_cand[1]) > max_occur_ans_num // 2:
                top_analysis_info = analyses_info[top_analysis_cand[1][-1]]  # 答案一样时优先选择中文生成的
                generate_ref = QuestRef(texts=[top_analysis_info.ans], analyses=[top_analysis_info.get_analysis()])
                return generate_ref

        # Return the most frequent result among inconsistent answers
        top_analysis_info = analyses_info[top_analysis_cand[1][0]]
        generate_ref = QuestRef(texts=[top_analysis_info.ans], analyses=[top_analysis_info.get_analysis()])

        # Use code answers as a supplement
        if use_code_ans:
            for a in analyse_ans_cands.items():
                if check_is_same_answer(a[0], top_code_ans_cand[0]):
                    final_rst = analyses_info[a[1][0]]
                    generate_ref = QuestRef(texts=[final_rst.ans], analyses=[final_rst.get_analysis()])
                    return generate_ref

            new_analysis = self.reform_analysis_content(top_code_ans_cand[0])
            generate_ref = QuestRef(texts=[top_code_ans_cand[0]], analyses=[new_analysis])
        print("top_analysis_cand: ", top_analysis_cand)
        return generate_ref

    def get_multi_analysis_info(self, message: List, chat_fun, iteration: int = 3, max_loop: int = 10):
        """Call chat_fun multiple times based on the message to get the answer"""
        analyses_info = []
        llm_history = []
        _message = message
        while iteration > 0 and max_loop > 0:
            max_loop -= 1
            rsp_text = chat_fun(_message,
                                temperature=self.temperature,
                                llm_history=llm_history)

            gen_analysis = convert_reply_to_normal_info(rsp_text)
            if not gen_analysis:
                continue
            # _message += [AssistantPrompt([TextSpan(rsp_text, explain="回复")])]

            analyses_info.append(gen_analysis)
            iteration -= 1

            # same answer
            if gen_analysis.code_ans and check_is_same_answer(gen_analysis.ans, gen_analysis.code_ans):
                gen_analysis.is_same = True

        self.message_debug.append(llm_history[0])
        return analyses_info

    def do_analysis_by_trans_to_eng(self, chat_fun) -> Optional[List[Normal_Analysis_Info]]:
        """Translate"""
        eng_stem = chat_gpt3([UserPrompt([chinese_to_english_span])],
                             slots={'text': self.question.quest_stem.get_stem()})
        print("eng_stem: ", eng_stem)
        example_reply_text_span = [normal_reply_format] + normal_eng_examples
        bgkl = self.create_background_text_span("Chinese")
        # similar questions
        sim_quest_text_span = []
        for sim_quest in self.question.similar_quests:
            sim_quest: Question
            analyses = "".join([analysis for analysis in sim_quest.quest_ref.analyses])
            answers = "".join([text for text in sim_quest.quest_ref.texts])
            stem = sim_quest.quest_stem.text
            options = [o.bullet + '.' + o.text for o in sim_quest.quest_stem.options]
            options = " ".join(options)
            eng_similar_stem = chat_gpt3([UserPrompt([chinese_to_english_span])],
                             slots={'text': stem + options})
            eng_similar_answers = chat_gpt3([UserPrompt([chinese_to_english_span])],
                             slots={'text': answers})
            eng_similar_analyses = chat_gpt3([UserPrompt([chinese_to_english_span])],
                             slots={'text': analyses})
            sim_quest_text_span.append(SIM_QUEST_SPAN.fill_slots({"sim_stem": eng_similar_stem,
                                                                  "sim_analysis": eng_similar_analyses,
                                                                  "sim_ans": eng_similar_answers}))
            sim_question_text_span = [REFERENCE_SIM, LINE_BREAK] + sim_quest_text_span
        if bgkl == []:
            message = [self.system,
                    SystemPrompt(example_reply_text_span + sim_question_text_span),
                    UserPrompt([UNSOLVED_QUESTION_SPAN.fill_slots({'question': eng_stem})])]
        else:
            eng_bgkl = chat_gpt3([UserPrompt([chinese_to_english_span])], slots={'text': bgkl})
            background_text_span = [BGKL_SPAN] + [BACKGROUND_KL_SPAN.fill_slots({"background": eng_bgkl})]
            message = [self.system,
                    SystemPrompt(example_reply_text_span + sim_question_text_span + background_text_span),
                    UserPrompt([UNSOLVED_QUESTION_SPAN.fill_slots({'question': eng_stem})])]
        analyses_infos = self.get_multi_analysis_info(message, chat_fun, iteration=2, max_loop=3)
        if not analyses_infos:
            return

        # English to Chinese
        for analysis_info in analyses_infos:
            analysis_info.thought = chat_gpt3([UserPrompt([english_to_chinese_span])],
                                              slots={'text': analysis_info.thought})
            analysis_info.ans = chat_gpt3([UserPrompt([english_to_chinese_span])],
                                          slots={'text': analysis_info.ans})
            if analysis_info.code_ans:
                analysis_info.code_ans = chat_gpt3([UserPrompt([english_to_chinese_span])],
                                                   slots={'text': analysis_info.code_ans})
            if analysis_info.steps:
                steps = "\n".join(analysis_info.steps)
                steps = chat_gpt3([UserPrompt([english_to_chinese_span])],
                                  slots={'text': steps})
                analysis_info.steps = steps.split('\n')
        return analyses_infos

    def do_analysis_by_chi(self, chat_fun):
        messages = self.chi_system_messages + [
            UserPrompt([UNSOLVED_QUESTION_SPAN.fill_slots({'question': self.question.quest_stem.text})])]
        return self.get_multi_analysis_info(messages, chat_fun, iteration=3, max_loop=4)
    
    def do_analysis_by_eng(self, chat_fun, iteration):
        messages = self.eng_system_messages + [
            UserPrompt([UNSOLVED_QUESTION_SPAN.fill_slots({'question': self.question.quest_stem.text})])]
        return self.get_multi_analysis_info(messages, chat_fun, iteration=iteration, max_loop=iteration+1)

    def run(self):
        if self.language == "Chinese":
            analyses_info = self.do_analysis_by_chi(chat_gpt3)
        else:
            analyses_info = self.do_analysis_by_eng(chat_gpt3, 3)

        all_same = True
        for a in analyses_info:
            if not a.is_same:
                all_same = False
        if all_same:
            self.question.generate_ref = self.get_ensemble_questref(analyses_info)
            return
        if self.language == "Chinese":
            analyses_info += self.do_analysis_by_trans_to_eng(chat_gpt3)
        else:
            analyses_info += self.do_analysis_by_eng(chat_gpt3, 2)

        # 中英文ensemble结果
        self.question.generate_ref = self.get_ensemble_questref(analyses_info)


if __name__ == '__main__':
    import json
    jd = json.load(open("../../examples/experiments/AddSub/eng/31.json", "r"))
    jd['quest_id'] = ""
    #ans = jd['similar_quests']['quest_ref']['texts']
    #analyses = jd['similar_quests']['quest_ref']['analyses']
    #jd['similar_quests']['quest_ref']['texts'] = [ans]
    #jd['similar_quests']['quest_ref']['analyses'] = [analyses]
    #similar_quests = jd['similar_quests']
    #jd['similar_quests'] = [similar_quests]
    q = Question.from_json(jd)
    print(q.quest_stem.text)
    print(q.quest_ref.to_json())
    print(q.quest_ref.to_json()['analyses'][0])
    try:
       analyser = SingleNormalAnalyser(q, language="English")
       analyser.temperature = 0.5
       analyser.run()
    except:
       flag = True
       while flag == True:
           import time
           time.sleep(5)
           try:
              analyser = SingleNormalAnalyser(q, language="English")
              analyser.temperature = 0.5
              analyser.run()
              flag = False
           except:
              flag = True
    # print(q.generate_ref)
    # print("temperature: ", analyser.temperature)
    print(q.generate_ref.to_json())
    # print(analyser.reform_analysis_content(answer='616'))
