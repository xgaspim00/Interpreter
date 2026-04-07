"""
This module contains the built-in classes and functions for the SOL language.
"""

from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError
from interpreter.runtime import SolClass, SolObject

OBJECT_CLASS = SolClass(name="Object", superclass=None)
INTEGER_CLASS = SolClass(name="Integer", superclass=OBJECT_CLASS)
STRING_CLASS = SolClass(name="String", superclass=OBJECT_CLASS)
BOOLEAN_CLASS = SolClass(name="Boolean", superclass=OBJECT_CLASS)
NIL_CLASS = SolClass(name="Nil", superclass=OBJECT_CLASS)
BLOCK_CLASS = SolClass(name="Block", superclass=OBJECT_CLASS)
TRUE_CLASS = SolClass(name="True", superclass=BOOLEAN_CLASS)
FALSE_CLASS = SolClass(name="False", superclass=BOOLEAN_CLASS)

NIL = SolObject(sol_class=NIL_CLASS, value=None)
TRUE = SolObject(sol_class=TRUE_CLASS, value=None)
FALSE = SolObject(sol_class=FALSE_CLASS, value=None)


def integer_plus(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements the Integer.plus: method."""
    # Check that there is exactly one argument
    if len(args) != 1:
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER, message="Integer.plus expects exactly one argument"
        )
    arg = args[0]  # Extract the single argument
    # Check that both receiver and argument are of class Integer
    if receiver.sol_class != INTEGER_CLASS or arg.sol_class != INTEGER_CLASS:
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER,
            message="Integer.plus expects both receiver and argument to be of class Integer",
        )
    # Check that both receiver and argument have integer values
    if not isinstance(receiver.value, int) or not isinstance(arg.value, int):
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER,
            message="Integer.plus expects both receiver and argument to have integer values",
        )
    # Perform the addition and return a new Integer object with the result
    result_value = receiver.value + arg.value
    # Return a new SolObject representing the result of the addition
    return SolObject(sol_class=INTEGER_CLASS, value=result_value)


def integer_minus(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements the Integer.minus: method."""
    # Check that there is exactly one argument
    if len(args) != 1:
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER, message="Integer.minus expects exactly one argument"
        )
    # Extract the single argument
    arg = args[0]
    # Check that both receiver and argument are of class Integer
    if receiver.sol_class != INTEGER_CLASS or arg.sol_class != INTEGER_CLASS:
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER,
            message="Integer.minus expects both receiver and argument to be of class Integer",
        )
    # Check that both receiver and argument have integer values
    if not isinstance(receiver.value, int) or not isinstance(arg.value, int):
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER,
            message="Integer.minus expects both receiver and argument to have integer values",
        )
    # Perform the subtraction and return a new Integer object with the result
    result_value = receiver.value - arg.value
    # Return a new SolObject representing the result of the subtraction
    return SolObject(sol_class=INTEGER_CLASS, value=result_value)


def integer_multiply(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements the Integer.multiplyBy: method."""
    # Check that there is exactly one argument
    if len(args) != 1:
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER,
            message="Integer.multiplyBy expects exactly one argument",
        )
    # Extract the single argument
    arg = args[0]
    # Check that both receiver and argument are of class Integer
    if receiver.sol_class != INTEGER_CLASS or arg.sol_class != INTEGER_CLASS:
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER,
            message="Integer.multiplyBy expects both receiver and argument to be of class Integer",
        )
    # Check that both receiver and argument have integer values
    if not isinstance(receiver.value, int) or not isinstance(arg.value, int):
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER,
            message="Integer.multiplyBy expects both receiver and argument to have integer values",
        )
    # Perform the multiplication and return a new Integer object with the result
    result_value = receiver.value * arg.value
    # Return a new SolObject representing the result of the multiplication
    return SolObject(sol_class=INTEGER_CLASS, value=result_value)


def integer_divide(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements the Integer.divideBy: method."""
    # Check that there is exactly one argument
    if len(args) != 1:
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER, message="Integer.divideBy expects exactly one argument"
        )
    # Extract the single argument
    arg = args[0]
    # Check that both receiver and argument are of class Integer
    if receiver.sol_class != INTEGER_CLASS or arg.sol_class != INTEGER_CLASS:
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER,
            message="Integer.divideBy expects both receiver and argument to be of class Integer",
        )
    # Check that both receiver and argument have integer values
    if not isinstance(receiver.value, int) or not isinstance(arg.value, int):
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER,
            message="Integer.divideBy expects both receiver and argument to have integer values",
        )
    # Check for division by zero
    if arg.value == 0:
        raise InterpreterError(
            error_code=ErrorCode.INT_INVALID_ARG,
            message="Integer.divideBy expects argument to be non-zero",
        )
    # Perform the integer division and return a new Integer object with the result
    result_value = receiver.value // arg.value
    # Return a new SolObject representing the result of the division
    return SolObject(sol_class=INTEGER_CLASS, value=result_value)


