from textual import app as textual_app
from textual import reactive, widgets

from wordall.games import wordle


class WordleTargetDisplay(widgets.Static):
    game_: reactive.Reactive[wordle.WordleGame | None] = reactive.reactive(None)

    def render(self) -> textual_app.RenderResult:
        assert self.game_ is not None

        return f"The correct answer was: {self.game_.target}."
