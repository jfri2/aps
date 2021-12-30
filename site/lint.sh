#!/bin/sh
pylint --rcfile .pylintrc $(find . -name "*.py" | xargs)
