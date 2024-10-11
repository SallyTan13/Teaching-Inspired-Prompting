"""Span is a unit that makes up the Prompt, which can include slots to be filled.
When concatenating prompts, line breaks are not added, so they need to be created manually.

Here, three classes are provided:
ISpan - Interface class
Span - An ISpan with template replacement
TextSpan - An ISpan for static text

Some predefined SPANs are also provided.
"""
import abc
import re
from string import Formatter
from typing import Union, Dict, Any, Mapping, Optional


Slots = Optional[Dict[str, Any]]


_explain_trans = {
    ord('\n'): r'\n',
    ord('\t'): r'\t',
}


class ISpan(abc.ABC):
    @abc.abstractmethod
    def fill_slots(self, slots: Slots = None) -> "ISpan":
        return NotImplemented

    @abc.abstractmethod
    def get_text(self, slots: Slots = None) -> str:
        """用于拼接 prompt"""
        return NotImplemented

    @property
    @abc.abstractmethod
    def explain(self) -> str:
        """用于 debug"""
        return NotImplemented

    @property
    def explain_repr(self) -> str:
        return self.explain.translate(_explain_trans)


class Span(ISpan):
    """支持模板的 ISpan，用法类似 string format:
    some literal {filed_name} some literal
    只支持一个级别的嵌套
    """
    def __init__(self, template: str, explain: str):
        self._template = template
        self._explain = explain
        self.require_slots = _parse_template(self._template)

    def fill_slots(self, slots: Slots = None) -> Union["TextSpan", "Span"]:
        if not self.require_slots:
            return TextSpan(self._template, self._explain)

        slots = {k: v for k, v in slots.items() if k in self.require_slots}
        if not slots:
            return self

        new_template = self._template.format_map(slots)
        if len(slots) == len(self.require_slots):
            return TextSpan(new_template, explain=self._explain)
        return Span(new_template, explain=self._explain)

    def get_text(self, slots: Slots = None):
        not_filled = {k for k in self.require_slots if k not in slots}
        if not_filled:
            not_filled_str = ','.join(not_filled)
            raise RuntimeError(f'{self} has {not_filled_str} not filled')
        return self._template.format_map(slots)

    @property
    def explain(self) -> str:
        return self._explain

    def __repr__(self):
        return f'<Span {self.explain_repr} {len(self.require_slots)}slots>'

    def __str__(self):
        return self.get_text()


class TextSpan(ISpan):
    """纯文本形式的 ISpan，视为 const 的"""
    def __init__(self, text, explain):
        self._text = text
        self._explain = explain

    def fill_slots(self, slots: Slots = None) -> "TextSpan":
        return self

    @property
    def text(self) -> str:
        return self._text

    def get_text(self, slots: Slots = None) -> str:
        return self._text

    @property
    def explain(self) -> str:
        return self._explain

    def __repr__(self):
        return f'<TextSpan {self.explain_repr}>'

    def __str__(self):
        return self.text


_formatter = Formatter()
_field_validator = re.compile(r'^[_a-zA-Z][_a-zA-Z0-9]*$')


def _parse_template(template):
    """parse template，get the slotting"""
    slots = set()
    for literal, field_name, format_spec, conversion in _formatter.parse(template):
        if field_name is None:
            continue
        if not _field_validator.match(field_name):
            raise ValueError(f'invalid template field: {field_name}')
        slots.add(field_name)
    return slots


if __name__ == '__main__':
    print()
    # span1 = Span('{0} abcd {1}', 'span1')  # will raise error
    span2 = Span('{a}___{b}', 'span2')
    # span2.get_text({})  # will raise error
    text2 = span2.get_text({
        "a": 1,
        "b": 2
    })
    print(text2)
    span3 = span2.fill_slots({'a': 1, 'b': 2})
    text3 = span3.get_text({})
    print(text3)
