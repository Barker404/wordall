import pathlib
import string
import typing
from typing import Any
from unittest import mock

import pytest
import pytest_mock

from wordall import word_dictionary_loaders


def mock_dictionary_file(
    mocker: pytest_mock.MockerFixture,
    word_list: list[str],
) -> mock.MagicMock:
    word_list_data = "\n".join(word_list)

    # Pathlib uses an open *method*, so to be able to inspect the Path object that
    # open() was called on we need to ensure self is passed to it, which requires
    # binding to the instance. Wrapping the mock object in a function allows this to
    # happen.
    open_mock = mocker.mock_open(read_data=word_list_data)

    def open_mock_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        return open_mock(self, *args, **kwargs)

    mocker.patch("pathlib.Path.open", open_mock_wrapper)
    return typing.cast(mock.MagicMock, open_mock)


def mock_multiple_dictionary_files(
    mocker: pytest_mock.MockerFixture,
    word_lists: list[list[str]],
) -> mock.MagicMock:
    word_list_datas = ["\n".join(word_list) for word_list in word_lists]
    mock_files = [
        mocker.mock_open(read_data=data).return_value for data in word_list_datas
    ]

    # Pathlib uses an open *method*, so to be able to inspect the Path object that
    # open() was called on we need to ensure self is passed to it, which requires
    # binding to the instance. Wrapping the mock object in a function allows this to
    # happen.
    open_mock = mocker.mock_open()

    def open_mock_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        return open_mock(self, *args, **kwargs)

    # This allows returning different file content each time open() is called. It will
    # raise StopIteration if open() is called too many times though!
    open_mock.side_effect = mock_files

    mocker.patch("pathlib.Path.open", open_mock_wrapper)
    return typing.cast(mock.MagicMock, open_mock)


