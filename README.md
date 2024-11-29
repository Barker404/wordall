# wordall

Wordall is intended to be a flexible Python-based implementation of word-guessing games
such as Wordle and Quordle. It should be possible to implement different games and run
them within the same framework and text-based user interface, and to configure games
with different word lengths, guess numbers, etc.

The intention of this project is primarily to practice and learn more about python
packaging and development tools - the wordle game is a fun vehicle for that. The
text-based user interface is also an interesting new concept for me.

## Usage

### Install
From the repo root:
```
pip install .
```
Package is not yet published to pypi.

### Run
To run the textual user interface from an environment with the package installed:
```
wordall
```
Note that game choice and settings are currently hard coded in src/wordall/tui/app.py

## Development
See [CONTRIBUTING.md](./CONTRIBUTING.md) for development documentation.

## License
Wordall uses the MIT License, see [LICENSE](./LICENSE).

SCOWL is used for the default word list and has its own license. See
src/wordall/resources/scowl-2020.12.07/Copyright if downloaded within the source files
or wordall/resources/scowl-2020.12.07/Copyright within the package wheel for SCOWL's
license. More information about SCOWL at http://wordlist.aspell.net/.
