"""this module defines a Walker that takes an object that 
sequantially generates strings of letters"""

from typing import List


def _char_from_remainder(remainder: int) -> str:
    """matches the integer from the remainder with the
    corresponding char in the sequential string generation"""
    match remainder:
        case 0:
            return "a"
        case 1:
            return "b"
        case 2:
            return "c"
        case 3:
            return "d"
        case 4:
            return "e"
        case 5:
            return "f"
        case 6:
            return "g"
        case 7:
            return "h"
        case 8:
            return "i"
        case 9:
            return "j"
        case 10:
            return "k"
        case 11:
            return "l"
        case 12:
            return "m"
        case 13:
            return "n"
        case 14:
            return "o"
        case 15:
            return "p"
        case 16:
            return "q"
        case 17:
            return "r"
        case 18:
            return "s"
        case 19:
            return "t"
        case 20:
            return "u"
        case 21:
            return "v"
        case 22:
            return "w"
        case 23:
            return "x"
        case 24:
            return "y"
        case 25:
            return "z"
        case _:
            return None


def _concatenate_string_array(array: List[str]) -> str:
    """concatenates an array of strings into a single string"""
    result = ""
    array.reverse()
    for string in array:
        result += string
    return result

class SequentialStringGenerator:
    """A class that generates possibly infinitely many strings in sequential order"""

    def __init__(self) -> None:
        self._string_serial = 0

    def next_string(self) -> str:
        """generates the next string in sequential order"""
        temp = self._string_serial
        result, remainder = divmod(temp, 26)
        str_builder = []
        next_char = _char_from_remainder(remainder)
        str_builder.append(next_char)
        while result > 0:
            result, remainder = divmod(result - 1, 26)
            next_char = _char_from_remainder(remainder)
            str_builder.append(next_char)
        self._string_serial += 1
        return _concatenate_string_array(str_builder)

    def reset(self) -> None:
        """resets the generator"""
        self._string_serial = 0


if __name__ == "__main__":
    s = SequentialStringGenerator()
    for i in range(0, 100):
        print(s.next_string())
