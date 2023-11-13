
### LANPONG

< Description >

### Dev:

# Setting up your own virtual environment

Run `make virtualenv` to create a virtual environment.
then activate it with `source .venv/bin/activate`.

# Install the project in develop mode

Run `make install` to install the project in develop mode.

# Install pre-commit hooks

Run `poetry run pre-commit install` to install the pre-commit hooks


## Linter/Formatting

# Format the code

Run `make fmt` to format the code.

# Run the linter

Run `make lint` to run the linter.


# Makefile utilities

This project comes with a `Makefile` that contains a number of useful utility.

```bash
❯ make
Usage: make <target>

Targets:
help:             ## Show the help.
install:          ## Install the project in dev mode.
fmt:              ## Format code using black & isort.
lint:             ## Run pep8, black, mypy linters.
test: lint        ## Run tests and generate coverage report.
watch:            ## Run tests on every change.
clean:            ## Clean unused files.
virtualenv:       ## Create a virtual environment.
release:          ## Create a new tag for release.
```
## Usage

```bash
$ python -m lanpong
#or
$ lanpong
```
