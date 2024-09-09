import pytest

from wordall import wordall


class TestIsWordInAlphabet:
    @pytest.fixture
    def game_with_alphabet(self, mocker):
        # Patch Game so that we can directly create an instance without needing a
        # subclass, and to set ALPHABET to a desired value
        mocker.patch.multiple(wordall.Game, __abstractmethods__=set(), ALPHABET="abcde")
        game = wordall.Game()
        return game

    def test_is_in_alphabet(self, game_with_alphabet):
        assert game_with_alphabet.is_word_in_alphabet("baed")

    def test_not_in_alphabet(self, game_with_alphabet):
        assert not game_with_alphabet.is_word_in_alphabet("abf")


class TestWordleGameInit:
    @pytest.fixture
    def mock_word_list(self, request, mocker):
        word_list = request.param
        word_list_data = "\n".join(word_list)
        open_mock = mocker.patch(
            "builtins.open", mocker.mock_open(read_data=word_list_data)
        )
        return open_mock, word_list

    @pytest.mark.parametrize(
        "mock_word_list", [["APPLE", "BREAD", "CHIPS"]], indirect=True
    )
    def test_loads_word_list(self, mock_word_list):
        open_mock, word_list = mock_word_list
        word_list_path = "/a/b/c"

        wordle_game = wordall.WordleGame(word_list_path, 0)

        open_mock.assert_called_once_with(word_list_path)
        assert wordle_game.word_list == word_list

    @pytest.mark.parametrize(
        "mock_word_list", [["APPLE", "BREA8", "CHIPS"]], indirect=True
    )
    def test_exception_on_non_alphabet_word_list(self, mock_word_list):
        with pytest.raises(wordall.InvalidWordListError):
            wordall.WordleGame("/a/b/c", 0)

    @pytest.mark.parametrize("mock_word_list", [[]], indirect=True)
    def test_exception_on_empty_word_list(self, mock_word_list):
        with pytest.raises(wordall.InvalidWordListError):
            wordall.WordleGame("/a/b/c", 0)

    @pytest.mark.parametrize(
        "mock_word_list", [["APPLE", "BREAD", "CHIPS"]], indirect=True
    )
    def test_selects_random_target(self, mocker, mock_word_list):
        _, word_list = mock_word_list

        mock_choice = mocker.patch("random.choice")

        wordle_game = wordall.WordleGame("/a/b/c", 0)

        mock_choice.assert_called_once_with(word_list)
        assert wordle_game.target == mock_choice.return_value
