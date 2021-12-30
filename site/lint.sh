#!/bin/sh
pylint -E --rcfile .pylintrc $(find . -name "*.py" | xargs)
