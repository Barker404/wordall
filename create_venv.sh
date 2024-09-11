#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

requirements="${SCRIPT_DIR}/requirements.txt"
usage="Usage: $0 [-d] [-h]"

while getopts "dh" option; do
    case "${option}" in
        d)
            requirements="${SCRIPT_DIR}/requirements-dev.txt"
            ;;
        h)
            echo "${usage}"
            exit;;
        *)
            exit 1;;
   esac
done

if [[ "$PYENV_VERSION" = "wordall" ]]; then
    echo "ERROR: Deactivate the wordall pyenv virtualenv first"
    exit 1
fi

# Could avoid this and call activate script directly from virtualenv later, but then
# shims for newly installed scripts wouldn't be created automatically
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

pyenv virtualenv-delete -f wordall
pyenv virtualenv wordall

pyenv activate wordall
pip install -r "${requirements}"

echo
echo 'Activate new virtualenv with:'
echo '`pyenv activate wordall`'
