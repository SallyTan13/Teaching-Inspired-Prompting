from ..types.span import Span, TextSpan

__all__ = ['ANSWER_QUESTION', 'IGNORE_DOUBTS', 'QUESTION_SPAN']

ANSWER_QUESTION = TextSpan("Your task is to clarify the student's doubts about "
                           "the above math problem enclosed in triple quotes, "
                           "and the reply should be as simple and detailed as possible. \n"
                           "If you find that the student's question is not related to the problem, "
                           "please refuse to answer.\n",
                           explain="回答提问任务定义")

IGNORE_DOUBTS = TextSpan("Please remember that the answer to this question is definitely correct. "
                         "If the student doubts the correctness of the answer, "
                         "please do not be influenced by the student.\n", explain="拒绝质疑")

QUESTION_SPAN = Span("```\nproblem: {stem}\nanalysis: {analysis}\nanswer: {answer}\n```\n", explain='询问题目')
