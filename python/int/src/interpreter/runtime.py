"""
Runtime structures for the SOL interpreter.

Author: Marek Gašpierik (xgaspim00)

This module defines the core internal representations of SOL's object-oriented
concepts: instances (SolObject), classes (SolClass), lexical scopes (Environment),
and closures (BlockValue).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError


class SolObject:
    """
    A class representing an object in the SOL language.
    """

    sol_class: SolClass
    attributes: dict[str, SolObject]
    value: int | str | SolClass | BlockValue | None

    # Initialize a SOL object with its class, an optional value, and an empty attribute dictionary.
    def __init__(
        self, sol_class: SolClass, value: int | str | SolClass | BlockValue | None = None
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

    # Initialize a SOL class with its name, optional superclass, and an empty method dictionary.
    def __init__(self, name: str, superclass: SolClass | None) -> None:
        self.name = name
        self.superclass = superclass
        self.methods = {}

    def lookup_method(self, selector: str) -> Callable[..., SolObject] | None:
        """Looks up a method by selector in this class and its superclasses."""
        if selector in self.methods:
            return self.methods[selector]
        if self.superclass is not None:
            return self.superclass.lookup_method(selector)
        return None


class Environment:
    """
    A class representing an environment in the SOL language.
    """

    variables: dict[str, SolObject]
    parent: Environment | None

    # Initialize an environment with an optional parent environment
    # and an empty variable dictionary.
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
        Gets the value of a variable by name from the current scope or any parent scope.
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


@dataclass
class BlockValue:
    """
    Represents a block closure — the AST node together with its captured execution context.
    """

    block_model: object
    closure: Environment
    self_obj: SolObject
    defining_class: SolClass
