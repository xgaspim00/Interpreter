"""
Runtime structures for the interpreter, including classes for objects, classes, and environments.
"""

from __future__ import annotations

from collections.abc import Callable

from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError


class SolObject:
    """
    A class representing an object in the SOL language.
    """

    sol_class: SolClass
    attributes: dict[str, SolObject]
    value: int | str | SolClass | tuple[object, ...] | None

    def __init__(
        self, sol_class: SolClass, value: int | str | SolClass | tuple[object, ...] | None = None
    ) -> None:
        self.sol_class = sol_class
        self.attributes = {}
        self.value = value


class SolClass:
    """
    A class representing a class in the SOL language.
    """

    name: str
    superclass: SolClass | None
    methods: dict[str, Callable[..., SolObject]]

    def __init__(self, name: str, superclass: SolClass | None) -> None:
        self.name = name
        self.superclass = superclass
        self.methods = {}


class Environment:
    """
    A class representing an environment (scope) in the SOL language.
    """

    variables: dict[str, SolObject]
    parent: Environment | None

    def __init__(self, parent: Environment | None = None) -> None:
        self.variables = {}
        self.parent = parent

    def has(self, name: str) -> bool:
        """
        Checks if a variable with the given name exists in the current scope or any parent scope.
        """
        if name in self.variables:
            return True
        if self.parent is not None:
            return self.parent.has(name)
        return False

    def get(self, name: str) -> SolObject:
        """
        Looks up a variable by name, searching in the current scope and parent scopes.
        """
        if name in self.variables:
            return self.variables[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise InterpreterError(
            error_code=ErrorCode.SEM_UNDEF, message=f"Undefined variable: {name}"
        )

    def set(self, name: str, value: SolObject) -> None:
        """
        Sets a variable to a value.
        If the variable already exists in the current scope, it is updated.
        """
        if name in self.variables:
            self.variables[name] = value
        elif self.parent is not None and self.parent.has(name):
            self.parent.set(name, value)
        else:
            self.variables[name] = value
