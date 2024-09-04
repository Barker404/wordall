import abc
import random
import string


class Game(abc.ABC):
    """
    Abstract base class for word-guessing game logic. Does not handle any user
    interaction. In general, will accept guesses until the correct word(s) is found, at
    which point the game ends.
    """

    @property
    @abc.abstractmethod
    def ALPHABET(self) -> str:
        """
        The alphabet that target and guess words are made up of, as a single string.
        """
        pass

    @abc.abstractmethod
    def guess_word(self, guess_word: str) -> bool:
        """
        Args:
            guess_word: A word to be guessed, possibly provided by a user.
        Returns:
            True if the game is "complete", False if the game is not complete. The game
            is complete when the user has guessed the target word or words successfully.
        """
        pass

    @classmethod
    def is_word_in_alphabet(cls, word: str) -> bool:
        """Returns True if the given word is entirely made from the game alphabet."""
        return all(c in cls.ALPHABET for c in word)


class WordleGame(Game):
    """
    The logic for a classic wordle game, in which a single word is being guessed.
    """

    ALPHABET = string.ascii_uppercase

    def __init__(self, word_list_path: str) -> None:
        super().__init__()
        self.word_list = self._load_word_list(word_list_path)
        self.target = self._select_target()
        self.guesses = []

    def _load_word_list(self, word_list_path: str) -> list[str]:
        """
        Loads the words for the given file and returns them as a list. The words in the
        file should be one per line. Raises InvalidWordListWordError if any word does
        not match the alphabet.
        """
        with open(word_list_path) as word_list_file:
            word_list = [w.strip() for w in word_list_file.readlines()]

        invalid = [w for w in word_list if self.is_word_in_alphabet(w)]
        if invalid:
            raise InvalidWordListWordError(invalid)

        return word_list

    def _select_target(self) -> str:
        """
        Chooses a target word, which the user must try to guess, randomly from the word
        list.
        """
        self.target = random.choice(self.word_list)

    def guess_word(self, guess_word: str) -> bool:
        # Returns True if game is over

        if not self.is_word_in_alphabet:
            raise InvalidGuessWord(guess_word)

        self.guesses.append(guess_word)
        return guess_word == self.target


class InvalidWordListWordError(Exception):
    pass


class InvalidGuessWord(Exception):
    pass
