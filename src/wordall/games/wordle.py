from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pathlib

from wordall import game


class WordleGame(game.Game):
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

        self.guesses: list[game.Guess] = []
        self.alphabet_states = {
            c: game.AlphabetLetterState.NOT_GUESSED for c in self.ALPHABET
        }
        self.game_state = game.GameState.GUESSING

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
        if self.game_state != game.GameState.GUESSING:
            raise game.GameAlreadyFinishedError()

        if not self.is_valid_word(guess_word):
            raise game.InvalidGuessWordError(guess_word)

        guess = game.Guess(guess_word, self.target)
        self.guesses.append(guess)
        self._update_alphabet_states(guess)

        if guess_word == self.target:
            self.game_state = game.GameState.SUCCEEDED
            return True
        elif len(self.guesses) == self.guess_limit:
            self.game_state = game.GameState.FAILED
            return True
        else:
            return False

    def _update_alphabet_states(self, guess: game.Guess) -> None:
        """
        Updates game alphabet states as necessary based on the guess.

        All letters start NOT_GUESSED. They can transition to FOUND if guessed
        correctly anywhere (even if more exist) or UNUSED if guessed and not present in
        the target. They can also transition to FOUND_ELSEWHERE is guessed in the wrong
        position. FOUND_ELSEWHERE words can later transition to FOUND.
        """
        for c, state in guess.guess_letter_states:
            if state == game.GuessLetterState.CORRECT:
                # Transition to FOUND from any state. Could even transition from UNUSED
                # if the letter was already guessed incorrectly in this word.
                self.alphabet_states[c] = game.AlphabetLetterState.FOUND
            elif state == game.GuessLetterState.ELSEWHERE:
                if self.alphabet_states[c] != game.AlphabetLetterState.FOUND:
                    # Transition to FOUND_ELSEWHERE from any state except FOUND.
                    # In theory it shouldn't be possible to transition from UNUSED,
                    # because ELSEWHERE should always come before INCORRECT on the same
                    # letter.
                    assert self.alphabet_states[c] != game.AlphabetLetterState.UNUSED
                    self.alphabet_states[c] = game.AlphabetLetterState.FOUND_ELSEWHERE
            else:
                assert state == game.GuessLetterState.INCORRECT
                if self.alphabet_states[c] == game.AlphabetLetterState.NOT_GUESSED:
                    # Transition from NOT_GUESSED to UNUSED. A guess letter could be
                    # INCORRECT without the alphabet letter being UNUSED if the letter
                    # is in the guess word multiple times. If the alphabet letter is
                    # still UNUSED by the end of the update, it really is UNUSED.
                    self.alphabet_states[c] = game.AlphabetLetterState.UNUSED

    def is_valid_word(self, word: str) -> bool:
        return word in self.word_dictionary and len(word) == len(self.target)

    @property
    def max_guess_word_length(self) -> int | None:
        return len(self.target)


class InvalidDictionaryFileError(Exception):
    pass
