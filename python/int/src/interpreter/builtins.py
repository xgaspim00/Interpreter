"""
This module defines the builtin classes and methods

Author: Marek Gašpierik (xgaspim00)

This file implements only static methods that are independent of the program's
runtime state. Dynamic methods are implemented and injected dynamically by the
Interpreter class in `interpreter.py`.
"""

import math
from collections.abc import Callable

from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError
from interpreter.runtime import SolClass, SolObject

# Define the core classes and singleton objects for the SOL language.
OBJECT_CLASS = SolClass(name="Object", superclass=None)
INTEGER_CLASS = SolClass(name="Integer", superclass=OBJECT_CLASS)
STRING_CLASS = SolClass(name="String", superclass=OBJECT_CLASS)
NIL_CLASS = SolClass(name="Nil", superclass=OBJECT_CLASS)
BLOCK_CLASS = SolClass(name="Block", superclass=OBJECT_CLASS)
TRUE_CLASS = SolClass(name="True", superclass=OBJECT_CLASS)
FALSE_CLASS = SolClass(name="False", superclass=OBJECT_CLASS)

NIL = SolObject(sol_class=NIL_CLASS, value=None)
TRUE = SolObject(sol_class=TRUE_CLASS, value=None)
FALSE = SolObject(sol_class=FALSE_CLASS, value=None)


def _is_instance_of(obj: SolObject, target: SolClass) -> bool:
    """Returns True if obj's class is target or a subclass of target."""
    cls: SolClass | None = obj.sol_class
    while cls is not None:
        if cls is target:
            return True
        cls = cls.superclass
    return False


def _check_arity(method_name: str, args: list[SolObject], expected: int) -> None:
    """
    Helper function to check that the number of arguments matches
    the expected arity for a method.
    """
    if len(args) != expected:
        raise InterpreterError(
            error_code=ErrorCode.INT_INVALID_ARG,
            message=f"{method_name} expects {expected} arguments, got {len(args)}",
        )


class IntegerMethods:
    """
    Namespace for built-in SOL Integer methods.
    """

    @staticmethod
    def _validate(receiver: SolObject, args: list[SolObject]) -> tuple[int, int]:
        """
        Helper method to validate that the receiver and argument
        are Integers and extract their values.
        """
        _check_arity("Integer", args, 1)
        arg = args[0]
        if not isinstance(receiver.value, int) or not isinstance(arg.value, int):
            raise InterpreterError(
                error_code=ErrorCode.INT_INVALID_ARG,
                message="Integer method expects both receiver and argument to be Integers",
            )
        return receiver.value, arg.value

    @staticmethod
    def _make_arithmetic(op: str) -> Callable[[SolObject, list[SolObject]], SolObject]:
        """Factory method to create arithmetic methods for Integer."""

        def method(receiver: SolObject, args: list[SolObject]) -> SolObject:
            a, b = IntegerMethods._validate(receiver, args)
            match op:
                case "+":
                    result = a + b
                case "-":
                    result = a - b
                case "*":
                    result = a * b
                case "/":
                    if b == 0:
                        raise InterpreterError(
                            error_code=ErrorCode.INT_INVALID_ARG,
                            message="Division by zero",
                        )
                    result = math.trunc(a / b)
                case _:
                    raise ValueError(f"Unknown arithmetic op: {op}")
            return SolObject(sol_class=INTEGER_CLASS, value=result)

        return method

    # Define the arithmetic methods using the factory.
    plus = _make_arithmetic("+")
    minus = _make_arithmetic("-")
    multiply = _make_arithmetic("*")
    div = _make_arithmetic("/")

    @staticmethod
    def greater_than(receiver: SolObject, args: list[SolObject]) -> SolObject:
        """
        Returns true if the integer value of the receiver is greater
        than the integer value of the argument, false otherwise.
        """
        a, b = IntegerMethods._validate(receiver, args)
        return TRUE if a > b else FALSE

    @staticmethod
    def equal_to(receiver: SolObject, args: list[SolObject]) -> SolObject:
        """
        Returns true if the receiver and argument have the same integer value
        false otherwise.
        """
        a, b = IntegerMethods._validate(receiver, args)
        return TRUE if a == b else FALSE

    @staticmethod
    def as_string(receiver: SolObject, args: list[SolObject]) -> SolObject:
        """Returns a string representation of the integer value of the receiver."""
        _check_arity("Integer.asString", args, 0)
        return SolObject(sol_class=STRING_CLASS, value=str(receiver.value))

    @staticmethod
    def as_integer(receiver: SolObject, _args: list[SolObject]) -> SolObject:
        """Returns the receiver itself."""
        return receiver

    @staticmethod
    def times_repeat(_receiver: SolObject, _args: list[SolObject]) -> SolObject:
        """Placeholder overridden by the Interpreter at runtime.

        The actual implementation requires access to the runtime execution context
        to invoke a block repeatedly, so it is injected by
        Interpreter._register_conditional_methods.
        """
        return NIL


