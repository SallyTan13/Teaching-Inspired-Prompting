import abc

from .span import ISpan, Slots
from typing import Iterable, Optional


class IPrompt(abc.ABC):
    @abc.abstractmethod
    def get_text(self, slots: Slots) -> str:
        return NotImplemented


class Prompt(IPrompt):
    def __init__(self, role: str, spans: Iterable[ISpan], slots: Slots = None, enable=True):
        self.role = role
        if slots:
            self._spans = [span.fill_slots(slots) for span in spans]
        else:
            self._spans = list(spans)
        self.enable = enable

    def get_text(self, slots: Slots = None) -> str:
        texts = []
        for span in self._spans:
            texts.append(span.get_text(slots))
        return ''.join(texts)

    def get_message(self, slots: Slots = None) -> dict:
        return {
            "role": self.role,
            "content": self.get_text(slots)
        }

    def __repr__(self):
        explains_repr = '·'.join(s.explain_repr for s in self._spans)
        return f'<{self.role.capitalize()} {explains_repr}>'


class SystemPrompt(Prompt):
    def __init__(self, spans: Iterable[ISpan], slots: Slots = None, enable=True):
        super().__init__('system', spans, slots)


class UserPrompt(Prompt):
    def __init__(self, spans: Iterable[ISpan], slots: Slots = None, enable=True):
        super().__init__('user', spans, slots)


class AssistantPrompt(Prompt):
    def __init__(self, spans: Iterable[ISpan], slots: Slots = None, enable=True):
        super().__init__('assistant', spans, slots)
