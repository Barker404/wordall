from typing import Any, ClassVar, Generic, TypeVar

from rich import text
from textual import app as textual_app
from textual import reactive, widgets

from wordall import game

T = TypeVar("T", bound=game.Game)


class GuessesDisplay(widgets.Static, Generic[T]):
    game_: reactive.Reactive[T | None] = reactive.reactive(None)


# This would be better as a protocol, but there's no typing.Intersection to have it also
# be typed as a Game subclass
GameWithGuessList = game.SingleWordleLikeBaseGame


class GuessesFromListDisplay(GuessesDisplay[GameWithGuessList]):
    game_: reactive.Reactive[GameWithGuessList | None] = reactive.reactive(None)

    def compose(self) -> textual_app.ComposeResult:
        # At compose time reactive game has been data bound, but not yet updated to
        # match parent version. So instead we use a hack to directly access the game on
        # the app.
        game_: game.Game = self.app.game_  # type: ignore
        assert isinstance(game_, GameWithGuessList)

        for i in range(game_.guess_limit):
            yield GuessFromListDisplay(i).data_bind(GuessesFromListDisplay.game_)


class GuessFromListDisplay(widgets.Static):
    guess_letter_state_to_style: ClassVar[dict[game.GuessLetterState, str]] = {
        game.GuessLetterState.CORRECT: "black on dark_green",
        game.GuessLetterState.ELSEWHERE: "black on yellow",
        game.GuessLetterState.INCORRECT: "white on black",
    }

    game_: reactive.Reactive[GameWithGuessList | None] = reactive.reactive(None)

    def __init__(self, guess_number: int, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.guess_number = guess_number

    def render(self) -> textual_app.RenderResult:
        assert self.game_ is not None

        separator = text.Text(" ")
        if len(self.game_.guesses) > self.guess_number:
            guess = self.game_.guesses[self.guess_number]
            return separator.join(
                self.render_guess_letter_state(c, state)
                for c, state in guess.guess_letter_states
            )
        elif self.game_.max_guess_word_length is not None:
            return separator.join([text.Text("#")] * self.game_.max_guess_word_length)
        else:
            return text.Text("#")

    @classmethod
    def render_guess_letter_state(
        cls, c: str, state: game.GuessLetterState
    ) -> text.Text:
        return text.Text(c, style=cls.guess_letter_state_to_style[state])
