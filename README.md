# wordall

Wordall is intended to be a flexible Python-based implementation of word-guessing games
such as Wordle and Quordle. It should be possible to implement different games and run
them within the same framework and text-based user interface, and to configure games
with different word lengths, guess numbers, etc.

The intention of this project is primarily to practice and learn more about python
packaging and development tools - the wordle game is a fun vehicle for that. The
text-based user interface is also an interesting new concept for me.

## Development setup
All examples for ubuntu

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
Creating an environment using frozen requirements (requirements.txt) is only really
useful during development or testing when wanting to avoid possible errors due to new
dependency versions. Otherwise, the package can be installed directly in a fresh
environment and dependencies will be pulled in automatically.

To create an environment without dev dependencies from frozen requirements:
```
./create_venv.sh
```
To create an environment with dev dependencies from frozen requirements:
```
./create_venv.sh -d
```

### Re-compile requirements.txt
For new dependencies only:
```
./pip_compile.sh
```
To upgrade all:
```
./pip_compile.sh -u
```

### Build package
After activating an environment (to get `build`):
```
python -m build
```

### Run tests
After activating an environment with dev dependencies:
```
pytest --cov-report term-missing --cov=src tests/
```

### Formatting, linting, and type-checking
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
