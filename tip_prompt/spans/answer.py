from ..types.span import Span, TextSpan

__all__ = ['SOLVE_MATH_TEACHER', 'REFERENCE_SIM', 'ANSWER_SIMPLE', 'REPLY_CHINESE', 'IGNORE_TYPO', 'REPLY_JSON',
           'SIM_QUEST_SPAN', 'UNSOLVED_QUESTION_SPAN', "LIST_COUNTEREXAMPLE_SPAN", 'BGKL_SPAN', 'CHOICE_QUESTION_SPAN']

SOLVE_MATH_TEACHER = TextSpan(
    'You are an super smart elementary school math teacher. \n'
    'You need read the math problem carefully and solve it '
    'in a step by step way to be sure you have the right answer.\n'
    'You often make mistakes in calculations, so please be careful when calculating. \n',
    explain='老师人设')

ANSWER_SIMPLE = TextSpan("Please make sure your replies as simple and easy to understand as possible.\n",
                         explain="回复尽量简单")

REPLY_CHINESE = TextSpan(
    'IMPORTANT: All content except for Python functions and title must be in Chinese.\n',
    explain='回答中文')

REPLY_ENGLISH = TextSpan(
    'IMPORTANT: All content except for Python functions and title must be in English.\n',
    explain='回答英文')

IGNORE_TYPO = TextSpan(
    "Please do not be influenced by the typos in the question and reason based on the semantics of the question.\n",
    explain="忽略OCR错误")

RECHECK_TEACHER = TextSpan("你是一个小学数学老师，下边是一道小学数学题，以及 ChatGPT 对这道题的解释\n"
                           "ChatGPT 是一个 AI 模型，他会犯低级错误，他的解释可能不合理，甚至是完全错误的。\n"
                           "你需要认真审查 ChatGPT 的解释，判断其 ChatGPT 的解答是否正确、合理。\n"
                           "如果解释是正确的合理的，请直接回答'正确'。\n"
                           "如果解释有错误，或者解释不合理，请直接给出正确的解释",
                           explain="套娃老师"),

REPLY_JSON = TextSpan("You should return in JSON format, and ensure that "
                      "the JSON format can be parsed directly by json.dumps in Python.\n"
                      "Field names and their meanings are as follows:\n",
                      explain="返回json")

REPLY_PYTHON = TextSpan("You should append the entire analyse process in a valid Python function to the end, "
                        "and the function should be named as 'solution'."
                        "Additionally, the final result should be printed at the end of the function.\n"
                        "Below is an example of the returned Python format:\n"
                        "```python\n"
                        "def solution(x=1, y=30):\n"
                        "    answer = x+y\n"
                        "    print(answer)\n"
                        "```\n",
                        explain="返回python")

REFERENCE_SIM = TextSpan(
    'If there is a reference question and the reference question is very similar to the question you need to answer, '
    'you should think based on the analysis process of the reference question, '
    'but you cannot be affected by its question stem.'
    'You still need to return the complete analysis process of the question you need to answer.\n',
    explain='参考相似题进行推理')

SIM_QUEST_SPAN = Span(
    "Reference question:\n"
    "{sim_stem}\n"
    "Reference analysis:\n"
    "{sim_analysis}\n"
    "Reference answer:\n"
    "{sim_ans}\n",
    explain="相似题"
)

BACKGROUND_KL_SPAN = Span(
    "Background: \n{background}",
    explain="背景知识"
)

LIST_COUNTEREXAMPLE_SPAN = Span("Here is a statement:\n"
                                "{statement}\n"
                                "If there are counterexamples to the above statement, "
                                "provide three counterexamples in chinese.\n"
                                "Note that the examples should be expressed with equations as much as possible, "
                                "based on facts, and should not be fabricated.\n",
                                explain='举反例')

UNSOLVED_QUESTION_SPAN = Span("Question:\n"
                              "{question}\n"
                              "Analysis:\n",
                              explain="待答疑题目")

CHOICE_QUESTION_SPAN = Span("```\n{stem}\n{options}\n```\n", explain='待答疑的选择题题干')

BGKL_SPAN = Span("You may use the following background knowledge when analyzing the problem:\n",
                 explain="背景知识")
