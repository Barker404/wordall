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
To create a non-dev environment from frozen requirements:
```
./create_venv.sh
```
To create a dev environment from frozen requirements:
```
./create_venv.sh -d
```

### Re-compile requirements.txt
For new deps only:
```
./pip_compile.sh
```
To upgrade all:
```
./pip_compile.sh -u
```
