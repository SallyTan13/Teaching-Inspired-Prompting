from typing import Callable, Optional


class Command:
    def __init__(self, name, description, target: Optional[Callable] = None):
        """cmd_span = Span("Command {name} run with result {result}", "命令结果")

        cmd_span.fill_slots(name=cmd.name, result=cmd_result)

        """
        self.name = name
        self.target = target
        self._description = description

    def run(self, *args, **kwargs):
        if not self.target:
            raise ValueError("target is not set")
        return self.target(*args, **kwargs)

