from typing import Optional, Union

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
        codes = ';'.join(str(code) for code in self.codes)

        return f'\033[{codes}m'

    def __call__(self, txt: str):
        return f'{self}{txt}{style.reset}'

    def __add__(self, other):
        if isinstance(other, EscapeCode):
            return EscapeCode(*self.codes, *other.codes)

        elif isinstance(other, str):
            return str(self) + other

        return NotImplemented


class NoCode(EscapeCode):
    def __repr__(self):
        return style.blue('<NoCode>')

    def __str__(self):
        return ""

    def __call__(self, txt: str):
        return txt

    def __add__(self, other):
        if isinstance(other, EscapeCode) or isinstance(other, str):
            return other

        return NotImplemented


class Style:
    def __init__(self):
        self.enabled = True

    # Properties
    @property
    def reset(self) -> Union[EscapeCode, NoCode]:
        return EscapeCode(name='reset') if self.enabled else NoCode()

    @property
    def bold(self) -> Union[EscapeCode, str]:
        return EscapeCode(1, name='bold') if self.enabled else NoCode()

    @property
    def italic(self) -> Union[EscapeCode, str]:
        return EscapeCode(3, name='italic') if self.enabled else NoCode()

    @property
    def underline(self) -> Union[EscapeCode, str]:
        return EscapeCode(4, name='underline') if self.enabled else NoCode()

    @property
    def red(self) -> Union[EscapeCode, str]:
        return EscapeCode(31, name='red') if self.enabled else NoCode()

    @property
    def green(self) -> Union[EscapeCode, str]:
        return EscapeCode(32, name='green') if self.enabled else NoCode()

    @property
    def yellow(self) -> Union[EscapeCode, str]:
        return EscapeCode(33, name='yellow') if self.enabled else NoCode()

    @property
    def blue(self) -> Union[EscapeCode, str]:
        return EscapeCode(34, name='blue') if self.enabled else NoCode()

    @property
    def purple(self) -> Union[EscapeCode, str]:
        return EscapeCode(35, name='purple') if self.enabled else NoCode()

    @property
    def white(self) -> Union[EscapeCode, str]:
        return EscapeCode(38, name='white') if self.enabled else NoCode()


# Instance
style = Style()
