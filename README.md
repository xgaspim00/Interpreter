# IPP Project: Interpreter and Tester

This repository contains an interpreter and an automated testing tool for a custom programming language designed for the IPP university course.

The project is divided into two main applications:
1. **Interpreter**: Reads, parses, and executes the intermediate representation (XML) of the custom programming language.
2. **Tester**: An automated testing framework designed to validate the functionality of the interpreter against various test suites.

## Author's Contributions

The core logic and functionality that I have implemented are located entirely in the following directories:

* 📁 **[`python/int/src/interpreter/`](python/int/src/interpreter/)**: Contains the complete source code for the Interpreter, implemented in Python.
* 📁 **[`typescript/tester/src/`](typescript/tester/src/)**: Contains the complete source code for the Tester, implemented in TypeScript.
* 📄 **[`Dockerfile`](Dockerfile)**: Configuration file containing the Docker setup for the project.

> **Note:** All other files and directories in this repository (such as `examples/`, `sol2xml/`, bash scripts, and test data) were provided by the course instructors as a template, reference material, or testing environment.

## Components

### 1. Python Interpreter
The interpreter (`python/int/src/interpreter/`) is built with **Python** and is responsible for:
- Loading and validating the XML representation of the custom source code.
- Managing the runtime environment (memory, data types, frames).
- Executing the instructions sequentially and handling runtime errors according to the language specification.

### 2. TypeScript Tester
The testing framework (`typescript/tester/src/`) is built with **TypeScript** and **Node.js**. Its responsibilities include:
- Recursively scanning for test files (`.src`, `.in`, `.out`, etc.).
- Passing the tests to the interpreter.
- Comparing the actual output, standard error, and return codes with the expected results.
- Generating a comprehensive test report.

## Requirements

To run the tools in this project, you will need:
- **Python 3.x** for the interpreter.
- **Node.js** (and optionally `npm`/`yarn`) to compile and run the TypeScript tester.
