#!/bin/bash
cd $(
    cd "$(dirname "$0")"
    pwd
)

pipenv run python ./main.py >>run.log 2>&1