def equal_int(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements the Object.eqal: method."""
    # Check that there is exactly one argument
    if len(args) != 1:
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER, message="Object.eqal: expects exactly one argument"
        )
    arg = args[0]  # Extract the single argument
    # Check for reference equality (i.e., whether receiver and argument are the same object)
    if not isinstance(receiver.value, int) or not isinstance(arg.value, int):
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER,
            message="Object.eqal: expects both receiver and argument to have integer values",
        )
    return TRUE if receiver.value == arg.value else FALSE


def greater_than(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements the Integer.greaterThan: method."""
    # Check that there is exactly one argument
    if len(args) != 1:
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER,
            message="Integer.greaterThan: expects exactly one argument",
        )
    arg = args[0]  # Extract the single argument
    # Check that both receiver and argument are of class Integer
    if receiver.sol_class != INTEGER_CLASS or arg.sol_class != INTEGER_CLASS:
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER,
            message="Integer.greaterThan: expects to be of class Integer",
        )
    # Check that both receiver and argument have integer values
    if not isinstance(receiver.value, int) or not isinstance(arg.value, int):
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER,
            message="Integer.greaterThan: expects to have integer values",
        )
    # Perform the comparison and return TRUE if receiver is greater than argument
    if receiver.value > arg.value:
        return TRUE
    return FALSE


def as_string(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements the Object.asString method."""
    # Check that there are no arguments
    if len(args) != 0:
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER, message="Object.asString expects no arguments"
        )
    # Convert the receiver's value to a string and return a new String object with that value
    result_value = str(receiver.value)
    return SolObject(sol_class=STRING_CLASS, value=result_value)


def times_repeat(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements the Integer.timesRepeat: method."""
    return NIL


def print_string(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements the String.print method."""
    # Check that there are no arguments
    if len(args) != 0:
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER, message="String.print expects no arguments"
        )
    # Print the receiver's value to the console
    print(receiver.value)
    return NIL


def equal_string(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements the String.equalTo method"""
    if len(args) != 1:
        raise InterpreterError(
            error_code=ErrorCode.INT_INVALID_ARG,
            message="equalTo with strings expects one argument",
        )
    string = args[0]
    if receiver.value == string.value:
        return TRUE
    return FALSE


def convert_to_integer(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements the String.asInteger method."""
    if len(args) != 0:
        raise InterpreterError(
            error_code=ErrorCode.INT_INVALID_ARG, message="String.asInteger expects no arguments"
        )
    if not isinstance(receiver.value, str):
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER,
            message="String.asInteger expects the receiver to have a string value",
        )
    try:
        int_value = int(receiver.value)
        return SolObject(sol_class=INTEGER_CLASS, value=int_value)
    except ValueError as e:
        raise InterpreterError(
            error_code=ErrorCode.INT_INVALID_ARG,
            message="String.asInteger expects the string to be a valid integer",
        ) from e


def read(args: list[SolObject]) -> SolObject:
    """Implements the Object.read method."""
    if len(args) != 0:
        raise InterpreterError(
            error_code=ErrorCode.INT_INVALID_ARG, message="Object.read expects no arguments"
        )
    try:
        input_value = input()
        return SolObject(sol_class=STRING_CLASS, value=input_value)
    except EOFError as e:
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER, message="Object.read encountered an unexpected EOF"
        ) from e


def string_size(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements the String.size method."""
    if len(args) != 0:
        raise InterpreterError(
            error_code=ErrorCode.INT_INVALID_ARG, message="String.size expects no arguments"
        )
    if receiver.sol_class != STRING_CLASS:
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER,
            message="String.size expects the receiver to be of class String",
        )
    if not isinstance(receiver.value, str):
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER,
            message="String.size expects the receiver to have a string value",
        )
    size_value = len(receiver.value)
    return SolObject(sol_class=INTEGER_CLASS, value=size_value)


def string_starts_with_ends_before(receiver: SolObject, args: list[SolObject]) -> SolObject:
    # type narrowing
    if not isinstance(receiver.value, str):
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER,
            message="startsWith:endsBefore: receiver must be a String",
        )
    if not isinstance(args[0].value, int) or not isinstance(args[1].value, int):
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER,
            message="startsWith:endsBefore: arguments must be Integers",
        )
    start = args[0].value
    end = args[1].value
    result = receiver.value[start - 1 : end - 1]
    return SolObject(sol_class=STRING_CLASS, value=result)


