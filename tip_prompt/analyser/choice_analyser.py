import openai
from tip_prompt.analyser.base_analyser import Analyser
from tip_prompt.types import *
from tip_prompt.spans.answer import *
from tip_prompt.spans.base import LINE_BREAK
from tip_prompt.utils.chat import chat_gpt3, chat_gpt4, chat_gpt_in_json
from tip_prompt.quest import Question, QuestRef
from tip_prompt.spans.answer import BACKGROUND_KL_SPAN
from typing import Optional, List
import re
import collections

openai.api_key = "XXXX"

choice_claim = TextSpan("You should provide the correct options "
                        "to the choice question delimited by triple backticks.", explain='选择题作答要求')


choice_reply_examples_chi = [
    TextSpan("Examples:\n", explain="title"),
    CHOICE_QUESTION_SPAN.fill_slots(slots={"stem": "小宁平均走一步的长度是58厘米，他从家走到学校走了135步，小宁家到学校的距离约为是( )",
                            "options": "A.8000米 B.80米 C.70米"}),
    TextSpan('thought: 依据距离=步数×每步长度，列出算式58×135，依据整数乘法计算方法计算，得出结果为7830，再根据四舍五入法发现即可解答.\n'
             'steps: \n'
             '1. 依据距离=步数×每步长度，列式求出小宁家到学校的距离，算式为58×135\n'
             '2. 根据所列算式58×135=7830厘米，求出小宁家到学校的距离为7830厘米\n'
             '3. 因选项的单位为米，而我们之前所计算的结果的单位为厘米，所以应将厘米换算为米，7830厘米=78.3米\n'
             '4. 再根据四舍五入法，78.3米约等于80米，所以应该选择B选项\n'
             'answer: B\n',
            explain='中文示例题1'),
    CHOICE_QUESTION_SPAN.fill_slots(slots={"stem": "下列说法正确的是( )",
                            "options": "A.一条射线长50米 B.一年中有6个大月，6个小月 C.1/3:1/4和4:3能组成比例 D. 2020年全年365天"}),
    TextSpan('thought: 分别判断题目中ABCD四个选项的说法是否正确\n'
             'steps: \n'
             '1. A选项，由于射线只有一个端点，向一方无限延长，所以不能度量长度，所以A不对。\n'
             '2. B选项，一年有7个大月，5个小月，所以B选项的说法不对。\n'
             '3. C选项，因为组成比例的含义是两个比相等的式子，1/3:1/4=4:3=4/3，4:3=4/3，所以可以与4:3组成比例，C选项的说法正确。\n'
             '4. D选项，2020除以4可以被整除，所以2020年是闰年，全年有366天，D选项的说法不对。\n'
             '5. 所以，最终答案是C\n'
             'answer: C\n',
            explain='中文示例题2')
]

choice_template_chi_prompts = [
    UserPrompt([CHOICE_QUESTION_SPAN], slots={"stem": "()的得数大于100？",
                            "options": "A.50+45 B.90+20 C.90-80"}),
    AssistantPrompt([TextSpan('thought: 将每个算式相加的结果与100进行比较\n'
                              'steps: \n'
                              '1. A选项计算结果为50+45=95，95小于100，所以A不对。\n'
                              '2. B选项计算结果为90+20=110，因为110大于100，所以B选项正确，正确答案是B。\n'
                              '3. 以防出现计算错误，我们再计算一下C选项的答案，90-80=10，因为10小于100，所以C选项也不对。\n'
                              '4. 所以，最终答案是B。\n'
                              'answer: B\n',
                              explain='中文示例题3')])
]

