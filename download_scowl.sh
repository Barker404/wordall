#!/usr/bin/env bash

set -euo pipefail

usage="Usage: $0 [-f] [-h]"
force=0

while getopts "fh" option; do
    case "${option}" in
    f)
        force=1
        ;;
    h)
        echo "${usage}"
        exit
        ;;
    *)
        echo "${usage}"
        exit 1
        ;;
    esac
done

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
RESOURCES_DIR="${SCRIPT_DIR}/src/wordall/resources"
URL=http://downloads.sourceforge.net/wordlist/scowl-2020.12.07.tar.gz

url_basename=$(basename "${URL}")
url_basename_no_ext=$(basename "${URL}" .tar.gz)
tar_path="${RESOURCES_DIR}/${url_basename}"
untarred_path="${RESOURCES_DIR}/${url_basename_no_ext}"

if [[ -d ${untarred_path} && ${force} -eq 0 ]]; then
    echo "SCOWL already exists; nothing to do"
    exit 0
fi

mkdir -p "${RESOURCES_DIR}"
wget "${URL}" -O "${tar_path}"
rm -r "${untarred_path}" || true # It's fine if the rm fails
tar -xzf "${tar_path}" -C "${RESOURCES_DIR}"
rm "${tar_path}"

echo
echo "Succesfully download SCOWL data to ${untarred_path}"
