from textual.app import RenderResult
from textual.reactive import Reactive, reactive
from textual.widgets import Static

from wordall.games import wordle


class WordleTargetDisplay(Static):
    game_: Reactive[wordle.WordleGame | None] = reactive(None)

    def render(self) -> RenderResult:
        assert self.game_ is not None

        return f"The correct answer was: {self.game_.target}."
