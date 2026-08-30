#!/bin/bash

set -e

source .venv/bin/activate

if [ "$1" = "--benchmark" ]; then
    python -m app.main --benchmark
else
    python -m app.main
fi