from typing import Any
from unittest import mock

import pytest
import pytest_mock


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
def mock_invalid_character_dictionary_file(
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
