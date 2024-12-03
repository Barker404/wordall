from __future__ import annotations

import random

from wordall import game, word_dictionary_loaders


class WordleGame(game.SingleWordleLikeBaseGame):
    """
    The logic for a classic wordle game, in which a single word is being guessed.
    """

    def __init__(
        self,
        word_dictionary_loader: word_dictionary_loaders.WordDictionaryLoader,
        guess_limit: int | None = None,
        target_word_length: int = 5,
    ) -> None:
        super().__init__(guess_limit)

        self.word_dictionary = word_dictionary_loader.get_word_dictionary(
            word_length=target_word_length,
            word_transform_function=str.upper,
            word_filter_function=self.is_word_in_alphabet,
        )
        self.target = self._select_target()
        assert len(self.target) == target_word_length

    def _select_target(self) -> str:
        """
        Chooses a target word, which the user must try to guess, randomly from the word
        dictionary.
        """
        return random.choice(list(self.word_dictionary))  # noqa: S311

    def is_valid_word(self, word: str) -> bool:
        return word in self.word_dictionary and len(word) == len(self.target)
