from __future__ import annotations

import abc
import collections
import enum
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


class AlphabetLetterState(enum.Enum):
    FOUND = 1
    FOUND_ELSEWHERE = 2
    UNUSED = 3
    NOT_GUESSED = 4


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

    @abc.abstractmethod
    def is_valid_word(self, word: str) -> bool:
        """
        Returns True if the given word is valid for this game i.e. would be accepted
        as a guess.
        """

    @property
    @abc.abstractmethod
    def max_guess_word_length(self) -> int | None:
        """
        Returns the game's maximum length for valid guess inputs, if it has one.
        Otherwise returns None.
        """


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


class InvalidGuessWordError(Exception):
    pass


class GameAlreadyFinishedError(Exception):
    pass
