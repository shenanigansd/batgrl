from pathlib import Path

from batgrl.app import App
from batgrl.gadgets.gadget import Gadget
from batgrl.gadgets.image import Image
from batgrl.gadgets.text import Text, add_text

from .colors import DEFAULT_COLOR_PAIR
from .effects import BOLDCRT
from .memory import MemoryGadget
from .modal import Modal
from .output import Output

TERMINAL = (
    Path(__file__).parent.parent.parent.parent / "assets" / "fallout_terminal.png"
)
HEADER = """\
ROBCO INDUSTRIES <TM> TERMLINK PROTOCOL
ENTER PASSWORD NOW

4 ATTEMPT(S) LEFT: █ █ █ █
"""


class HackApp(App):
    async def on_start(self):
        header = Text(size=(5, 39), default_color_pair=DEFAULT_COLOR_PAIR)
        add_text(header.canvas, HEADER)

        modal = Modal(
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            is_enabled=False,
            is_transparent=True,
        )

        output = Output(
            header,
            modal,
            size=(17, 13),
            pos=(5, 40),
            default_color_pair=DEFAULT_COLOR_PAIR,
        )

        memory = MemoryGadget(
            output,
            size=(17, 39),
            pos=(5, 0),
            default_color_pair=DEFAULT_COLOR_PAIR,
        )

        modal.memory = memory

        terminal = Image(
            path=TERMINAL, size=(36, 63), pos_hint={"y_hint": 0.5, "x_hint": 0.5}
        )
        container = Gadget(
            size=(22, 53),
            pos=(5, 5),
            background_color_pair=DEFAULT_COLOR_PAIR,
        )

        crt = BOLDCRT(size=(22, 53), is_transparent=True)

        terminal.add_gadget(container)
        container.add_gadgets(header, memory, output, modal, crt)
        self.add_gadget(terminal)

        memory.init_memory()


if __name__ == "__main__":
    HackApp(title="Hack", background_color_pair=DEFAULT_COLOR_PAIR).run()
