#!/bin/sh
export PYTHONPATH=.; pylint -E --rcfile .pylintrc $(find . -name "*.py" | xargs)
