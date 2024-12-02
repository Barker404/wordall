import abc
import enum
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
        word_filter_function: collections_abc.Callable[[str], bool] = lambda _: True,
    ) -> set[str]:
        """
        Returns the word dictionary. If word_length is supplied, limits loaded words to
        those with exactly that length. If word_filter_function is supplied, only words
        which it returns true for are kept. Raises NoWordsFoundError if no words would
        be returned.
        """
        raise NotImplementedError()


class SimpleFileLoader(WordDictionaryLoader):
    """
    Loads the dictionary of words from the given file. The words in the file are
    expected to be one per line.
    """

    def __init__(
        self, dictionary_file_path: pathlib.Path, encoding: str | None = None
    ) -> None:
        self.dictionary_file_path = dictionary_file_path
        self.encoding = encoding

    def get_word_dictionary(
        self,
        word_length: int | None = None,
        word_filter_function: collections_abc.Callable[[str], bool] = lambda _: True,
    ) -> set[str]:
        word_dictionary = _read_word_dictionary_file(
            self.dictionary_file_path,
            word_length=word_length,
            word_filter_function=word_filter_function,
            encoding=self.encoding,
        )

        if not word_dictionary:
            raise NoWordsFoundError("No words loaded")

        return word_dictionary


class MultipleFileLoader(WordDictionaryLoader):
    """
    Loads the dictionary of words from the union of the given files. The words in the
    file are expected to be one per line.
    """

    def __init__(
        self, dictionary_file_paths: list[pathlib.Path], encoding: str | None = None
    ) -> None:
        self.dictionary_file_paths = dictionary_file_paths
        self.encoding = encoding

    def get_word_dictionary(
        self,
        word_length: int | None = None,
        word_filter_function: collections_abc.Callable[[str], bool] = lambda _: True,
    ) -> set[str]:
        word_dictionary: set[str] = set()

        if self.dictionary_file_paths:
            word_dictionary = set.union(
                *(
                    _read_word_dictionary_file(
                        dictionary_file_path,
                        word_length=word_length,
                        word_filter_function=word_filter_function,
                        encoding=self.encoding,
                    )
                    for dictionary_file_path in self.dictionary_file_paths
                )
            )

        if not word_dictionary:
            raise NoWordsFoundError("No words loaded")

        return word_dictionary


class ScowlLanguageCategory(enum.Enum):
    AMERICAN = 1
    AUSTRALIAN = 2
    BRITISH = 3
    CANADIAN = 4


class ScowlWordSubcategory(enum.Enum):
    WORDS = 1
    ABBREVIATIONS = 2
    CONTRACTIONS = 3
    PROPER_NAMES = 4
    UPPER = 5


class ScowlWordListLoader(MultipleFileLoader):
    """
    Loads the dictionary of words from the SCOWL word list based on options provided.
    """

    COMMON_LANGUAGE_PREFIX = "english"
    MAX_POSSIBLE_VARIANT = 3
    MAX_POSSIBLE_SIZE = 100

    def __init__(  # noqa: PLR0913
        self,
        scowl_final_directory_path: pathlib.Path,
        max_size: int,
        language_category: ScowlLanguageCategory = ScowlLanguageCategory.BRITISH,
        max_variants: int = 1,
        included_subcategories: list[ScowlWordSubcategory] | None = None,
        encoding: str | None = "iso8859-1",  # Encoding used by SCOWL
    ) -> None:
        if not 0 < max_size <= self.MAX_POSSIBLE_SIZE:
            raise ValueError(f"Max size must be between 1 and {self.MAX_POSSIBLE_SIZE}")
        if not 0 <= max_variants <= self.MAX_POSSIBLE_VARIANT:
            raise ValueError(
                f"Max variant must be between 0 and {self.MAX_POSSIBLE_VARIANT}"
            )

        if included_subcategories is None:
            included_subcategories = [ScowlWordSubcategory.WORDS]

        dictionary_file_paths = []

        for language_category_or_none in [None, language_category]:
            for variant_number in range(max_variants + 1):
                category_name = self._get_category_name(
                    language_category_or_none, variant_number
                )

                for subcategory in included_subcategories:
                    dictionary_file_paths.extend(
                        self._get_matching_files(
                            scowl_final_directory_path,
                            category_name,
                            subcategory.name.lower().replace("_", "-"),
                            max_size,
                        )
                    )

        super().__init__(dictionary_file_paths, encoding=encoding)

    @classmethod
    def _get_category_name(
        cls, language_category: ScowlLanguageCategory | None, variant_number: int
    ) -> str:
        if language_category is None:
            language_category_string = cls.COMMON_LANGUAGE_PREFIX
        else:
            language_category_string = language_category.name.lower()

        if variant_number == 0:
            return language_category_string
        elif language_category == ScowlLanguageCategory.AMERICAN:
            return f"variant_{variant_number}"
        else:
            return f"{language_category_string}_variant_{variant_number}"

    @classmethod
    def _get_matching_files(
        cls,
        scowl_final_directory_path: pathlib.Path,
        category_name: str,
        sub_category_name: str,
        max_size: int,
    ) -> list[pathlib.Path]:
        glob_results = scowl_final_directory_path.glob(
            f"{category_name}-{sub_category_name}.*"
        )
        return [
            p
            for p in glob_results
            if p.is_file() and cls._get_word_list_size(p) <= max_size
        ]

    @staticmethod
    def _get_word_list_size(scowl_word_list_path: pathlib.Path) -> int:
        return int(scowl_word_list_path.suffix[1:])


class NoWordsFoundError(Exception):
    pass


def _read_word_dictionary_file(
    dictionary_file_path: pathlib.Path,
    word_length: int | None = None,
    word_filter_function: collections_abc.Callable[[str], bool] = lambda _: True,
    encoding: str | None = None,
) -> set[str]:
    with dictionary_file_path.open(encoding=encoding) as dictionary_file:
        all_words = [line_ for line in dictionary_file if (line_ := line.strip())]

    return {
        word
        for word in all_words
        if (word_length is None or len(word) == word_length)
        and word_filter_function(word)
    }
