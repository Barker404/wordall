import random
import string

from wordall import game


class NumberleGame(game.SingleWordleLikeBaseGame):
    ALPHABET = string.digits

    def __init__(
        self,
        guess_limit: int,
        target_word_length: int = 5,
    ) -> None:
        super().__init__(guess_limit)

        self.target = self._select_target(target_word_length)

    def _select_target(self, target_word_length: int) -> str:
        """
        Chooses a target word, which the user must try to guess, randomly.
        """
        number = random.randrange(10**target_word_length)  # noqa: S311
        return str(number).zfill(target_word_length)

    def is_valid_word(self, word: str) -> bool:
        return self.is_word_in_alphabet(word) and len(word) == len(self.target)
