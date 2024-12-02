import typing
from unittest import mock

import pytest
import pytest_mock

from wordall import word_dictionary_loaders
from wordall.games import numberle, wordle


@pytest.fixture
def mock_valid_dictionary_word_loader_5_letter(
    mocker: pytest_mock.MockerFixture,
) -> mock.MagicMock:
    word_set = {"APPLE", "BREAD", "CHIPS"}
    return _mock_word_dictionary_loader_helper(word_set, mocker)


def _mock_word_dictionary_loader_helper(
    word_set: set[str], mocker: pytest_mock.MockerFixture
) -> mock.MagicMock:
    mock_loader = mocker.MagicMock(word_dictionary_loaders.WordDictionaryLoader)
    mock_loader.get_word_dictionary.return_value = word_set
    return typing.cast(mock.MagicMock, mock_loader)


@pytest.fixture
def wordle_game_instance_5_letter(
    mock_valid_dictionary_word_loader_5_letter: mock.MagicMock,
) -> wordle.WordleGame:
    return wordle.WordleGame(
        mock_valid_dictionary_word_loader_5_letter, guess_limit=3, target_word_length=5
    )


@pytest.fixture
def wordle_game_instance_5_letter_no_limit(
    mock_valid_dictionary_word_loader_5_letter: mock.MagicMock,
) -> wordle.WordleGame:
    return wordle.WordleGame(
        mock_valid_dictionary_word_loader_5_letter,
        guess_limit=None,
        target_word_length=5,
    )


@pytest.fixture
def numberle_game_instance_5_digit() -> numberle.NumberleGame:
    return numberle.NumberleGame(guess_limit=3, target_word_length=5)


@pytest.fixture
def numberle_game_instance_5_digit_no_limit() -> numberle.NumberleGame:
    return numberle.NumberleGame(guess_limit=None, target_word_length=5)
