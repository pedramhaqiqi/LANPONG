
### LANPONG

< Description >

### Dev:

## Setting up your own virtual environment

Run `make virtualenv` to create a virtual environment.
then activate it with `source .venv/bin/activate`.

## Install the project in develop mode

Run `make install` to install the project in develop mode.

## Run the tests to ensure everything is working

Run `make test` to run the tests.

## Create a new branch to work on your contribution

Run `git checkout -b my_contribution`

## Make your changes

Edit the files using your preferred editor. (we recommend VIM or VSCode)

## Format the code

Run `make fmt` to format the code.

## Run the linter

Run `make lint` to run the linter.

## Test your changes

Run `make test` to run the tests.

## Makefile utilities

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
---
# lanpong

[![codecov](https://codecov.io/gh/pedramhaqiqi/LANPONG/branch/main/graph/badge.svg?token=LANPONG_token_here)](https://codecov.io/gh/pedramhaqiqi/LANPONG)
[![CI](https://github.com/pedramhaqiqi/LANPONG/actions/workflows/main.yml/badge.svg)](https://github.com/pedramhaqiqi/LANPONG/actions/workflows/main.yml)

Awesome lanpong created by pedramhaqiqi


## Usage

```bash
$ python -m lanpong
#or
$ lanpong
```


