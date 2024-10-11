from tip_prompt.types.prompt import Prompt, AssistantPrompt, UserPrompt
from tip_prompt.types.span import Slots, TextSpan
import openai
import json
from json.decoder import JSONDecodeError
from typing import Iterable, Optional, List
import re
from io import StringIO
from contextlib import redirect_stdout


def convert_msg_to_text(llm_history: List = None) -> str:
    """history message is converted to text"""
    if not llm_history:
        return ""
    _stdout = StringIO()
    llm_history_texts = []
    for messages in llm_history:
        for message in messages:
            message: dict
            llm_history_texts.append(message["content"])
    with redirect_stdout(_stdout):
        _stdout.write("\n".join(llm_history_texts))
    debug_text = _stdout.getvalue()
    return debug_text


def chat_gpt3(messages: Iterable, slots: Optional[Slots] = None, llm_history: List = None, temperature=0.0, **kwargs):
    llm_messages = []
    for message in messages:
        if isinstance(message, Prompt):
            if message.enable:
                llm_messages.append(message.get_message(slots))
        elif isinstance(message, dict):
            llm_messages.append(message)

    if llm_history is not None:
        llm_history.append(llm_messages)

    resp_json = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                             messages=llm_messages,
                                             temperature=temperature,
                                             **kwargs)
    return resp_json['choices'][0]['message']['content']


def chat_gpt4(messages: Iterable, slots: Optional[Slots] = None, llm_history: List = None, temperature=0.0, **kwargs):
    llm_messages = []
    for message in messages:
        if isinstance(message, Prompt):
            llm_messages.append(message.get_message(slots))
        elif isinstance(message, dict):
            llm_messages.append(message)

    if llm_history is not None:
        llm_history.append(llm_messages)

    resp_json = openai.ChatCompletion.create(model="gpt-4",
                                             messages=llm_messages,
                                             temperature=temperature,
                                             **kwargs)
    return resp_json['choices'][0]['message']['content']


def chat_gpt_in_json(gpt_fun, messages: Iterable, slots: Optional[Slots] = None, **kwargs):
    while True:
        result = gpt_fun(messages, slots, **kwargs)
        try:
            result = result.replace('```json', '')
            result = result.replace('```', '')
            m = re.search(r"(\{(?:.|\n)+?\})", result)
            if m:
                result = m.groups()[0]
                result = result.replace("思路", "thought")
                result = result.replace("答案", "answer")
            result = json.loads(result)
            return result
        except JSONDecodeError:
            print('Json格式错误，重新请求')
            messages.append(AssistantPrompt([TextSpan(result, explain="回复")]))
            messages.append(UserPrompt([TextSpan("There is an error in the JSON format of your answer. "
                                                 "Please check the JSON format and answer the question again.\n",
                                                 explain="回复")]))
        print("result: \n", result)


if __name__ == '__main__':
    import openai_monkey.hardware
    from tip_prompt.types import *

    print()
    messages = [
        SystemPrompt([
            TextSpan("You are now an elementary school math tutor.\n"
                     "You need to provide answers based on the correct answers and thought processes of the reference"
                     " questions I have provided for you.\n"
                     "You need to imitate the thought process of the reference questions when answering questions.\n"
                     "Your final calculation results must match the correct answers I have provided for you."
                     " If they do not match, please rethink and answer again.\n"
                     "Very important: You need to answer in Chinese.",
                     explain="你是老师")
        ], enable=True),
        UserPrompt([
            TextSpan("三角形最多有2个钝角", explain="题目")
        ]),
        AssistantPrompt([
            TextSpan("这道题是错误的，钝角是指大于90度的角，两个钝角的角度和大于180度。"
                     "如果三角形有两个钝角，那么它三个角的内角和会大于180度，这与三角形的内角和等于180度相矛盾。",
                     explain="解答")
        ]),
        UserPrompt([
            TextSpan("全班有50个学生，每个学生有2个苹果，全班一共有多少个苹果。现在其中一个学生把苹果送给了班级内的另一个学生，这时全班一共有多少个苹果", explain="题目")
        ]),
        AssistantPrompt([
            TextSpan("全班一共有100个苹果。50×2=100\n"
                     "在学生送出苹果后，其中一个学生的减少值，恰好等于另一个学生的增加值。"
                     "题目只关心全班的苹果总数，所以这里的总数不需要再分别计算每个学生的数目，总数不变，仍然是100个。",
                     explain="解答")
        ]),
        UserPrompt([
            TextSpan("小明有10个苹果，小红有10个苹果，小明问小红借了3个苹果，他们一共有多少个苹果？", explain="题目"),
        ]),
        AssistantPrompt([
            TextSpan("两人一共有20个苹果。10+10=20\n"
                     "在借苹果的事情发生前，两人一共有 10+10=20 个苹果。"
                     "我们的问题是计算两人的苹果总数，并不关心小明和小红各自的苹果数目。所以不需要独立计算两人的苹果数。"
                     "小红将苹果借给小明后，小红减少的苹果数目恰好是小明增加的苹果数，所以苹果总数不会发生变化",
                     explain="解答")
        ], enable=True),
        UserPrompt([
            TextSpan("小明有10根铅笔，小红有3根铅笔，小明问小红借了1根铅笔，他们一共有多少根铅笔？", explain="题目"),
        ]),
        SystemPrompt([
            TextSpan("在简单分析后，重新描述下题目和里边的知识点", explain="复述"),
        ]),
        AssistantPrompt([
            TextSpan("小明和小红一共有13根铅笔。题目考察了物品在内部转移不改变总数的概念。", explain="gpt4ans")
        ]),
        SystemPrompt([
            TextSpan("现在尝试解释这道题目", explain="query")
        ])
    ]
    print(chat_gpt3(messages, temperature=0.5))
