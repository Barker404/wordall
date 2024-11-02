from typing import ClassVar

from rich import text
from textual.app import RenderResult
from textual.reactive import Reactive, reactive
from textual.widgets import Static

from wordall import game
from wordall.games import wordle


class WordleAlphabetDisplay(Static):
    alphabet_letter_state_to_style: ClassVar[dict[game.AlphabetLetterState, str]] = {
        game.AlphabetLetterState.FOUND: "black on dark_green",
        game.AlphabetLetterState.FOUND_ELSEWHERE: "black on yellow",
        game.AlphabetLetterState.UNUSED: "white on black",
        game.AlphabetLetterState.NOT_GUESSED: "black on white",
    }

    game_: Reactive[wordle.WordleGame | None] = reactive(None)

    def render(self) -> RenderResult:
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
