import pathlib
import string
from typing import Any
from unittest import mock

import pytest
import pytest_mock

from wordall import word_dictionary_loaders


@pytest.fixture
def mock_valid_dictionary_file(
    mocker: pytest_mock.MockerFixture,
) -> tuple[mock.MagicMock, list[str]]:
    return _mock_dictionary_file_helper(
        ["APPLE", "BREAD", "CHIPS", "DONUTS", "EGGS"], mocker
    )


@pytest.fixture
def mock_valid_empty_line_dictionary_file(
    mocker: pytest_mock.MockerFixture,
) -> tuple[mock.MagicMock, list[str]]:
    return _mock_dictionary_file_helper(
        ["", "APPLE", "BREAD", "", "CHIPS", "DONUTS", "EGGS", ""], mocker
    )


@pytest.fixture
def mock_non_alphabet_character_dictionary_file(
    mocker: pytest_mock.MockerFixture,
) -> tuple[mock.MagicMock, list[str]]:
    return _mock_dictionary_file_helper(["APPLE", "BREA8", "CHIPS"], mocker)


@pytest.fixture
def mock_empty_dictionary_file(
    mocker: pytest_mock.MockerFixture,
) -> tuple[mock.MagicMock, list[str]]:
    return _mock_dictionary_file_helper([], mocker)


def _mock_dictionary_file_helper(
    word_list: list[str], mocker: pytest_mock.MockerFixture
) -> tuple[mock.MagicMock, list[str]]:
    word_list_data = "\n".join(word_list)

    # Pathlib uses an open *method*, so to be able to inspect the Path object that
    # open() was called on we need to ensure self is passed to it, which requires
    # binding to the instance. Wrapping the mock object in a function allows this to
    # happen.
    open_mock = mocker.mock_open(read_data=word_list_data)

    def open_mock_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        return open_mock(self, *args, **kwargs)

    mocker.patch("pathlib.Path.open", open_mock_wrapper)
    return open_mock, word_list


class TestSimpleFileLoader:
    def test_loads_word_dictionary(
        self,
        mock_valid_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        open_mock, word_list = mock_valid_dictionary_file
        dictionary_file_path = pathlib.Path("/a/b/c")

        loader = word_dictionary_loaders.SimpleFileLoader(dictionary_file_path)
        word_dictionary = loader.get_word_dictionary()

        open_mock.assert_called_once_with(dictionary_file_path)
        assert word_dictionary == set(word_list)

    def test_loads_word_dictionary_with_word_length(
        self,
        mock_valid_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        open_mock, word_list = mock_valid_dictionary_file
        dictionary_file_path = pathlib.Path("/a/b/c")

        loader = word_dictionary_loaders.SimpleFileLoader(dictionary_file_path)
        word_dictionary = loader.get_word_dictionary(word_length=5)

        open_mock.assert_called_once_with(dictionary_file_path)
        assert word_dictionary == {word for word in word_list if len(word) == 5}

    def test_skips_empty_lines_in_dictionary(
        self,
        mock_valid_empty_line_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        open_mock, word_list = mock_valid_empty_line_dictionary_file
        dictionary_file_path = pathlib.Path("/a/b/c")

        loader = word_dictionary_loaders.SimpleFileLoader(dictionary_file_path)
        word_dictionary = loader.get_word_dictionary()

        open_mock.assert_called_once_with(dictionary_file_path)
        assert word_dictionary == {word for word in word_list if word}

    def test_accepts_non_alphabet_words_without_validator(
        self,
        mock_non_alphabet_character_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        open_mock, word_list = mock_non_alphabet_character_dictionary_file
        dictionary_file_path = pathlib.Path("/a/b/c")

        loader = word_dictionary_loaders.SimpleFileLoader(dictionary_file_path)
        word_dictionary = loader.get_word_dictionary()

        open_mock.assert_called_once_with(dictionary_file_path)
        assert word_dictionary == set(word_list)

    def test_raises_exception_on_invalid_word(
        self,
        mock_non_alphabet_character_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        loader = word_dictionary_loaders.SimpleFileLoader(pathlib.Path("/a/b/c"))
        with pytest.raises(word_dictionary_loaders.InvalidDictionaryWordError):
            loader.get_word_dictionary(
                word_validator=lambda word: all(c in string.ascii_letters for c in word)
            )

    def test_raises_exception_on_empty_dictionary(
        self,
        mock_empty_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        loader = word_dictionary_loaders.SimpleFileLoader(pathlib.Path("/a/b/c"))
        with pytest.raises(word_dictionary_loaders.InvalidDictionaryFileError):
            loader.get_word_dictionary()
