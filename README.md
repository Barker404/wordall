# wordall

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
pytest tests/
```

### Format and lint
```
ruff format && ruff check
```
To autofix linting errors (where possible):
```
ruff check --fix
```

### Static type check
```
mypy --strict .
```
