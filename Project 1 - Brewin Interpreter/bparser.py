# pylint: disable=too-few-public-methods

"""
Provided module for parsing Brewin programs. When grading your project,
we'll use our own copy; don't submit (or change) your own version!
"""


class StringWithLineNumber(str):
    """
    Wrapper class for str that allows you to add a line number tag (line_num).
    """

    line_num = None

    def __new__(cls, string, line_num):
        instance = super().__new__(cls, string)
        instance.line_num = line_num
        return instance

    def __copy__(self):
        return StringWithLineNumber(self, self.line_num)

    def __deepcopy__(self, _memo):
        return StringWithLineNumber(self, self.line_num)


class BParser:
    """
    Static class that wraps BParser.parse and class-level constants. Do not initialize this class!
    """

    OPEN_PAREN_CHAR = "("
    CLOSE_PAREN_CHAR = ")"
    COMMENT_CHAR = "#"
    QUOTE_CHAR = '"'
    WHITESPACE_CHARS = " \t\r\n"
    DELIMETER_CHARS = WHITESPACE_CHARS + OPEN_PAREN_CHAR + CLOSE_PAREN_CHAR

    @staticmethod
    def parse(lines):
        """
        Maps a list of input strings containing only alphanumeric tokens, spaces, and parentheses
        to a tuple with two items:
        1. A parsing status indicator (True for success, False for failure)
        2. A potentially nested list of tuples representing the tokens in the
        input strings. Each tuple has a line number and an alpha-numeric token.

        Ex:
        (this is (a ((test))))
        (this is too)

        would output:

        (
            True,
            [
                [(0, 'this'), (0, 'is'), [(0, 'a'), [[(0, 'test')]]]],
                [(1, 'this'), (1, 'is'), (1, 'too')]
            ]
        )
        """
        cur_token = ""
        in_quote = False
        output = []
        output_stack = [output]
        for line_no, line in enumerate(lines):
            line = BParser.__remove_comment(line)
            for char in line:
                if char == BParser.QUOTE_CHAR:
                    if not in_quote:
                        if cur_token:
                            token_and_line_num = StringWithLineNumber(
                                cur_token, line_no
                            )
                            output_stack[-1].append(token_and_line_num)
                        cur_token = BParser.QUOTE_CHAR
                        in_quote = True
                    else:
                        cur_token += BParser.QUOTE_CHAR
                        token_and_line_num = StringWithLineNumber(cur_token, line_no)
                        output_stack[-1].append(token_and_line_num)
                        cur_token = ""
                        in_quote = False
                    continue
                if in_quote:
                    cur_token += char
                    continue

                if char in BParser.DELIMETER_CHARS:
                    if cur_token:
                        token_and_line_num = StringWithLineNumber(cur_token, line_no)
                        output_stack[-1].append(token_and_line_num)
                        cur_token = ""
                if char == BParser.OPEN_PAREN_CHAR:
                    nested = output_stack[-1]
                    nested.append([])
                    output_stack.append(nested[-1])
                elif char == BParser.CLOSE_PAREN_CHAR:
                    if len(output_stack) < 2:
                        return False, "Extra closing parenthesis"
                    output_stack.pop()
                elif char not in BParser.WHITESPACE_CHARS:
                    cur_token += char
            if in_quote:
                return False, "Unclosed string"
            if cur_token:
                token_and_line_num = StringWithLineNumber(cur_token, line_no)
                output_stack[-1].append(token_and_line_num)
                cur_token = ""
        if len(output_stack) > 1:
            return False, "Unclosed parenthesis"
        return True, output

    @staticmethod
    def __remove_comment(line):
        in_string = False
        stripped_line = ""
        for char in line:
            if char == BParser.COMMENT_CHAR and not in_string:
                return stripped_line
            if char == BParser.QUOTE_CHAR:
                in_string = not in_string
            stripped_line += char
        return stripped_line