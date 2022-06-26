#!/bin/bash

mkdir -p /workspace/.venv
mkdir -p /workspace/input
mkdir -p /workspace/output

cd /workspace
# ImportError回避のため
unset PYTHONPATH
# パッケージをvenvへinstall
poetry install --no-root
