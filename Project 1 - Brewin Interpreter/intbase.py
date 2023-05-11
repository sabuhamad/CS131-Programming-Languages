"""
Module that contains the enum ErrorType and the InterpreterBase that you should
subclass when writing your own interpreter.

When grading, we will use our own copy of intbase; you should not submit a copy of it,
or make any changes to your local copy!
"""

from enum import Enum
from bparser import BParser


class ErrorType(Enum):
    """
    Enum for all possible errors that you'll be tested on.
    """

    TYPE_ERROR = 1
    NAME_ERROR = 2  # if a variable or function name can't be found
    SYNTAX_ERROR = 3  # used for syntax errors
    FAULT_ERROR = 4  # used if an object reference is null and used to make a call


class InterpreterBase:
    """
    Base class for the interpreter; your implementation should subclass InterpreterBase.
    """

    # constants
    CLASS_DEF = "class"
    METHOD_DEF = "method"
    FIELD_DEF = "field"
    NULL_DEF = "null"
    BEGIN_DEF = "begin"
    SET_DEF = "set"
    NEW_DEF = "new"
    IF_DEF = "if"
    WHILE_DEF = "while"
    MAIN_CLASS_DEF = "main"
    MAIN_FUNC_DEF = "main"
    CALL_DEF = "call"
    TEMPLATE_CLASS_DEF = "tclass"
    RETURN_DEF = "return"
    INPUT_STRING_DEF = "inputs"
    INPUT_INT_DEF = "inputi"
    TRUE_DEF = "true"
    FALSE_DEF = "false"
    PRINT_DEF = "print"
    ME_DEF = "me"
    NOTHING_DEF = "nothing"
    INHERITS_DEF = "inherits"
    SUPER_DEF = "super"
    INT_DEF = "int"
    BOOL_DEF = "bool"
    STRING_DEF = "string"
    VOID_DEF = "void"
    LET_DEF = "let"
    THROW_DEF = "throw"
    TRY_DEF = "try"
    EXCEPTION_VARIABLE_DEF = "exception"
    TYPE_CONCAT_CHAR = "@"

    # methods
    def __init__(self, console_output=True, inp=None):
        self.console_output = console_output
        self.inp = inp  # if not none, then read input from passed-in list
        self.output_log = []
        self.input_cursor = 0
        self.error_type = None
        self.error_line = None

    def reset(self):
        """
        "Reset" I/O for another run of the program
        """
        self.output_log = []
        self.input_cursor = 0
        self.error_type = None
        self.error_line = None

    def run(self, program):
        """Run a program. You need to implement this in your derived class!"""

    def get_input(self):
        """
        Wrap python's input() to allow user-supplied input instead of stdin.
        """
        if not self.inp:
            return input()  # Get input from keyboard if not input list provided

        if self.input_cursor < len(self.inp):
            cur_input = self.inp[self.input_cursor]
            self.input_cursor += 1
            return cur_input

        return None

    def error(self, error_type, description=None, line_num=None):
        """
        A method to log any errors. Your derived class must call this
        function for any errors that you run into!
        """
        # log the error before we throw
        self.error_line = line_num
        self.error_type = error_type

        if description:
            description = ": " + description
        else:
            description = ""

        if line_num:
            raise RuntimeError(f"{error_type} on line {line_num}{description}")

        raise RuntimeError(f"{error_type}{description}")

    def output(self, val):
        """
        Wrapper for stdout (letting us spy on output and control if it's printed).
        Students should call this when they want to print to stdout!
        """
        if self.console_output:
            print(val)
        self.output_log.append(val)

    def get_output(self):
        """Get full output log (what should have gone to stdout.)"""
        return self.output_log

    def get_error_type_and_line(self):
        """If an error has occured, return its type and line number."""
        return self.error_type, self.error_line

    def validate_program(self, program):
        """Predicate for if a program is properly formed (i.e. has valid syntax)."""
        result, _ = BParser.parse(program)
        return result