def true_not(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements True.not - returns FALSE."""
    return FALSE


def false_not(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements False.not - returns TRUE."""
    return TRUE


def true_if_true_if_false(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements True.ifTrue:ifFalse: - evaluates the first (true) block."""
    # args[0] is the true block, args[1] is the false block
    # Block evaluation will be filled in once Block methods are implemented
    return NIL


def false_if_true_if_false(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements False.ifTrue:ifFalse: - evaluates the second (false) block."""
    # args[0] is the true block, args[1] is the false block
    # Block evaluation will be filled in once Block methods are implemented
    return NIL


def true_and(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements True.and: - evaluates and returns the argument block."""
    # TRUE and X = X, so evaluate the block
    # Block evaluation will be filled in once Block methods are implemented
    return NIL


def false_and(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements False.and: - short-circuits, returns FALSE without evaluating."""
    return FALSE


def true_or(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements True.or: - short-circuits, returns TRUE without evaluating."""
    return TRUE


def false_or(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements False.or: - evaluates and returns the argument block."""
    # FALSE or X = X, so evaluate the block
    # Block evaluation will be filled in once Block methods are implemented
    return NIL


def while_true(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements Block.whileTrue: - will be implemented with Block support."""
    return NIL


def equal_object(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements the Object.equalTo: method for reference equality."""
    if len(args) != 1:
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER, message="Object.equalTo: expects exactly one argument"
        )
    arg = args[0]
    return TRUE if receiver is arg else FALSE


def is_nil(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements the Object.isNil method."""
    if len(args) != 0:
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER, message="Object.isNil expects no arguments"
        )
    return TRUE if receiver is NIL else FALSE


def identical_object(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements the Object.identicalTo: method for reference equality."""
    if len(args) != 1:
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER,
            message="Object.identicalTo: expects exactly one argument",
        )
    arg = args[0]
    return TRUE if receiver is arg else FALSE


def new_object(receiver: SolObject, args: list[SolObject]) -> SolObject:
    """Implements the Object.new method."""
    return NIL


# Register the methods in the INTEGER_CLASS
INTEGER_CLASS.methods["plus:"] = integer_plus
INTEGER_CLASS.methods["minus:"] = integer_minus
INTEGER_CLASS.methods["multiplyBy:"] = integer_multiply
INTEGER_CLASS.methods["divBy:"] = integer_divide
INTEGER_CLASS.methods["greaterThan:"] = greater_than
INTEGER_CLASS.methods["equalTo:"] = equal_int
INTEGER_CLASS.methods["asString"] = as_string
INTEGER_CLASS.methods["timesRepeat:"] = times_repeat
# Register the methods in the STRING_CLASS
STRING_CLASS.methods["print"] = print_string
STRING_CLASS.methods["equalTo:"] = equal_string
STRING_CLASS.methods["asInteger"] = convert_to_integer
STRING_CLASS.methods["size"] = string_size
STRING_CLASS.methods["read"] = read
STRING_CLASS.methods["startsWith:endsBefore:"] = string_starts_with_ends_before

# Register the methods in TRUE_CLASS and FALSE_CLASS
TRUE_CLASS.methods["not"] = true_not
FALSE_CLASS.methods["not"] = false_not
TRUE_CLASS.methods["ifTrue:ifFalse:"] = true_if_true_if_false
FALSE_CLASS.methods["ifTrue:ifFalse:"] = false_if_true_if_false
TRUE_CLASS.methods["and:"] = true_and
FALSE_CLASS.methods["and:"] = false_and
TRUE_CLASS.methods["or:"] = true_or
FALSE_CLASS.methods["or:"] = false_or

# Register the read method in the OBJECT_CLASS, so that it is available on all objects
OBJECT_CLASS.methods["equalTo:"] = equal_object
OBJECT_CLASS.methods["isNil"] = is_nil
OBJECT_CLASS.methods["identicalTo:"] = identical_object
OBJECT_CLASS.methods["asString"] = as_string
OBJECT_CLASS.methods["new"] = new_object
