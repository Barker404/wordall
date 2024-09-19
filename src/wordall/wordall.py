import abc
import enum
import pathlib
import random
import string
from typing import ClassVar


class GameState(enum.Enum):
    GUESSING = 1
    SUCCEEDED = 2
    FAILED = 3


class Game(abc.ABC):
    """
    Abstract base class for word-guessing game logic. Does not handle any user
    interaction. In general, will accept guesses until the correct word(s) is found, at
    which point the game ends.
    """

    game_state: GameState

    ALPHABET: ClassVar[str] = string.ascii_uppercase
    """
    The alphabet that target and guess words are made up of, as a single string.
    """

    @abc.abstractmethod
    def guess_word(self, guess_word: str) -> bool:
        """
        Args:
            guess_word: A word to be guessed, possibly provided by a user.
        Returns:
            True if the game is "complete", False if the game is not complete. The game
            is complete when the user has guessed the target word(s) successfully or run
            out of guess attempts.
        """

    @classmethod
    def is_word_in_alphabet(cls, word: str) -> bool:
        """Returns True if the given word is entirely made from the game alphabet."""
        return all(c in cls.ALPHABET for c in word)


class WordleGame(Game):
    """
    The logic for a classic wordle game, in which a single word is being guessed.
    """

    def __init__(self, word_list_path: pathlib.Path, guess_limit: int) -> None:
        super().__init__()
        self.word_list = self._load_word_list(word_list_path)
        self.target = self._select_target()
        self.guesses: list[str] = []
        self.guess_limit = guess_limit
        self.game_state = GameState.GUESSING

    def _load_word_list(self, word_list_path: pathlib.Path) -> list[str]:
        """
        Loads the words for the given file and returns them as a list. The words in the
        file should be one per line. Raises InvalidWordListWordError if any word does
        not match the alphabet.
        """
        with word_list_path.open() as word_list_file:
            word_list = [line.strip() for line in word_list_file]

        if not word_list:
            raise InvalidWordListError("Empty word list")

        invalid = [w for w in word_list if not self.is_word_in_alphabet(w)]
        if invalid:
            raise InvalidWordListError(f"Invalid words: {invalid}")

        return word_list

    def _select_target(self) -> str:
        """
        Chooses a target word, which the user must try to guess, randomly from the word
        list.
        """
        return random.choice(self.word_list)  # noqa: S311

    def guess_word(self, guess_word: str) -> bool:
        if self.game_state != GameState.GUESSING:
            raise GameAlreadyFinishedError()

        if not self.is_word_in_alphabet(guess_word):
            raise InvalidGuessWordError(guess_word)

        self.guesses.append(guess_word)

        if guess_word == self.target:
            self.game_state = GameState.SUCCEEDED
            return True
        elif len(self.guesses) == self.guess_limit:
            self.game_state = GameState.FAILED
            return True
        else:
            return False


class InvalidWordListError(Exception):
    pass


class InvalidGuessWordError(Exception):
    pass


class GameAlreadyFinishedError(Exception):
    pass
