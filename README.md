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

## GitHub Composite Action

A GitHub composite action is available to generate diffs between header files using the cheader2json package. This action can be reused in other repositories to automate the process of generating diffs.

### Inputs

- `pypi-version` (optional): The published PyPI version number to use. If not provided, the latest published version will be used. If set to a commit hash or a string such as `main`, the corresponding branch of the cheader2json repository will be used.
- `repository-url` (required): The URL of the Git repository to generate the diff for.
- `old-version` (optional): The specific old version number to generate the diff for.
- `new-version` (optional): The specific new version number to generate the diff for.
- `version-constraint` (optional): A custom version constraint pattern using regular expressions.
- `header-paths` (required): A path or regex within the source code checkouts to get the header files that should be converted to JSON.

### Outputs

- `diff-output`: The results of the diff for use by other steps in a larger GitHub Actions workflow.

### Example Generate Diff Step

```yaml
- name: Generate Diff
  uses: GMLC-TDC/cheader2json/.github/actions/generate-diff
  with:
    pypi-version: 'latest'
    repository-url: 'https://github.com/GMLC-TDC/HELICS.git'
    old-version: 'v3.0.0'
    new-version: 'v3.1.0'
    version-constraint: '^v3.*'
    header-paths: 'include/**/*.h'
```
