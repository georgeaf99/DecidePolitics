# PolitiHack
A chat bot that keeps you connected to important political decisions


## Development

Setup:

1. Acquire appropriate `config.json` file
2. `source setup.sh`

How to run static analysis: `pylint -E $(find . -type f -name "*.py")`

Basic Style Guide:

1. Use `import <full namespace module name> as <module name>` all module imports
2. Use `from <full namespace module name> import <class>` for importing classes from other modules
3. Do not import functions or variables from other modules, use `<module name>.(var|func)` instead
