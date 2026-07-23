"""Named OpenCV keyboard values used by network screens."""


class KeyBindings:
    ESCAPE = 27
    TAB = 9
    BACKSPACE = frozenset((8, 127))
    ENTER = frozenset((10, 13))
    SPACE = 32
    PRINTABLE_FIRST = 32
    PRINTABLE_LAST = 126

    @staticmethod
    def is_key(key, character: str) -> bool:
        return key in (ord(character.lower()), ord(character.upper()))

    @classmethod
    def is_printable(cls, key) -> bool:
        return cls.PRINTABLE_FIRST <= key <= cls.PRINTABLE_LAST
