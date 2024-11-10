#!/bin/bash

# Run isort to sort imports
isort .

# Run ruff to format code
ruff check --fix .
