"""
This module contains the main logic of the interpreter.

Author: Ondřej Ondryáš <iondryas@fit.vut.cz>
Author: Marek Gašpierik (xgaspim00) <xgaspim00@stud.fit.vut.cz>
"""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import TextIO

from lxml import etree
from lxml.etree import ParseError
from pydantic import ValidationError

from interpreter.builtins import (
    BLOCK_CLASS,
    FALSE,
    FALSE_CLASS,
    INTEGER_CLASS,
    NIL,
    NIL_CLASS,
    OBJECT_CLASS,
    STRING_CLASS,
    TRUE,
    TRUE_CLASS,
    _is_instance_of,
)
from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError
from interpreter.input_model import Block as Blockmodel
from interpreter.input_model import Expr, Literal, Program
from interpreter.runtime import BlockValue, Environment, SolClass, SolObject

logger = logging.getLogger(__name__)


class Interpreter:
    """
    The main interpreter class, responsible for loading the source file and executing the program.
    """

    def __init__(self) -> None:
        self.current_program: Program | None = None
        self.classes: dict[str, SolClass] = {}
        self.input_io: TextIO | None = None

    def load_program(self, source_file_path: Path) -> None:
        """
        Reads the source SOL-XML file and stores it as the target program for this interpreter.
        If any program was previously loaded, it is replaced by the new one.
        """
        logger.info("Opening source file: %s", source_file_path)
        try:
            xml_tree = etree.parse(source_file_path)
        except ParseError as e:
            raise InterpreterError(
                error_code=ErrorCode.INT_XML, message="Error parsing input XML"
            ) from e
        try:
            self.current_program = Program.from_xml_tree(xml_tree.getroot())  # type: ignore
        except ValidationError as e:
            raise InterpreterError(
                error_code=ErrorCode.INT_STRUCTURE, message="Invalid SOL-XML structure"
            ) from e

    def execute(self, input_io: TextIO) -> None:
        """
        Executes the currently loaded program, using the provided input stream as standard input.
        """
        logger.info("Executing program")

        self.input_io = input_io
        self.classes = {
            "Object": OBJECT_CLASS,
            "Integer": INTEGER_CLASS,
            "String": STRING_CLASS,
            "Nil": NIL_CLASS,
            "Block": BLOCK_CLASS,
            "True": TRUE_CLASS,
            "False": FALSE_CLASS,
        }

        assert self.current_program is not None
        for class_def in self.current_program.classes:
            if class_def.name in self.classes:
                raise InterpreterError(
                    error_code=ErrorCode.SEM_ERROR,
                    message=f"Duplicate class definition: {class_def.name}",
                )
            if self.classes.get(class_def.parent) is None:
                raise InterpreterError(
                    error_code=ErrorCode.SEM_UNDEF,
                    message=f"Undefined parent class: {class_def.parent}",
                )
            self.classes[class_def.name] = SolClass(
                name=class_def.name, superclass=self.classes[class_def.parent]
            )

        for class_def in self.current_program.classes:
            sol_class = self.classes[class_def.name]
            for method_def in class_def.methods:
                if method_def.block.arity != method_def.selector.count(":"):
                    raise InterpreterError(
                        error_code=ErrorCode.SEM_ARITY,
                        message=f"Method {method_def.selector} has incorrect arity",
                    )
                sol_class.methods[method_def.selector] = self._make_method(
                    sol_class, method_def.block
                )

        main_class = self.classes.get("Main")
        if main_class is None or "run" not in self._get_all_methods(main_class):
            raise InterpreterError(
                error_code=ErrorCode.SEM_MAIN,
                message="Main class or run instance method not found",
            )

        self._register_block_methods()
        self._register_conditional_methods()
        self._register_string_methods()
        main_instance = SolObject(sol_class=main_class)
        self._send_message(main_instance, "run", [])

    def _get_all_methods(self, sol_class: SolClass) -> set[str]:
        """
        Returns a set of all method selectors available on the given class,
        including those inherited from superclasses.
        """
        methods: set[str] = set()
        current: SolClass | None = sol_class
        while current is not None:
            methods.update(current.methods.keys())
            current = current.superclass
        return methods

    def _eval_block_arg(self, block_obj: SolObject) -> SolObject:
        """Helper to evaluate a 0-arity block by sending it the 'value' message."""
        return self._send_message(block_obj, "value", [])

    def _handle_instantiation(
        self, target_class: SolClass, selector: str, args: list[SolObject]
    ) -> SolObject | None:
        """Handles 'new' and 'from:' messages sent to class objects."""
        if target_class is NIL_CLASS and selector in ["new", "from:"]:
            return NIL

        if selector == "new":
            if _is_instance_of(SolObject(sol_class=target_class), BLOCK_CLASS):
                # Block new creates an inert empty block;
                # actual blocks are created via block literals.
                dummy_block = Blockmodel(arity=0, parameters=[], assigns=[])
                return self._make_block_object(dummy_block, Environment(), NIL, target_class)

            default_val: int | str | None = None
            if _is_instance_of(SolObject(sol_class=target_class), INTEGER_CLASS):
                default_val = 0
            elif _is_instance_of(SolObject(sol_class=target_class), STRING_CLASS):
                default_val = ""
            return SolObject(sol_class=target_class, value=default_val)

        if selector == "from:" and len(args) == 1:
            source = args[0]
            dummy_target = SolObject(sol_class=target_class)
            if _is_instance_of(dummy_target, INTEGER_CLASS) and not isinstance(source.value, int):
                raise InterpreterError(
                    ErrorCode.INT_INVALID_ARG,
                    message="from: argument missing internal int attribute",
                )
            if _is_instance_of(dummy_target, STRING_CLASS) and not isinstance(source.value, str):
                raise InterpreterError(
                    ErrorCode.INT_INVALID_ARG,
                    message="from: argument missing internal str attribute",
                )

            new_inst = SolObject(sol_class=target_class, value=source.value)
            new_inst.attributes = source.attributes.copy()
            return new_inst

        return None

    def _handle_accessor(
        self, receiver: SolObject, selector: str, args: list[SolObject], search_class: SolClass
    ) -> SolObject | None:
        """Handles fallback to dynamic getters and setters if no method is found."""
        if isinstance(receiver.value, SolClass):
            return None

        if selector.endswith(":") and len(args) == 1:
            attr_name = selector[:-1]
            if search_class.lookup_method(attr_name) is not None:
                raise InterpreterError(
                    error_code=ErrorCode.INT_INST_ATTR,
                    message=f"Cannot create attribute '{attr_name}': collide with existing method",
                )
            receiver.attributes[attr_name] = args[0]
            return receiver

        if ":" not in selector and len(args) == 0 and selector in receiver.attributes:
            return receiver.attributes[selector]

        return None

    def _send_message(
        self,
        receiver: SolObject,
        selector: str,
        args: list[SolObject],
        start_class: SolClass | None = None,
    ) -> SolObject:
        """
        Sends a message to the receiver object,
        invoking the method corresponding to the selector.
        """

        # If the receiver holds a class object, handle class-side messages first.
        if isinstance(receiver.value, SolClass):
            target_class = receiver.value

            # Try to handle constructor messages ('new' or 'from:') sent to the class.
            instantiation_result = self._handle_instantiation(target_class, selector, args)
            if instantiation_result is not None:
                return instantiation_result

            # Look up and invoke a class-side method (e.g. String read).
            found_class_method = target_class.lookup_method(selector)
            if found_class_method is not None:
                return found_class_method(receiver, args)

        # Look up the method in the class hierarchy starting from search_class.
        # When 'super' is used, start_class is set to the superclass of the defining class.
        search_class = start_class if start_class is not None else receiver.sol_class
        found_method = search_class.lookup_method(selector)
        if found_method is not None:
            return found_method(receiver, args)

        # No method found — try to handle the message as a dynamic getter or setter.
        accessor_result = self._handle_accessor(receiver, selector, args, search_class)
        if accessor_result is not None:
            return accessor_result

        # The receiver does not understand the message and has no matching attribute.
        raise InterpreterError(
            error_code=ErrorCode.INT_DNU,
            message=f"{receiver.sol_class.name} does not understand '{selector}'",
        )

    def _eval_expr(
        self, expr: Expr, env: Environment, self_obj: SolObject, defining_class: SolClass
    ) -> SolObject:
        """
        Evaluates an expression in the given environment and returns the resulting object.
        """
        if expr.literal is not None:
            return self._eval_literal(expr.literal)
        if expr.var is not None:
            name = expr.var.name
            if name == "self":
                return self_obj
            if name == "super":
                return self_obj
            if name == "nil":
                return NIL
            if name == "true":
                return TRUE
            if name == "false":
                return FALSE
            return env.get(name)

        if expr.block is not None:
            return self._make_block_object(expr.block, env, self_obj, defining_class)

        if expr.send is not None:
            send = expr.send
            # Check for the keyword "super"
            is_super = send.receiver.var is not None and send.receiver.var.name == "super"
            receiver = self._eval_expr(send.receiver, env, self_obj, defining_class)
            args = [self._eval_expr(a.expr, env, self_obj, defining_class) for a in send.args]
            # If a keyword "super" is used, we need to start the
            # method lookup from the superclass of the defining class.
            start = defining_class.superclass if is_super else None
            return self._send_message(receiver, send.selector, args, start_class=start)

        # If the expression is empty, raise an error.
        raise InterpreterError(
            error_code=ErrorCode.INT_OTHER,
            message="Empty expression cannot be evaluated",
        )

    def _eval_literal(self, literal: Literal) -> SolObject:
        """Evaluates a literal and returns the corresponding SolObject."""
        match literal.class_id:
            case "Integer":
                return SolObject(sol_class=INTEGER_CLASS, value=int(literal.value))
            case "String":
                return SolObject(sol_class=STRING_CLASS, value=literal.value)
            case "Nil":
                return NIL
            case "True":
                return TRUE
            case "False":
                return FALSE
            case "class":
                sol_class = self.classes.get(literal.value)
                # Check if the class exists before trying to create an object for it.
                if sol_class is None:
                    raise InterpreterError(
                        error_code=ErrorCode.SEM_UNDEF,
                        message=f"Undefined class: {literal.value}",
                    )
                return SolObject(sol_class=OBJECT_CLASS, value=sol_class)
            case _:
                # If the literal has an unknown class_id, we raise an error.
                raise InterpreterError(
                    error_code=ErrorCode.INT_OTHER,
                    message=f"Unknown literal class: {literal.class_id}",
                )

    def _make_block_object(
        self,
        block_model: Blockmodel,
        env: Environment,
        self_obj: SolObject,
        defining_class: SolClass,
    ) -> SolObject:
        """
        Creates a SolObject representing a block,
        capturing the given environment and self object.
        """
        obj = SolObject(sol_class=BLOCK_CLASS)
        obj.value = BlockValue(
            block_model=block_model,
            closure=env,
            self_obj=self_obj,
            defining_class=defining_class,
        )
        return obj

    def _exec_block(
        self,
        block_model: Blockmodel,
        closure_env: Environment,
        self_obj: SolObject,
        defining_class: SolClass,
        args: list[SolObject],
    ) -> SolObject:
        """
        Executes the given block of code in the provided environment and returns the result.
        """
        # Arity check
        if len(args) != block_model.arity:
            raise InterpreterError(
                error_code=ErrorCode.INT_DNU,
                message=f"Block expected {block_model.arity} arguments but got {len(args)}",
            )
        # Check for variable name collisions between block parameters and assigned variables.
        param_names = {param.name for param in block_model.parameters}
        for assign in block_model.assigns:
            if assign.target.name in param_names:
                raise InterpreterError(
                    error_code=ErrorCode.SEM_COLLISION, message="Cannot assign to block parameter"
                )
        # New environment for the block execution, with the closure environment as its parent
        env = Environment(parent=closure_env)
        # Bind parameters to arguments in the new environment
        for param, arg in zip(block_model.parameters, args, strict=False):
            env.variables[param.name] = arg
        # Execute the block's statements in order, returning the value of the last expression
        # If no statements were evaluated, result is nil
        result: SolObject = NIL
        for assign in block_model.assigns:
            value = self._eval_expr(assign.expr, env, self_obj, defining_class)
            # Store the result of expression to the variable
            # Exception: if the variable name is "_", we do not store the value
            # in the environment, but we still update the result to the value of the expression.
            if assign.target.name != "_":
                env.set(assign.target.name, value)
            # Update the result to the value of the last assignment expression
            result = value
        # Return the value of the last expression in the block as the result of the block execution
        return result

    def _make_method(self, defining_class: SolClass, block: object) -> Callable[..., SolObject]:
        """
        Creates a callable that executes the given method block
        with the provided receiver and arguments.
        """
        # The block should be a Blockmodel, but we check it at runtime to ensure type safety.
        if not isinstance(block, Blockmodel):
            raise InterpreterError(
                error_code=ErrorCode.INT_OTHER,
                message="Invalid method block",
            )

        # The method function that will be called when the method is invoked.
        def method(receiver: SolObject, args: list[SolObject]) -> SolObject:
            """Executes the method with the provided receiver and arguments."""
            # Methods always start in a fresh scope with no parent — they do not capture
            # any outer variables. Only block literals (closures) capture their enclosing env.
            return self._exec_block(block, Environment(), receiver, defining_class, args)

        return method

    def _register_block_methods(self) -> None:
        """
        Registers the built-in methods for the Block class.
        This should be called after all classes are created but before execution starts.
        """

        def block_value(receiver: SolObject, args: list[SolObject]) -> SolObject:
            """Implements the value, value:, and value:value: methods for the Block class."""
            bv = receiver.value
            # We check the structure of the block object at runtime to ensure type safety.
            if not isinstance(bv, BlockValue):
                raise InterpreterError(
                    error_code=ErrorCode.INT_DNU,
                    message="Invalid block object",
                )
            # Check the types of the components to ensure they are correct.
            if not isinstance(bv.block_model, Blockmodel):
                raise InterpreterError(
                    error_code=ErrorCode.INT_DNU, message="Invalid block model in block object"
                )
            # Execute the block with the provided receiver and arguments,
            # using the captured environment and self object.
            return self._exec_block(
                bv.block_model, bv.closure, bv.self_obj, bv.defining_class, args
            )

        def block_while_true(receiver: SolObject, args: list[SolObject]) -> SolObject:
            """Implements the whileTrue: method for the Block class."""
            last_body_result = NIL
            while True:
                condition = self._send_message(receiver, "value", [])
                if not _is_instance_of(condition, TRUE_CLASS):
                    break
                # Execute the body blocks and update the last_body_result with its result.
                last_body_result = self._send_message(args[0], "value", [])
            return last_body_result

        # Register the methods to the Block class
        BLOCK_CLASS.methods["value"] = block_value
        BLOCK_CLASS.methods["value:"] = block_value
        BLOCK_CLASS.methods["value:value:"] = block_value
        BLOCK_CLASS.methods["whileTrue:"] = block_while_true

    def _register_conditional_methods(self) -> None:
        """
        Registers the built-in methods for True and False conditionals
        (ifTrue:ifFalse:, ifTrue:, ifFalse:, and:, or:) and Integer.timesRepeat:.
        """

        def true_and(receiver: SolObject, args: list[SolObject]) -> SolObject:
            """Implements the and: method for the Boolean class."""
            return self._eval_block_arg(args[0])

        def false_and(receiver: SolObject, args: list[SolObject]) -> SolObject:
            """Implements the and: method for the Boolean class."""
            return FALSE

        def true_or(receiver: SolObject, args: list[SolObject]) -> SolObject:
            """Implements the or: method for the Boolean class."""
            return TRUE

        def false_or(receiver: SolObject, args: list[SolObject]) -> SolObject:
            """Implements the or: method for the Boolean class."""
            return self._eval_block_arg(args[0])

        def true_if(receiver: SolObject, args: list[SolObject]) -> SolObject:
            """Implements True.ifTrue:ifFalse: — evaluates the true branch (first argument)."""
            return self._eval_block_arg(args[0])

        def false_if(receiver: SolObject, args: list[SolObject]) -> SolObject:
            """Implements False.ifTrue:ifFalse: — evaluates the false branch (second argument)."""
            return self._eval_block_arg(args[1])

        def true_if_true(receiver: SolObject, args: list[SolObject]) -> SolObject:
            """Implements the ifTrue: single-branch method — evaluates the block."""
            return self._eval_block_arg(args[0])

        def false_if_false(receiver: SolObject, args: list[SolObject]) -> SolObject:
            """Implements the ifFalse: single-branch method — evaluates the block."""
            return self._eval_block_arg(args[0])

        def integer_times_repeat(receiver: SolObject, args: list[SolObject]) -> SolObject:
            """Implements the timesRepeat: method for the Integer class."""
            if not isinstance(receiver.value, int):
                raise InterpreterError(ErrorCode.INT_OTHER, "Receiver must be an integer")

            result = NIL
            # Execute the block the specified number of times,
            # passing the current iteration index (starting from 1) as an argument.
            for i in range(1, receiver.value + 1):
                sol_i = SolObject(sol_class=INTEGER_CLASS, value=i)
                result = self._send_message(args[0], "value:", [sol_i])
            return result

        # Register the methods to the appropriate classes
        TRUE_CLASS.methods["ifTrue:ifFalse:"] = true_if
        FALSE_CLASS.methods["ifTrue:ifFalse:"] = false_if
        TRUE_CLASS.methods["ifTrue:"] = true_if_true
        FALSE_CLASS.methods["ifFalse:"] = false_if_false
        TRUE_CLASS.methods["and:"] = true_and
        FALSE_CLASS.methods["and:"] = false_and
        TRUE_CLASS.methods["or:"] = true_or
        FALSE_CLASS.methods["or:"] = false_or
        INTEGER_CLASS.methods["timesRepeat:"] = integer_times_repeat

    def _register_string_methods(self) -> None:
        """
        Registers the built-in methods for the String class that require access
        to the interpreter's IO stream.
        """

        def string_read(receiver: SolObject, args: list[SolObject]) -> SolObject:
            """Reads a line of input from the injected input_io stream."""
            if len(args) != 0:
                raise InterpreterError(
                    error_code=ErrorCode.INT_INVALID_ARG,
                    message="String.read expects no arguments",
                )

            # Check that the input stream is initialized before trying to read from it.
            if self.input_io is None:
                raise InterpreterError(
                    error_code=ErrorCode.INT_OTHER, message="Input stream is not initialized"
                )

            try:
                # Read a line from the standard input stream injected by the tester
                line = self.input_io.readline()
                # Check for EOF
                if not line:
                    raise EOFError

                # Store the line in the object without the trailing newline character
                return SolObject(sol_class=STRING_CLASS, value=line.rstrip("\n"))
            except EOFError as e:
                raise InterpreterError(
                    error_code=ErrorCode.INT_OTHER, message="String.read: unexpected EOF"
                ) from e

        STRING_CLASS.methods["read"] = string_read
