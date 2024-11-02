from typing import ClassVar

from rich import text
from textual import app as textual_app
from textual import reactive, widgets

from wordall import game
from wordall.games import wordle


class WordleAlphabetDisplay(widgets.Static):
    alphabet_letter_state_to_style: ClassVar[dict[game.AlphabetLetterState, str]] = {
        game.AlphabetLetterState.FOUND: "black on dark_green",
        game.AlphabetLetterState.FOUND_ELSEWHERE: "black on yellow",
        game.AlphabetLetterState.UNUSED: "white on black",
        game.AlphabetLetterState.NOT_GUESSED: "black on white",
    }

    game_: reactive.Reactive[wordle.WordleGame | None] = reactive.reactive(None)

    def render(self) -> textual_app.RenderResult:
        assert self.game_ is not None

        separator = text.Text(" ")
        return separator.join(
            self.render_alphabet_letter_state(c, state)
            for c, state in self.game_.alphabet_states.items()
        )

    @classmethod
    def render_alphabet_letter_state(
        cls, c: str, state: game.AlphabetLetterState
    ) -> text.Text:
        return text.Text(c, style=cls.alphabet_letter_state_to_style[state])