class TestSimpleFileLoader:
    def test_loads_word_dictionary(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        word_list = ["APPLE", "BREAD", "CHIPS", "DONUTS", "EGGS"]
        open_mock = mock_dictionary_file(mocker, word_list)
        dictionary_file_path = pathlib.Path("/a/b/c")

        loader = word_dictionary_loaders.SimpleFileLoader(dictionary_file_path)
        word_dictionary = loader.get_word_dictionary()

        open_mock.assert_called_once_with(dictionary_file_path, encoding=None)
        assert word_dictionary == set(word_list)

    def test_loads_word_dictionary_with_encoding(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        word_list = ["APPLE", "BREAD", "CHIPS"]
        open_mock = mock_dictionary_file(mocker, word_list)
        dictionary_file_path = pathlib.Path("/a/b/c")

        loader = word_dictionary_loaders.SimpleFileLoader(
            dictionary_file_path, encoding="latin-1"
        )
        loader.get_word_dictionary()

        open_mock.assert_called_once_with(dictionary_file_path, encoding="latin-1")

    def test_loads_word_dictionary_with_word_length(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        word_list = ["APPLE", "BREAD", "CHIPS", "DONUTS", "EGGS"]
        open_mock = mock_dictionary_file(mocker, word_list)
        dictionary_file_path = pathlib.Path("/a/b/c")

        loader = word_dictionary_loaders.SimpleFileLoader(dictionary_file_path)
        word_dictionary = loader.get_word_dictionary(word_length=5)

        open_mock.assert_called_once_with(dictionary_file_path, encoding=None)
        assert word_dictionary == {word for word in word_list if len(word) == 5}

    def test_skips_empty_lines_in_dictionary(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        word_list = ["", "APPLE", "BREAD", "", "CHIPS", "DONUTS", "EGGS", ""]
        open_mock = mock_dictionary_file(mocker, word_list)
        dictionary_file_path = pathlib.Path("/a/b/c")

        loader = word_dictionary_loaders.SimpleFileLoader(dictionary_file_path)
        word_dictionary = loader.get_word_dictionary()

        open_mock.assert_called_once_with(dictionary_file_path, encoding=None)
        assert word_dictionary == {word for word in word_list if word}

    def test_accepts_non_alphabet_words_without_filter(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        word_list = ["APPLE", "BREA8", "CHIPS", "D*NUT$"]
        open_mock = mock_dictionary_file(mocker, word_list)
        dictionary_file_path = pathlib.Path("/a/b/c")

        loader = word_dictionary_loaders.SimpleFileLoader(dictionary_file_path)
        word_dictionary = loader.get_word_dictionary()

        open_mock.assert_called_once_with(dictionary_file_path, encoding=None)
        assert word_dictionary == set(word_list)

    def test_transforms_words(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        word_list = ["apple", "bread", "chips"]
        mock_dictionary_file(mocker, word_list)
        dictionary_file_path = pathlib.Path("/a/b/c")

        loader = word_dictionary_loaders.SimpleFileLoader(dictionary_file_path)
        word_dictionary = loader.get_word_dictionary(word_transform_function=str.upper)

        assert word_dictionary == {"APPLE", "BREAD", "CHIPS"}

    def test_filters_words(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        word_list = ["APPLE", "BREA8", "CHIPS", "D*NUT$"]
        mock_dictionary_file(mocker, word_list)
        dictionary_file_path = pathlib.Path("/a/b/c")

        def letters_only(word: str) -> bool:
            return all(c in string.ascii_letters for c in word)

        loader = word_dictionary_loaders.SimpleFileLoader(dictionary_file_path)
        word_dictionary = loader.get_word_dictionary(word_filter_function=letters_only)

        assert word_dictionary == {"APPLE", "CHIPS"}

    def test_transforms_before_filtering(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        word_list = ["apple", "bread", "chip!"]
        mock_dictionary_file(mocker, word_list)
        dictionary_file_path = pathlib.Path("/a/b/c")

        def upper_letters_only(word: str) -> bool:
            return all(c in string.ascii_uppercase for c in word)

        loader = word_dictionary_loaders.SimpleFileLoader(dictionary_file_path)
        word_dictionary = loader.get_word_dictionary(
            word_transform_function=str.upper, word_filter_function=upper_letters_only
        )

        assert word_dictionary == {"APPLE", "BREAD"}

    def test_raises_exception_on_empty_dictionary(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mock_dictionary_file(mocker, [])

        loader = word_dictionary_loaders.SimpleFileLoader(pathlib.Path("/a/b/c"))
        with pytest.raises(word_dictionary_loaders.NoWordsFoundError):
            loader.get_word_dictionary()

    def test_raises_exception_on_effective_empty_dictionary(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        word_list = ["APPLE", "BREAD", "CHIPS", "DONUTS", "EGGS"]
        mock_dictionary_file(mocker, word_list)

        loader = word_dictionary_loaders.SimpleFileLoader(pathlib.Path("/a/b/c"))
        with pytest.raises(word_dictionary_loaders.NoWordsFoundError):
            loader.get_word_dictionary(word_filter_function=lambda _: False)


class TestMultipleFileLoader:
    def test_loads_word_dictionaries(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        word_lists = [["APPLE", "BREAD"], ["CHIPS", "DONUTS"], ["EGGS", "FLOUR"]]
        open_mock = mock_multiple_dictionary_files(mocker, word_lists)
        dictionary_file_paths = [
            pathlib.Path("/a/a"),
            pathlib.Path("/a/b"),
            pathlib.Path("/a/c"),
        ]

        loader = word_dictionary_loaders.MultipleFileLoader(dictionary_file_paths)
        word_dictionary = loader.get_word_dictionary()

        open_mock.assert_has_calls(
            [
                mocker.call(dictionary_file_paths[0], encoding=None),
                mocker.call(dictionary_file_paths[1], encoding=None),
                mocker.call(dictionary_file_paths[2], encoding=None),
            ]
        )
        assert word_dictionary == {"APPLE", "BREAD", "CHIPS", "DONUTS", "EGGS", "FLOUR"}

    def test_loads_word_dictionaries_with_encoding(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        word_lists = [["APPLE", "BREAD"], ["CHIPS", "DONUTS"], ["EGGS", "FLOUR"]]
        open_mock = mock_multiple_dictionary_files(mocker, word_lists)
        dictionary_file_paths = [
            pathlib.Path("/a/a"),
            pathlib.Path("/a/b"),
            pathlib.Path("/a/c"),
        ]

        loader = word_dictionary_loaders.MultipleFileLoader(
            dictionary_file_paths, encoding="latin-1"
        )
        loader.get_word_dictionary()

        open_mock.assert_has_calls(
            [
                mocker.call(dictionary_file_paths[0], encoding="latin-1"),
                mocker.call(dictionary_file_paths[1], encoding="latin-1"),
                mocker.call(dictionary_file_paths[2], encoding="latin-1"),
            ]
        )

    def test_loads_word_dictionaries_with_word_length(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        word_lists = [["APPLE", "BREAD"], ["CHIPS", "DONUTS"], ["EGGS", "FLOUR"]]
        mock_multiple_dictionary_files(mocker, word_lists)
        dictionary_file_paths = [
            pathlib.Path("/a/a"),
            pathlib.Path("/a/b"),
            pathlib.Path("/a/c"),
        ]

        loader = word_dictionary_loaders.MultipleFileLoader(dictionary_file_paths)
        word_dictionary = loader.get_word_dictionary(word_length=5)

        assert word_dictionary == {"APPLE", "BREAD", "CHIPS", "FLOUR"}

    def test_skips_empty_lines_in_dictionaries(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        word_lists = [
            ["APPLE", "BREAD", ""],
            ["CHIPS", "", "DONUTS"],
            ["", "EGGS", "FLOUR"],
        ]
        mock_multiple_dictionary_files(mocker, word_lists)
        dictionary_file_paths = [
            pathlib.Path("/a/a"),
            pathlib.Path("/a/b"),
            pathlib.Path("/a/c"),
        ]

        loader = word_dictionary_loaders.MultipleFileLoader(dictionary_file_paths)
        word_dictionary = loader.get_word_dictionary()

        assert word_dictionary == {"APPLE", "BREAD", "CHIPS", "DONUTS", "EGGS", "FLOUR"}

    def test_accepts_non_alphabet_words_without_filter(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        word_lists = [["APPLE", "BREA8"], ["CHIPS", "DONUT$"], ["EGGS", "F-_=R"]]
        mock_multiple_dictionary_files(mocker, word_lists)
        dictionary_file_paths = [
            pathlib.Path("/a/a"),
            pathlib.Path("/a/b"),
            pathlib.Path("/a/c"),
        ]

        loader = word_dictionary_loaders.MultipleFileLoader(dictionary_file_paths)
        word_dictionary = loader.get_word_dictionary()

        assert word_dictionary == {"APPLE", "BREA8", "CHIPS", "DONUT$", "EGGS", "F-_=R"}

    def test_transforms_words(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        word_lists = [["apple", "bread"], ["chips", "donuts"], ["eggs", "flour"]]
        mock_multiple_dictionary_files(mocker, word_lists)
        dictionary_file_paths = [
            pathlib.Path("/a/a"),
            pathlib.Path("/a/b"),
            pathlib.Path("/a/c"),
        ]

        loader = word_dictionary_loaders.MultipleFileLoader(dictionary_file_paths)
        word_dictionary = loader.get_word_dictionary(word_transform_function=str.upper)

        assert word_dictionary == {"APPLE", "BREAD", "CHIPS", "DONUTS", "EGGS", "FLOUR"}

    def test_filters_words(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        word_lists = [["APPLE", "BREA8"], ["CHIPS", "DONUT$"], ["EGGS", "F-_=R"]]
        mock_multiple_dictionary_files(mocker, word_lists)
        dictionary_file_paths = [
            pathlib.Path("/a/a"),
            pathlib.Path("/a/b"),
            pathlib.Path("/a/c"),
        ]

        def letters_only(word: str) -> bool:
            return all(c in string.ascii_letters for c in word)

        loader = word_dictionary_loaders.MultipleFileLoader(dictionary_file_paths)
        word_dictionary = loader.get_word_dictionary(word_filter_function=letters_only)

        assert word_dictionary == {"APPLE", "CHIPS", "EGGS"}

    def test_transforms_before_filtering(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        word_lists = [["apple", "brea8"], ["chips", "donut$"], ["eggs", "f-_=r"]]
        mock_multiple_dictionary_files(mocker, word_lists)
        dictionary_file_paths = [
            pathlib.Path("/a/a"),
            pathlib.Path("/a/b"),
            pathlib.Path("/a/c"),
        ]

        def upper_letters_only(word: str) -> bool:
            return all(c in string.ascii_uppercase for c in word)

        loader = word_dictionary_loaders.MultipleFileLoader(dictionary_file_paths)
        word_dictionary = loader.get_word_dictionary(
            word_transform_function=str.upper, word_filter_function=upper_letters_only
        )

        assert word_dictionary == {"APPLE", "CHIPS", "EGGS"}

    def test_raises_exception_on_empty_dictionaries(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mock_multiple_dictionary_files(mocker, [[], [], []])
        dictionary_file_paths = [
            pathlib.Path("/a/a"),
            pathlib.Path("/a/b"),
            pathlib.Path("/a/c"),
        ]

        loader = word_dictionary_loaders.MultipleFileLoader(dictionary_file_paths)
        with pytest.raises(word_dictionary_loaders.NoWordsFoundError):
            loader.get_word_dictionary()

    def test_raises_exception_on_effective_empty_dictionaries(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        word_lists = [["APPLE", "BREAD"], ["CHIPS", "DONUTS"], ["EGGS", "FLOUR"]]
        mock_multiple_dictionary_files(mocker, word_lists)
        dictionary_file_paths = [
            pathlib.Path("/a/a"),
            pathlib.Path("/a/b"),
            pathlib.Path("/a/c"),
        ]

        loader = word_dictionary_loaders.MultipleFileLoader(dictionary_file_paths)
        with pytest.raises(word_dictionary_loaders.NoWordsFoundError):
            loader.get_word_dictionary(word_filter_function=lambda _: False)

    def test_raises_exception_on_no_dictionaries(self) -> None:
        loader = word_dictionary_loaders.MultipleFileLoader([])
        with pytest.raises(word_dictionary_loaders.NoWordsFoundError):
            loader.get_word_dictionary()


class TestScowlWordListLoader:
    # Not testing functionality that is common with MultipleFileLoader (parent class)
    # due to it already being tested above and complexity of test setup for this class

    def test_selects_word_files_only(self, mocker: pytest_mock.MockerFixture) -> None:
        base_path_mock = mocker.MagicMock(pathlib.Path)
        # Expected to glob once for english words and once for british words
        base_path_mock.glob.side_effect = (
            [pathlib.Path("/a/english-words.10"), pathlib.Path("/a/english-words.60")],
            [pathlib.Path("/a/british-words.25")],
        )

        is_file_mock = mocker.patch("pathlib.Path.is_file")
        is_file_mock.return_value = True

        loader = word_dictionary_loaders.ScowlWordListLoader(
            base_path_mock, 100, max_variants=0
        )
        assert loader.dictionary_file_paths == [
            pathlib.Path("/a/english-words.10"),
            pathlib.Path("/a/english-words.60"),
            pathlib.Path("/a/british-words.25"),
        ]
        assert base_path_mock.glob.mock_calls == [
            mocker.call("english-words.*"),
            mocker.call("british-words.*"),
        ]

    def test_ignores_files_over_max_size(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        base_path_mock = mocker.MagicMock(pathlib.Path)
        # Expected to glob once for english words and once for british words
        base_path_mock.glob.side_effect = (
            [pathlib.Path("/a/english-words.20"), pathlib.Path("/a/english-words.55")],
            [pathlib.Path("/a/british-words.50"), pathlib.Path("/a/british-words.51")],
        )

        is_file_mock = mocker.patch("pathlib.Path.is_file")
        is_file_mock.return_value = True

        loader = word_dictionary_loaders.ScowlWordListLoader(
            base_path_mock, 50, max_variants=0
        )
        assert loader.dictionary_file_paths == [
            pathlib.Path("/a/english-words.20"),
            pathlib.Path("/a/british-words.50"),
        ]

    def test_raises_error_when_max_size_too_big(self) -> None:
        with pytest.raises(ValueError, match="Max size"):
            word_dictionary_loaders.ScowlWordListLoader(pathlib.Path("/a/"), 101)

    def test_searches_for_correct_language_category(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        base_path_mock = mocker.MagicMock(pathlib.Path)
        # Expected to glob once for english words and once for american words
        base_path_mock.glob.side_effect = (
            [pathlib.Path("/a/english-words.20"), pathlib.Path("/a/english-words.40")],
            [pathlib.Path("/a/american-words.60")],
        )

        is_file_mock = mocker.patch("pathlib.Path.is_file")
        is_file_mock.return_value = True

        loader = word_dictionary_loaders.ScowlWordListLoader(
            base_path_mock,
            100,
            language_category=word_dictionary_loaders.ScowlLanguageCategory.AMERICAN,
            max_variants=0,
        )
        assert loader.dictionary_file_paths == [
            pathlib.Path("/a/english-words.20"),
            pathlib.Path("/a/english-words.40"),
            pathlib.Path("/a/american-words.60"),
        ]
        assert base_path_mock.glob.mock_calls == [
            mocker.call("english-words.*"),
            mocker.call("american-words.*"),
        ]

    def test_includes_variants(self, mocker: pytest_mock.MockerFixture) -> None:
        base_path_mock = mocker.MagicMock(pathlib.Path)
        # Expected to glob 3 times for english words and 3 times for american words
        # American variant file names are a special case
        expected_file_names = [
            "english-words.20",
            "english_variant_1-words.20",
            "english_variant_2-words.20",
            "american-words.20",
            "variant_1-words.20",
            "variant_2-words.20",
        ]

        # One filename per glob
        base_path_mock.glob.side_effect = [
            [pathlib.Path(f"/a/{fn}")] for fn in expected_file_names
        ]

        is_file_mock = mocker.patch("pathlib.Path.is_file")
        is_file_mock.return_value = True

        loader = word_dictionary_loaders.ScowlWordListLoader(
            base_path_mock,
            100,
            language_category=word_dictionary_loaders.ScowlLanguageCategory.AMERICAN,
            max_variants=2,
        )
        # All glob results should be in dictionary_file_paths
        assert loader.dictionary_file_paths == [
            pathlib.Path(f"/a/{fn}") for fn in expected_file_names
        ]

        # All globs should be made
        assert base_path_mock.glob.mock_calls == [
            mocker.call(fn.replace("20", "*")) for fn in expected_file_names
        ]

    def test_raises_error_when_max_variants_too_big(self) -> None:
        with pytest.raises(ValueError, match="Max variant"):
            word_dictionary_loaders.ScowlWordListLoader(
                pathlib.Path("/a/"), 100, max_variants=4
            )

    def test_includes_other_subcategories(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        base_path_mock = mocker.MagicMock(pathlib.Path)
        # Expected to glob each subcategory except words for english and british
        expected_file_names = [
            "english-abbreviations.20",
            "english-contractions.20",
            "english-proper-names.20",
            "english-upper.20",
            "british-abbreviations.20",
            "british-contractions.20",
            "british-proper-names.20",
            "british-upper.20",
        ]

        # One filename per glob
        base_path_mock.glob.side_effect = [
            [pathlib.Path(f"/a/{fn}")] for fn in expected_file_names
        ]

        is_file_mock = mocker.patch("pathlib.Path.is_file")
        is_file_mock.return_value = True

        loader = word_dictionary_loaders.ScowlWordListLoader(
            base_path_mock,
            100,
            max_variants=0,
            included_subcategories=[
                word_dictionary_loaders.ScowlWordSubcategory.ABBREVIATIONS,
                word_dictionary_loaders.ScowlWordSubcategory.CONTRACTIONS,
                word_dictionary_loaders.ScowlWordSubcategory.PROPER_NAMES,
                word_dictionary_loaders.ScowlWordSubcategory.UPPER,
            ],
        )
        # All glob results should be in dictionary_file_paths
        assert loader.dictionary_file_paths == [
            pathlib.Path(f"/a/{fn}") for fn in expected_file_names
        ]

        # All globs should be made
        assert base_path_mock.glob.mock_calls == [
            mocker.call(fn.replace("20", "*")) for fn in expected_file_names
        ]

    def test_uses_iso8859_1_by_default(
        self,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        base_path_mock = mocker.MagicMock(pathlib.Path)
        # Expected to glob once for english words and once for british words
        base_path_mock.glob.side_effect = (
            [pathlib.Path("/a/english-words.10"), pathlib.Path("/a/english-words.60")],
            [pathlib.Path("/a/british-words.25")],
        )

        is_file_mock = mocker.patch("pathlib.Path.is_file")
        is_file_mock.return_value = True

        loader = word_dictionary_loaders.ScowlWordListLoader(
            base_path_mock, 100, max_variants=0
        )
        assert loader.encoding == "iso8859-1"
