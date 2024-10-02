import abc
import collections
import enum
import pathlib
import random
import string
from typing import Any, ClassVar


class GameState(enum.Enum):
    GUESSING = 1
    SUCCEEDED = 2
    FAILED = 3


class GuessLetterState(enum.Enum):
    CORRECT = 1
    ELSEWHERE = 2
    INCORRECT = 3


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

    def __init__(
        self,
        dictionary_file_path: pathlib.Path,
        guess_limit: int,
        word_length: int | None = None,
    ) -> None:
        super().__init__()

        self.guess_limit = guess_limit
        self.word_length = word_length

        self.word_dictionary = self._load_word_dictionary(
            dictionary_file_path, word_length=word_length
        )
        self.target = self._select_target()

        self.guesses: list[Guess] = []
        self.game_state = GameState.GUESSING

    def _load_word_dictionary(
        self, dictionary_file_path: pathlib.Path, word_length: int | None = None
    ) -> set[str]:
        """
        Loads the dictionary of words from the given file. The words in the file should
        be one per line. Raises InvalidDictionaryFileError if any word does not match
        the alphabet.
        """
        with dictionary_file_path.open() as dictionary_file:
            all_words = [line_ for line in dictionary_file if (line_ := line.strip())]
            dictionary = {
                word
                for word in all_words
                if word_length is None or len(word) == word_length
            }

        if not dictionary:
            raise InvalidDictionaryFileError("Empty dictionary file")

        invalid = [w for w in dictionary if not self.is_word_in_alphabet(w)]
        if invalid:
            raise InvalidDictionaryFileError(f"Invalid words: {invalid}")

        return dictionary

    def _select_target(self) -> str:
        """
        Chooses a target word, which the user must try to guess, randomly from the word
        dictionary.
        """
        return random.choice(list(self.word_dictionary))  # noqa: S311

    def guess_word(self, guess_word: str) -> bool:
        if self.game_state != GameState.GUESSING:
            raise GameAlreadyFinishedError()

        if guess_word not in self.word_dictionary:
            raise InvalidGuessWordError(guess_word)

        self.guesses.append(Guess(guess_word, self.target))

        if guess_word == self.target:
            self.game_state = GameState.SUCCEEDED
            return True
        elif len(self.guesses) == self.guess_limit:
            self.game_state = GameState.FAILED
            return True
        else:
            return False


class Guess:
    def __init__(self, guess_word: str, target_word: str) -> None:
        self.target_word = target_word
        self.guess_word = guess_word
        self.guess_letter_states = self._get_guess_letter_states(
            guess_word, target_word
        )

    def __repr__(self) -> str:
        return (
            f"{type(self).__qualname__}(guess_word={self.guess_word!r}, "
            f"target_word={self.target_word!r})"
        )

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Guess):
            return (
                self.guess_word == other.guess_word
                and self.target_word == other.target_word
                and self.guess_letter_states == other.guess_letter_states
            )
        return NotImplemented

    @staticmethod
    def _get_guess_letter_states(
        guess_word: str, target_word: str
    ) -> list[tuple[str, GuessLetterState]]:
        target_letter_counter = collections.Counter(target_word)
        guess_letter_states = [(c, GuessLetterState.INCORRECT) for c in guess_word]

        # First mark the correct guesses
        for i, c in enumerate(guess_word):
            if len(target_word) > i and target_word[i] == c:
                guess_letter_states[i] = (c, GuessLetterState.CORRECT)
                target_letter_counter[c] -= 1

        # Now look for elsewhere guesses, including double letters
        for i, c in enumerate(guess_word):
            # Skip if already marked correct
            if guess_letter_states[i][1] == GuessLetterState.CORRECT:
                continue

            if c in target_letter_counter and target_letter_counter[c] > 0:
                guess_letter_states[i] = (c, GuessLetterState.ELSEWHERE)
                target_letter_counter[c] -= 1

        return guess_letter_states


class InvalidDictionaryFileError(Exception):
    pass


class InvalidGuessWordError(Exception):
    pass


class GameAlreadyFinishedError(Exception):
    pass
