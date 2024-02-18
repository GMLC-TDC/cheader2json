# cheader2json

Take one or more c header files as input, and do a JSON dump of a portion of the libclang AST for easier processing by other
tools. This code was originally from the libclang based Python/Matlab binding generator for HELICS, but has been split out
to make it more reusable. Functionality is also provided to do a diff of two JSON files, that can be used to get a quick
overview of what has changed between releases.

## Installation

```shell
pip install cheader2json
```

Recommended: Install in a Python virtual environment.

## Usage

Convert a c header file to a JSON file with a subset of the AST (excluding function bodies) and a JSON file with type information:

```shell
cheader2json convert <HEADER_FILE>
```

Dump a pair of JSON files named `example.ast.json` and `example.types.json` for multiple header files, and ignore `DO_SOMETHING` macro
(the ignore macro option can be given more than once, or IGNORED_MACROS environment variable can be set to a space separated list of
macro names to ignore):

```shell
cheader2json convert <HEADER_FILE1> <HEADER_FILE2> --prefix=example --ignore-macro=DO_SOMETHING
```

Do a diff of two dumped AST JSON files:

```shell
cheader2json diff <JSON_AST_FILE_OLD> <JSON_AST_FILE_NEW>
```