class StringMethods:
    """
    Namespace for built-in SOL String methods.
    """

    @staticmethod
    def print(receiver: SolObject, args: list[SolObject]) -> SolObject:
        """Prints the string value of the receiver to standard output."""
        _check_arity("String.print", args, 0)
        print(receiver.value, end="")
        return receiver

    @staticmethod
    def equal_to(receiver: SolObject, args: list[SolObject]) -> SolObject:
        """Returns true if the receiver and argument are equal (have the same value)"""
        _check_arity("String.equalTo", args, 1)
        return TRUE if receiver.value == args[0].value else FALSE

    @staticmethod
    def as_integer(receiver: SolObject, args: list[SolObject]) -> SolObject:
        """
        Returns the integer value of the string if it is a valid integer representation
        or nil otherwise.
        """
        _check_arity("String.asInteger", args, 0)
        if not isinstance(receiver.value, str):
            raise InterpreterError(
                error_code=ErrorCode.INT_OTHER,
                message="String.asInteger: receiver must be a String",
            )
        try:
            return SolObject(sol_class=INTEGER_CLASS, value=int(receiver.value))
        except ValueError:
            return NIL  # spec: returns nil if not a valid integer

    @staticmethod
    def as_string(receiver: SolObject, _args: list[SolObject]) -> SolObject:
        """Returns the receiver itself."""
        return receiver

    @staticmethod
    def concatenate_with(receiver: SolObject, args: list[SolObject]) -> SolObject:
        """Concatenates the receiver with the argument and returns a new String object."""
        _check_arity("String.concatenateWith", args, 1)
        if not _is_instance_of(args[0], STRING_CLASS):
            return NIL  # spec: non-String argument → nil
        if not isinstance(receiver.value, str) or not isinstance(args[0].value, str):
            return NIL
        return SolObject(sol_class=STRING_CLASS, value=receiver.value + args[0].value)

    @staticmethod
    def length(receiver: SolObject, args: list[SolObject]) -> SolObject:
        """
        Returns the length of the string.
        Raises an error if the receiver is not a String or if any arguments are provided.
        """
        _check_arity("String.length", args, 0)
        if not isinstance(receiver.value, str):
            raise InterpreterError(
                error_code=ErrorCode.INT_OTHER,
                message="String.length: receiver must be a String",
            )
        return SolObject(sol_class=INTEGER_CLASS, value=len(receiver.value))

    @staticmethod
    def starts_with_ends_before(receiver: SolObject, args: list[SolObject]) -> SolObject:
        """
        Returns a substring of the receiver using 1-based indices.

        args[0] is the start index (inclusive), args[1] is the end index (exclusive).
        Returns nil if either argument is not a positive Integer.
        """
        _check_arity("String.startsWith:endsBefore", args, 2)
        if not isinstance(receiver.value, str):
            raise InterpreterError(
                error_code=ErrorCode.INT_OTHER,
                message="startsWith:endsBefore: receiver must be a String",
            )
        if not _is_instance_of(args[0], INTEGER_CLASS) or not _is_instance_of(
            args[1], INTEGER_CLASS
        ):
            return NIL
        if not isinstance(args[0].value, int) or not isinstance(args[1].value, int):
            return NIL
        start, end = args[0].value, args[1].value
        if start <= 0 or end <= 0:
            return NIL
        # Convert from 1-based inclusive indices to 0-based exclusive indices for Python slicing.
        return SolObject(sol_class=STRING_CLASS, value=receiver.value[start - 1 : end - 1])


class NilMethods:
    """Static namespace for built-in SOL Nil methods."""

    @staticmethod
    def as_string(_receiver: SolObject, _args: list[SolObject]) -> SolObject:
        """Returns the string "nil" for the Nil object."""
        return SolObject(sol_class=STRING_CLASS, value="nil")


