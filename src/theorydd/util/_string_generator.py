"""this module defines a Walker that takes an object that 
sequantially generates strings of letters"""


class SequentialStringGenerator:
    """A class that generates possibly infinitely many strings in sequential order"""

    _last_string: str

    def __init__(self) -> None:
        self.reset()

    def next_string(self) -> str:
        """generates the next string in sequential order"""
        # if the last string is empty, return "a"
        if self._last_string == "":
            self._last_string = "a"
            return self._last_string

        # if the last string ends with "z", add "a" to the end
        last_char = self._last_string[-1]
        if last_char == "z":
            self._last_string += "a"
            return self._last_string

        # otherwise, increment the last character
        # (example "b" -> "c", "d" -> "e")
        new_last_char = chr(ord(last_char) + 1)
        self._last_string = self._last_string[:-1] + new_last_char
        return self._last_string

    def reset(self) -> None:
        """resets the generator"""
        # reset the last string to empty
        self._last_string = ""


if __name__ == "__main__":
    s = SequentialStringGenerator()
    for i in range(0, 100):
        print(s.next_string())
