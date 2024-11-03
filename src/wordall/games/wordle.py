from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pathlib

from wordall import game


class WordleGame(game.SingleWordleLikeBaseGame):
    """
    The logic for a classic wordle game, in which a single word is being guessed.
    """

    def __init__(
        self,
        dictionary_file_path: pathlib.Path,
        guess_limit: int | None = None,
        target_word_length: int | None = None,
    ) -> None:
        super().__init__(guess_limit)

        self.word_dictionary = self._load_word_dictionary(
            dictionary_file_path, word_length=target_word_length
        )
        self.target = self._select_target()
        if target_word_length:
            assert len(self.target) == target_word_length

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

    def is_valid_word(self, word: str) -> bool:
        return word in self.word_dictionary and len(word) == len(self.target)


class InvalidDictionaryFileError(Exception):
    pass
