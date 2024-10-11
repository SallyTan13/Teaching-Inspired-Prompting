import re
from io import StringIO
from contextlib import redirect_stdout
from typing import List


def normalize(code_str: str):
    code_parts = code_str.split("\n")
    if not code_parts[0]:
        code_parts = code_parts[1:]

    valid_code_parts = []
    empty = re.match(r"(\s+)def", code_parts[0])
    max_empty = len(empty.groups()[0]) if empty else 0
    for line in code_parts:
        valid_code_parts.append(line[max_empty:])
    code_str = "\n".join(valid_code_parts)

    fun_name_m = re.search(r"\s*def\s([^\(]+)", code_str)
    if not fun_name_m:
        return ""
    fun_name = fun_name_m.groups()[0]
    if "return" in code_str:
        code_str += f"\nprint({fun_name}())"
    else:
        code_str += f"\n{fun_name}()"
    code_str = re.sub("```(python)?", "", code_str)
    code_str = "import math\n" + code_str
    return code_str


def do_python(code_str: str):
    code_str = normalize(code_str)
    try:
        _stdout = StringIO()
        with redirect_stdout(_stdout):
            exec(code_str)
        code_ans = _stdout.getvalue()
    except Exception as e:
        code_ans = ""

    if code_ans:
        try:
            code_ans = str(round(float(code_ans), 3))
        except ValueError:
            pass
    return code_ans


def extract_python_code(text: str) -> List:
    lines = text.split("\n")
    solution_idxes = []
    for idx, line in enumerate(lines):
        if "def" in line:
            solution_idxes.append(idx)
    if not solution_idxes:
        return []
    else:
        code_strs = []
        pre_solution_idx = solution_idxes[0]
        for idx in solution_idxes[1:]:
            code_str = "\n".join(lines[pre_solution_idx: idx])
            code_strs.append(code_str)
            pre_solution_idx = idx
        code_str = "\n".join(lines[pre_solution_idx:])
        code_strs.append(code_str)
        return code_strs


if __name__ == '__main__':
    code = """
    def solution():
        x = math.ceil(600 / 3 + 4)
        weight = x * 22
        return weight
    """