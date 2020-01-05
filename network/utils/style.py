from typing import Optional

__all__ = ['style']


# Classes
class EscapeCode:
    def __init__(self, *codes: int, name: Optional[str] = None):
        self.name = name
        self.codes = codes

    def __repr__(self):
        codes = ', '.join(str(code) for code in self.codes)

        if self.name is None:
            return style.blue(f'<Code: {self(codes)}>')

        return style.blue(f'<Code: {self(codes)} ({self.name})>')

    def __str__(self):
        if not style.enabled:
            return ''

        codes = ';'.join(str(code) for code in self.codes)

        return f'\033[{codes}m'

    def __call__(self, txt: str):
        return f'{self}{txt}{style.reset}'

    def __add__(self, other):
        if isinstance(other, EscapeCode):
            return EscapeCode(*self.codes, *other.codes)

        elif isinstance(other, str):
            return str(self) + other

        return NotImplementedError


class Style:
    def __init__(self):
        self.enabled = True

    # Properties
    @property
    def reset(self) -> EscapeCode:
        return EscapeCode(name='reset')

    @property
    def bold(self) -> EscapeCode:
        return EscapeCode(1, name='bold')

    @property
    def italic(self) -> EscapeCode:
        return EscapeCode(3, name='italic')

    @property
    def underline(self) -> EscapeCode:
        return EscapeCode(4, name='underline')

    @property
    def red(self) -> EscapeCode:
        return EscapeCode(31, name='red')

    @property
    def green(self) -> EscapeCode:
        return EscapeCode(32, name='green')

    @property
    def yellow(self) -> EscapeCode:
        return EscapeCode(33, name='yellow')

    @property
    def blue(self) -> EscapeCode:
        return EscapeCode(34, name='blue')

    @property
    def purple(self) -> EscapeCode:
        return EscapeCode(35, name='purple')

    @property
    def white(self) -> EscapeCode:
        return EscapeCode(38, name='white')


# Instance
style = Style()
