# Development
All examples for ubuntu

## Dev environment setup

### Install and configure pyenv
Follow instructions from https://github.com/pyenv/pyenv to configure pyenv and
https://github.com/pyenv/pyenv-virtualenv to configure pyenv-virtualenv. Note that the
pyenv automatic installer already installs pyenv-virtualenv, but it still needs to be
configured in the shell.

### Install python version
Install based on current .python-version:
```
pyenv install "$(pyenv version-file-read ./.python-version)"
```

### Set up virtualenv
The `create_venv.sh` simplifies creating a new pyenv environment called `wordall`. It
just installs the latest compatible dependencies (no locking) the same as anybody would
get using `pip install wordall`.

To create an environment without dev dependencies:
```
./create_venv.sh
```
To create an environment with dev dependencies and editable wordall:
```
./create_venv.sh -d
```

## Build package
After activating an environment (to get `build`):
```
python -m build
```

## Run tests
After activating an environment with dev dependencies:
```
pytest
```
Coverage will be shown in output.

## Formatting, linting, and type-checking
Python formatting and linting are done using ruff for python. Shell script formatting
uses shfmt and linting uses shellcheck. Both are managed via pre-commit. Type-checking
is done using mypy, which is installed in the venv (outside of pre-commit's isolated
venv) and run by pre-commit (for reasons see
https://github.com/python/mypy/issues/13916).

Set up pre-commit:
```
pre-commit install
```

Checks will run before commit, and abort commit if any fail or make changes - in which
case the changes will need to be reviewed and git added.

To run ruff lnting manually on all files:
```
pre-commit run ruff --all-files
```
And similar for `ruff-format`, `shfmt` and `shellcheck`.

To run mypy manually on all files:
```
pre-commit run mypy --all-files
```
or
```
mypy --strict .
```

## Testing github workflows
Github workflows can be tested locally with `act` for faster feedback (although there
may be some differences). Requires docker (https://docs.docker.com/engine/install/).

Install act:
```
curl --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

Run workflows for push event:
```
act push
```
Run only one python version:
```
act push --matrix python-version:3.12
```

See also https://nektosact.com/usage/index.html
