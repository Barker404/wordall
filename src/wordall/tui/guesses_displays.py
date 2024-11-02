from typing import Any, ClassVar, cast

from rich import text
from textual import app as textual_app
from textual import reactive, widgets

from wordall import game
from wordall.games import wordle
from wordall.tui import app


class WordleGuessDisplay(widgets.Static):
    guess_letter_state_to_style: ClassVar[dict[game.GuessLetterState, str]] = {
        game.GuessLetterState.CORRECT: "black on dark_green",
        game.GuessLetterState.ELSEWHERE: "black on yellow",
        game.GuessLetterState.INCORRECT: "white on black",
    }

    game_: reactive.Reactive[wordle.WordleGame | None] = reactive.reactive(None)

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
        else:
            return separator.join([text.Text("#")] * len(self.game_.target))

    @classmethod
    def render_guess_letter_state(
        cls, c: str, state: game.GuessLetterState
    ) -> text.Text:
        return text.Text(c, style=cls.guess_letter_state_to_style[state])


class WordleGuessesDisplay(widgets.Static):
    game_: reactive.Reactive[wordle.WordleGame | None] = reactive.reactive(None)

    def compose(self) -> textual_app.ComposeResult:
        # At compose time reactive game has been data bound, but not yet updated to
        # match parent version. So instead we use a hack to directly access the game on
        # the app.
        game_ = cast(wordle.WordleGame, cast(app.WordallApp, self.app).game_)
        for i in range(game_.guess_limit):
            yield WordleGuessDisplay(i).data_bind(WordleGuessesDisplay.game_)
