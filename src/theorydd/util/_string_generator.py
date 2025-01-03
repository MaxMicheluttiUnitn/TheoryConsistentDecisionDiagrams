"""this module defines an object that 
sequantially generates strings of letters"""


def _next_char(c: str) -> str:
    """returns the next character in the alphabet,

    Args:
        c (str): a single character between 'a' and 'y'

    Returns:
        str: the next character in the alphabet
    """
    return chr(ord(c) + 1)


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

        # if the last string ends with "z"
        last_char = self._last_string[-1]
        if last_char == "z":
            # find the last character that is not "z"
            # and increment it
            # followed by changing all the characters after it to "a"
            for j in range(len(self._last_string) - 1, -1, -1):
                if self._last_string[j] != "z":
                    tail_zs_length = len(self._last_string) - j - 1
                    # last_string = last_string until j-th character + next_char(last non z) + a tail of a's
                    self._last_string = (
                        self._last_string[:j]
                        + _next_char(self._last_string[j])
                        + ("a" * tail_zs_length)
                    )
                    return self._last_string

            # if they are all z's, change string to all a's and add an a to the end
            self._last_string = "a" * len(self._last_string) + "a"
            return self._last_string

        # otherwise, just increment the last character
        # (example "b" -> "c", "d" -> "e")
        self._last_string = self._last_string[:-1] + _next_char(last_char)
        return self._last_string

    def reset(self) -> None:
        """resets the generator"""
        # reset the last string to empty
        self._last_string = ""


if __name__ == "__main__":
    s = SequentialStringGenerator()
    for i in range(0, 1000000):
        print(s.next_string())