choice_reply_examples_eng = [
    TextSpan("Examples:\n", explain="title"),
    CHOICE_QUESTION_SPAN.fill_slots(slots={"stem": "The approximate distance from Xiao Ning's home to school, "
                                           "given that he walks an average step length of 58 centimeters and has taken 135 steps, is about ()",
                            "options": "A.8000m B.80m C.70m"}),
    TextSpan('thought: Based on the formula distance = number of steps × length per step, write the equation 58 × 135, calculate it using integer multiplication method, and get the result of 7830. Then, according to the rounding rule, the answer can be solved.\n'
             'steps: \n'
             '1. Using the formula distance = number of steps × length per step, derive the equation 58 × 135\n'
             '2. According to the equation 58 × 135 = 7830 cm, determine the distance from Xiao Ning house to the school as 7830 cm\n'
             '3. Since the options are in meters and the result we calculated earlier is in centimeters, we should convert centimeters to meters. 7830 cm = 78.3 m\n'
             '4. Applying rounding rules, 78.3 m is approximately equal to 80 m, so option B should be selected\n'
             'answer: B\n',
            explain='英文示例题1'),
    CHOICE_QUESTION_SPAN.fill_slots(slots={"stem": "Which of the following statements is correct? ",
                            "options": "A. A ray is 50 meters long B. There are 6 big months (31 days) and 6 small months (30 days) in a year C. 1/3:1/4 and 4:3 can form a proportion D. The whole year in 2020 has 365 days."}),
    TextSpan('thought: 分别判断题目中ABCD四个选项的说法是否正确\n'
             'steps: \n'
             '1. Option A, since a ray has only one endpoint and extends infinitely in one direction, it cannot be measured in terms of length. Therefore, Option A is incorrect. \n'
             '2. Option B, there are 7 big months and 5 small months in a year, so the statement in Option B is incorrect.\n'
             '3. Option C, to form a proportion, the ratios on both sides should be equal. 1/3:1/4 = 4:3 = 4/3, and 4:3 is equal to 4/3. Therefore, it can form a proportion with 4:3. The statement in Option C is correct.\n'
             '4. Option D, 2020 is a leap year because it is divisible by 4, so the whole year has 366 days. The statement in Option D is incorrect.\n'
             '5. Therefore, the correct answer is Option C.\n'
             'answer: C\n',
            explain='英文示例题2')
]

choice_template_eng_prompts = [
    UserPrompt([CHOICE_QUESTION_SPAN], slots={"stem": "Which of the following expressions has a value greater than 100? ",
                            "options": "A.50+45 B.90+20 C.90-80"}),
    AssistantPrompt([TextSpan('thought: Compare the result of adding each equation to 100.\n'
                              'steps: \n'
                              '1. The result of option A is 50 + 45 = 95, which is less than 100, so Option A is incorrect.\n'
                              '2. The result of option B is 90 + 20 = 110, which is greater than 100, so Option B is correct. The correct answer is B.\n'
                              '3. To prevent calculation errors, let us calculate the answer for Option C again. 90 - 80 = 10, which is less than 100, so Option C is also incorrect.\n'
                              '4. Therefore, the final answer is B.\n'
                              'answer: B \n',
                              explain='英文示例题3')])
]

