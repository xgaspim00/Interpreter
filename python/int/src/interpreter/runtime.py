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
    Represents a runtime object in the SOL language.

    Every value in SOL is a SolObject. The `sol_class` field points to its class.
    The `value` field holds a primitive for built-in types (int for Integer, str for String,
    SolClass for class objects, BlockValue for blocks) and is None for regular instances.
    The `attributes` dict holds dynamically assigned instance attributes.
    """

    sol_class: SolClass
    attributes: dict[str, SolObject]
    value: int | str | SolClass | BlockValue | None

    def __init__(
        self, sol_class: SolClass, value: int | str | SolClass | BlockValue | None = None
    ) -> None:
        self.sol_class = sol_class
        self.attributes = {}
        self.value = value


class SolClass:
    """
    Represents a class in the SOL language.

    Holds the class name, a reference to its superclass (None only for Object),
    and a dictionary of methods keyed by their selector strings.
    """

    name: str
    superclass: SolClass | None
    methods: dict[str, Callable[..., SolObject]]

    def __init__(self, name: str, superclass: SolClass | None) -> None:
        self.name = name
        self.superclass = superclass
        self.methods = {}

    def lookup_method(self, selector: str) -> Callable[..., SolObject] | None:
        """Looks up a method by selector in this class and its superclasses.

        Returns None if the method is not found anywhere in the inheritance chain.
        """
        if selector in self.methods:
            return self.methods[selector]
        if self.superclass is not None:
            return self.superclass.lookup_method(selector)
        return None


class Environment:
    """
    Represents a lexical scope as a linked list of variable dictionaries.

    Each scope holds its own variables and a pointer to the enclosing (parent) scope.
    Variable lookup and assignment walk the chain upward, enabling closures to correctly
    read and mutate variables from outer scopes without accidentally shadowing them.
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
        """Resolves and returns the variables value"""
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

    block_model: object  # Typed as object to avoid circular imports with the AST module
    closure: Environment
    self_obj: SolObject
    defining_class: SolClass
