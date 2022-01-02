#!/bin/sh
export PYTHONPATH=.; pylint -j 4 --disable=all --enable=E,W --disable=unspecified-encoding,unused-import,wildcard-import,unused-wildcard-import,broad-except,bare-except --rcfile .pylintrc $(find . -name "*.py" | xargs)
