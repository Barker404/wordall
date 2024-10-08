from __future__ import annotations

import abc
import collections
import enum
import random
import string
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    import pathlib


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


class WordleGame(Game):
    """
    The logic for a classic wordle game, in which a single word is being guessed.
    """

    def __init__(
        self,
        dictionary_file_path: pathlib.Path,
        guess_limit: int,
        target_word_length: int | None = None,
    ) -> None:
        super().__init__()

        self.guess_limit = guess_limit

        self.word_dictionary = self._load_word_dictionary(
            dictionary_file_path, word_length=target_word_length
        )
        self.target = self._select_target()
        if target_word_length:
            assert len(self.target) == target_word_length

        self.guesses: list[Guess] = []
        self.alphabet_states = {
            c: AlphabetLetterState.NOT_GUESSED for c in self.ALPHABET
        }
        self.game_state = GameState.GUESSING

    def _load_word_dictionary(
        self, dictionary_file_path: pathlib.Path, word_length: int | None = None
    ) -> set[str]:
        """
        Loads the dictionary of words from the given file. The words in the file should
        be one per line. Raises InvalidDictionaryFileError if any word does not match
        the alphabet.
        If word_length is provided, only loads words of that length. This allows
        limiting number of words needed in memory for game where word length is known
        ahead of time.
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

        if not self.is_valid_word(guess_word):
            raise InvalidGuessWordError(guess_word)

        guess = Guess(guess_word, self.target)
        self.guesses.append(guess)
        self._update_alphabet_states(guess)

        if guess_word == self.target:
            self.game_state = GameState.SUCCEEDED
            return True
        elif len(self.guesses) == self.guess_limit:
            self.game_state = GameState.FAILED
            return True
        else:
            return False

    def _update_alphabet_states(self, guess: Guess) -> None:
        """
        Updates game alphabet states as necessary based on the guess.

        All letters start NOT_GUESSED. They can transition to FOUND if guessed
        correctly anywhere (even if more exist) or UNUSED if guessed and not present in
        the target. They can also transition to FOUND_ELSEWHERE is guessed in the wrong
        position. FOUND_ELSEWHERE words can later transition to FOUND.
        """
        for c, state in guess.guess_letter_states:
            if state == GuessLetterState.CORRECT:
                # Transition to FOUND from any state. Could even transition from UNUSED
                # if the letter was already guessed incorrectly in this word.
                self.alphabet_states[c] = AlphabetLetterState.FOUND
            elif state == GuessLetterState.ELSEWHERE:
                if self.alphabet_states[c] != AlphabetLetterState.FOUND:
                    # Transition to FOUND_ELSEWHERE from any state except FOUND.
                    # In theory it shouldn't be possible to transition from UNUSED,
                    # because ELSEWHERE should always come before INCORRECT on the same
                    # letter.
                    assert self.alphabet_states[c] != AlphabetLetterState.UNUSED
                    self.alphabet_states[c] = AlphabetLetterState.FOUND_ELSEWHERE
            else:
                assert state == GuessLetterState.INCORRECT
                if self.alphabet_states[c] == AlphabetLetterState.NOT_GUESSED:
                    # Transition from NOT_GUESSED to UNUSED. A guess letter could be
                    # INCORRECT without the alphabet letter being UNUSED if the letter
                    # is in the guess word multiple times. If the alphabet letter is
                    # still UNUSED by the end of the update, it really is UNUSED.
                    self.alphabet_states[c] = AlphabetLetterState.UNUSED

    def is_valid_word(self, word: str) -> bool:
        return word in self.word_dictionary and len(word) == len(self.target)


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
