import abc
import pathlib
from collections import abc as collections_abc


class WordDictionaryLoader(abc.ABC):
    """
    Base class for loading a word dictionary (the set of words to be used in some way in
    a game).
    """

    @abc.abstractmethod
    def get_word_dictionary(
        self,
        word_length: int | None = None,
        word_validator: collections_abc.Callable[[str], bool] | None = None,
    ) -> set[str]:
        """
        Returns the word dictionary. If word_length is supplied, limits loaded words to
        those with exactly that length. If word_validator is supplied, validates all
        loaded word using it and raises InvalidDictionaryWordError if any fail.
        """
        raise NotImplementedError()


class SimpleFileLoader(WordDictionaryLoader):
    """
    Loads the dictionary of words from the given file. The words in the file are
    expected to be one per line. Raises InvalidDictionaryFileError if no words are
    found.
    """

    def __init__(self, dictionary_file_path: pathlib.Path) -> None:
        self.dictionary_file_path = dictionary_file_path

    def get_word_dictionary(
        self,
        word_length: int | None = None,
        word_validator: collections_abc.Callable[[str], bool] | None = None,
    ) -> set[str]:
        with self.dictionary_file_path.open() as dictionary_file:
            all_words = [line_ for line in dictionary_file if (line_ := line.strip())]
            dictionary = {
                word
                for word in all_words
                if word_length is None or len(word) == word_length
            }

        if not dictionary:
            raise InvalidDictionaryFileError("No words loaded")

        if word_validator is not None:
            invalid = [w for w in dictionary if not word_validator(w)]
            if invalid:
                raise InvalidDictionaryWordError(f"Invalid words: {invalid}")

        return dictionary


class InvalidDictionaryWordError(Exception):
    pass


class InvalidDictionaryFileError(Exception):
    pass
