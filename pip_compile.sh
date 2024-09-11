#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SCRIPT_NAME=$(basename "$0")

pip_compile_args=()
usage="Usage: $0 [-u] [-h]"

while getopts "uh" option; do
    case "${option}" in
        u)
            pip_compile_args+=(--upgrade)
            ;;
        h)
            echo "${usage}"
            exit;;
        *)
            exit 1;;
   esac
done

export CUSTOM_COMPILE_COMMAND="./${SCRIPT_NAME}"

pip-compile "${pip_compile_args[@]}" --output-file="${SCRIPT_DIR}/requirements.txt" "${SCRIPT_DIR}/pyproject.toml"
pip-compile "${pip_compile_args[@]}" --extra=dev --output-file="${SCRIPT_DIR}/requirements-dev.txt" "${SCRIPT_DIR}/pyproject.toml"