choice_reply_format = TextSpan(
    "When you are certain that the answer is correct, you need to return the following content:\n"
    "thought: <It's necessary. Return your thinking process for solving this problem.>\n"
    "steps: <It's necessary. The steps for solving the question, with as much detail as possible.>\n"
    "answer: <It's necessary. The specific option to the question, such as A/B/C/D>\n"
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
    if ans_a == ans_b:
        return True
    else:
        return False
    

class ChoiceAnalyser(Analyser):
    def __init__(self, question: Question, temperature: float = 0.5, language: str = "Chinese", quest_num: int=1):
        super().__init__(question, temperature)
        self.system = self.create_system_prompt()
        self.temperature = 0.5
        self.language = language
        self.quest_num = quest_num

        if self.language == "Chinese":
            self.chi_system_messages = self.create_chi_messages()
        else:
            self.eng_system_messages = self.create_eng_messages()

    def create_system_prompt(self):
        """create system prompt"""
        pre_declaration_text_span = [SOLVE_MATH_TEACHER,
                                     choice_claim,
                                     LINE_BREAK]
        return SystemPrompt(pre_declaration_text_span)
    
    def create_chi_messages(self):
        sim_quest_text_span = self.create_sim_question_text_span(self.quest_num)
        sim_question_text_span = [REFERENCE_SIM, LINE_BREAK] + sim_quest_text_span
        bgkl = self.create_background_text_span(self.language)
        reply_format_text_span = [choice_reply_format] + choice_reply_examples_chi
        if bgkl == []:
            message = [
                self.system,
                SystemPrompt(sim_question_text_span + reply_format_text_span),
                *choice_template_chi_prompts
            ]
        else:
            background_text_span = [BGKL_SPAN] + [BACKGROUND_KL_SPAN.fill_slots({"background": bgkl})]
            message = [
                self.system,
                SystemPrompt(sim_question_text_span + background_text_span + reply_format_text_span),
                *choice_template_chi_prompts
            ]
        return message
    
    def create_eng_messages(self):
        sim_quest_text_span = self.create_sim_question_text_span(self.quest_num)
        sim_question_text_span = [REFERENCE_SIM, LINE_BREAK] + sim_quest_text_span
        bgkl = self.create_background_text_span(self.language)
        reply_format_text_span = [choice_reply_format] + choice_reply_examples_eng
        if bgkl == []:
            message = [
                self.system,
                SystemPrompt(sim_question_text_span + reply_format_text_span),
                *choice_template_eng_prompts
            ]
        else:
            background_text_span = [BGKL_SPAN] + [BACKGROUND_KL_SPAN.fill_slots({"background": bgkl})]
            message = [
                self.system,
                SystemPrompt(sim_question_text_span + background_text_span + reply_format_text_span),
                *choice_template_eng_prompts
            ]
        return message

    def convert_reply_to_questref(self, gpt_reply: str) -> Optional[QuestRef]:
        """covert the reply"""
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
        
        # analysis answer
        analysis_ans_m = re.search(r"answer:\s+(\w)", gpt_reply).group(1)
        if analysis_ans_m:
            analysis_ans = analysis_ans_m[0].strip()
        else:
            return

        final_ans = analysis_ans
        analysis = f"解题思路：{thought}\n"
        if steps:
            analysis += f"详细步骤：\n"
            analysis += "\n".join(steps)
        
        return QuestRef(texts=[final_ans], analyses=[analysis])

    def get_ensemble_results(self) -> List[QuestRef]:
        options = [o.bullet + '.' + o.text for o in self.question.quest_stem.options]
        options = " ".join(options)

        results = []
        for _ in range(4):
            rsp_text = chat_gpt3(self.message,
                                 {'stem': self.question.quest_stem.text,
                                  'options': options},
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

        
        # Multiple requests retain only one prompt.
        self.message_debug.append(llm_history[0])
        return analyses_info
    
    def get_ensemble_questref(self, analyses_info: List) -> Optional[QuestRef]:
        """Ensemble the best answer"""
        if not analyses_info:
            return
        
        answers = [result.texts[0] for result in analyses_info]
        print("answers: ", answers)
        max_confident_ans = collections.Counter(answers).most_common(1)[0]
        # 判断ans_list中的生成的答案是否相同

        print("max_confident_ans: ", max_confident_ans)
        if max_confident_ans[1] < len(analyses_info) // 2:
            analyses_info += self.do_analysis_by_chi(chat_gpt3)
            answers = [result.texts[0] for result in analyses_info]
            max_confident_ans = collections.Counter(answers).most_common(1)[0]
        
        answer = max_confident_ans[0]
        idx = answers.index(answer)

        return analyses_info[idx]
    
    def do_analysis_by_chi(self, chat_fun) -> List[QuestRef]:
        options = [o.bullet + '.' + o.text for o in self.question.quest_stem.options]
        options = " ".join(options)
        messages = self.chi_system_messages + [
            UserPrompt([CHOICE_QUESTION_SPAN.fill_slots({'stem': self.question.quest_stem.text, 
                                                         'options': options})])]
        return self.get_multi_analysis_info(messages, chat_fun, iteration=1, max_loop=2)
    
    def do_analysis_by_eng(self, chat_fun, iteration) -> List[QuestRef]:
        options = [o.bullet + '.' + o.text for o in self.question.quest_stem.options]
        options = " ".join(options)
        messages = self.eng_system_messages + [
            UserPrompt([CHOICE_QUESTION_SPAN.fill_slots({'stem': self.question.quest_stem.text, 
                                                         'options': options})])]
        return self.get_multi_analysis_info(messages, chat_fun, iteration=iteration, max_loop=iteration+1)
    
    def do_analysis_by_trans_to_eng(self, chat_fun) -> Optional[List[QuestRef]]:
        """Translate the question"""
        options = [o.bullet + '.' + o.text for o in self.question.quest_stem.options]
        options = " ".join(options)
        eng_stem = chat_gpt3([UserPrompt([chinese_to_english_span])],
                             slots={'text': self.question.quest_stem.text})
        eng_options = chat_gpt3([UserPrompt([chinese_to_english_span])],
                             slots={'text': options})
        
        # similar questions
        sim_quest_text_span = []
        num = 0
        for sim_quest in self.question.similar_quests:
            if num >= int(self.quest_num):
                break
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
            num += 1
        sim_question_text_span = [REFERENCE_SIM, LINE_BREAK] + sim_quest_text_span
        print("eng_stem: ", eng_stem + " " + eng_options)
        bgkl = self.create_background_text_span("Chinese")
        example_reply_text_span = [choice_reply_format] + choice_reply_examples_eng
        if bgkl == []:
            message = [self.system,
                    SystemPrompt(example_reply_text_span + sim_question_text_span),
                    UserPrompt([CHOICE_QUESTION_SPAN.fill_slots({'stem': eng_stem, 
                                                                'options': eng_options})])]
        else:
            eng_bgkl = chat_gpt3([UserPrompt([chinese_to_english_span])],
                             slots={'text': bgkl})
            print("eng_bgkl: ", eng_bgkl)
            background_text_span = [BGKL_SPAN] + [BACKGROUND_KL_SPAN.fill_slots({"background": eng_bgkl})]
            message = [self.system,
                    SystemPrompt(example_reply_text_span + sim_question_text_span + background_text_span),
                    UserPrompt([CHOICE_QUESTION_SPAN.fill_slots({'stem': eng_stem, 
                                                                'options': eng_options})])]
        analyses_infos = self.get_multi_analysis_info(message, chat_fun, iteration=1, max_loop=2)
        if not analyses_infos:
            return
        # covert the analysis into Chinese
        if self.language == "Chinese":
            # English to Chinese
            for analysis_info in analyses_infos:
                analysis_info.analyses[0] = chat_gpt3([UserPrompt([english_to_chinese_span])],
                                                slots={'text': analysis_info.analyses[0]})
        return analyses_infos
    
    def run(self):
        if self.language == "Chinese":
            analyses_info = self.do_analysis_by_chi(chat_gpt3)
        else:
            analyses_info = self.do_analysis_by_eng(chat_gpt3, 1)
 
        
        if self.language == "Chinese":
            analyses_info += self.do_analysis_by_trans_to_eng(chat_gpt3)
        else:
            analyses_info += self.do_analysis_by_eng(chat_gpt3, 1)
        self.question.generate_ref = self.get_ensemble_questref(analyses_info)



if __name__ == '__main__':
    import json

    jd = json.load(open("../../examples/experiments/Choice/chi/6.json", "r"))
    jd['quest_id'] = ""
    q = Question.from_json(jd)
    print("q.quest_stem.text: ", q.quest_stem.text)
    print("q.quest_ref.to_json(): ", q.quest_ref.to_json())
    print("q.quest_ref.to_json()['analyses']: ", q.quest_ref.to_json()['analyses'])
    
    try:

        analyser = ChoiceAnalyser(q, language = "Chinese")
        analyser.temperature = 0.5
    
        analyser.run()
    except Exception as e:
        print(e)
        flag = True
        while flag:
            try:
                analyser = ChoiceAnalyser(q, language = "Chinese")
                analyser.temperature = 0.5
                analyser.run()
                flag = False
            except:
                flag = True

    print(q.generate_ref.to_json())