class ObjectMethods:
    """
    Implementation of methods for the SOL Object class.
    """

    @staticmethod
    def equal_to(receiver: SolObject, args: list[SolObject]) -> SolObject:
        """Returns true if the receiver and argument are the same object (identity comparison)."""
        _check_arity("Object.equalTo", args, 1)
        return TRUE if receiver is args[0] else FALSE

    @staticmethod
    def identical_to(receiver: SolObject, args: list[SolObject]) -> SolObject:
        """Returns true if the receiver and argument are the same object, false otherwise."""
        _check_arity("Object.identicalTo", args, 1)
        return TRUE if receiver is args[0] else FALSE

    @staticmethod
    def is_nil(receiver: SolObject, args: list[SolObject]) -> SolObject:
        """Returns true if the receiver is nil, false otherwise."""
        _check_arity("Object.isNil", args, 0)
        return TRUE if receiver is NIL else FALSE

    @staticmethod
    def as_string(receiver: SolObject, args: list[SolObject]) -> SolObject:
        """Returns a string representation of the receiver."""
        _check_arity("Object.asString", args, 0)
        return SolObject(sol_class=STRING_CLASS, value="")

    @staticmethod
    def is_boolean(receiver: SolObject, _args: list[SolObject]) -> SolObject:
        """Returns true if the receiver is either true or false, false otherwise."""
        return (
            TRUE
            if (_is_instance_of(receiver, TRUE_CLASS) or _is_instance_of(receiver, FALSE_CLASS))
            else FALSE
        )

    @staticmethod
    def is_number(receiver: SolObject, _args: list[SolObject]) -> SolObject:
        """Returns true if the receiver is an Integer, false otherwise."""
        return TRUE if _is_instance_of(receiver, INTEGER_CLASS) else FALSE

    @staticmethod
    def is_string(receiver: SolObject, _args: list[SolObject]) -> SolObject:
        """Returns true if the receiver is a string, false otherwise."""
        return TRUE if _is_instance_of(receiver, STRING_CLASS) else FALSE

    @staticmethod
    def is_block(receiver: SolObject, _args: list[SolObject]) -> SolObject:
        """Returns true if the receiver is a block, false otherwise."""
        return TRUE if _is_instance_of(receiver, BLOCK_CLASS) else FALSE

    @staticmethod
    def not_nil(receiver: SolObject, _args: list[SolObject]) -> SolObject:
        """Returns true if the receiver is not nil, false if it is nil."""
        return FALSE if receiver is NIL else TRUE

    @staticmethod
    def yourself(receiver: SolObject, _args: list[SolObject]) -> SolObject:
        """Returns the receiver itself. (Useful for chaining messages to the same object.)"""
        return receiver


class TrueMethods:
    """Static namespace for built-in SOL True singleton methods."""

    @staticmethod
    def not_(_receiver: SolObject, _args: list[SolObject]) -> SolObject:
        """Returns the boolean negation of True, which is False."""
        return FALSE

    @staticmethod
    def as_string(_receiver: SolObject, _args: list[SolObject]) -> SolObject:
        """Returns the string "true" for the True object."""
        return SolObject(sol_class=STRING_CLASS, value="true")


class FalseMethods:
    """Static namespace for built-in SOL False singleton methods."""

    @staticmethod
    def not_(_receiver: SolObject, _args: list[SolObject]) -> SolObject:
        """Returns the boolean negation of False, which is True."""
        return TRUE

    @staticmethod
    def as_string(_receiver: SolObject, _args: list[SolObject]) -> SolObject:
        """Returns the string "false" for the False object."""
        return SolObject(sol_class=STRING_CLASS, value="false")


INTEGER_CLASS.methods["plus:"] = IntegerMethods.plus
INTEGER_CLASS.methods["minus:"] = IntegerMethods.minus
INTEGER_CLASS.methods["multiplyBy:"] = IntegerMethods.multiply
INTEGER_CLASS.methods["divBy:"] = IntegerMethods.div
INTEGER_CLASS.methods["greaterThan:"] = IntegerMethods.greater_than
INTEGER_CLASS.methods["equalTo:"] = IntegerMethods.equal_to
INTEGER_CLASS.methods["asString"] = IntegerMethods.as_string
INTEGER_CLASS.methods["asInteger"] = IntegerMethods.as_integer

STRING_CLASS.methods["print"] = StringMethods.print
STRING_CLASS.methods["equalTo:"] = StringMethods.equal_to
STRING_CLASS.methods["asInteger"] = StringMethods.as_integer
STRING_CLASS.methods["asString"] = StringMethods.as_string
STRING_CLASS.methods["concatenateWith:"] = StringMethods.concatenate_with
STRING_CLASS.methods["length"] = StringMethods.length
STRING_CLASS.methods["startsWith:endsBefore:"] = StringMethods.starts_with_ends_before

NIL_CLASS.methods["asString"] = NilMethods.as_string

OBJECT_CLASS.methods["equalTo:"] = ObjectMethods.equal_to
OBJECT_CLASS.methods["identicalTo:"] = ObjectMethods.identical_to
OBJECT_CLASS.methods["isNil"] = ObjectMethods.is_nil
OBJECT_CLASS.methods["asString"] = ObjectMethods.as_string
OBJECT_CLASS.methods["isBoolean"] = ObjectMethods.is_boolean
OBJECT_CLASS.methods["isNumber"] = ObjectMethods.is_number
OBJECT_CLASS.methods["isString"] = ObjectMethods.is_string
OBJECT_CLASS.methods["isBlock"] = ObjectMethods.is_block
OBJECT_CLASS.methods["notNil"] = ObjectMethods.not_nil
OBJECT_CLASS.methods["yourself"] = ObjectMethods.yourself

TRUE_CLASS.methods["not"] = TrueMethods.not_
TRUE_CLASS.methods["asString"] = TrueMethods.as_string

FALSE_CLASS.methods["not"] = FalseMethods.not_
FALSE_CLASS.methods["asString"] = FalseMethods.as_string
