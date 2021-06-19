from abc import ABC, abstractmethod
import asyncio
from contextlib import contextmanager

from prompt_toolkit.key_binding.key_bindings import Binding
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyProcessor
from prompt_toolkit.input import create_input
from prompt_toolkit.output import create_output

from .widgets import Widget

FLUSH_INTERVAL = .05
POLL_INTERVAL = .5
REFRESH_INTERVAL = 0


class App(ABC):
    """Base for creating terminal applications.
    """
    @abstractmethod
    def build(self):
        """Build and return the root widget for the app.
        """

    @abstractmethod
    async def on_start(self):
        """Main coroutine. Event loop starts here.
        """

    def run(self):
        """Run the app.
        """
        try:
            asyncio.run(self._run_async())
        except asyncio.CancelledError:
            pass

    def exit(self):
        for task in self._tasks:
            task.cancel()

        self._flush_task.cancel()

    def _on_resize(self):
        """Adjust widget geometry and redraw the screen.
        """
        # self.root.update_geometry()  # TODO: Uncomment once widgets are implemented.
        self._refresh()

    def _refresh(self):
        """Redraw the screen.
        """

    async def _run_async(self):
        with create_environment() as (env_out, env_in):
            self.env_out = env_out
            self.env_in = env_in

            self.kb = kb = KeyBindings()
            self.key_processor = key_processor = KeyProcessor(kb)

            self._tasks = tasks = [ ]
            self._flush_task = asyncio.create_task(_dummy_coroutine())

            self.root = self.build()
            # assert isinstance(self.root, Widget), f"expected Widget, got {type(self.root).__name__}"  # TODO: Uncomment once widgets are implemented.

            def read_from_input():
                """Read and process input.
                """
                keys = env_in.read_keys()

                key_processor.feed_multiple(keys)
                key_processor.process_keys()

                self._flush_task.cancel()
                self._flush_task = asyncio.create_task(flush_soon())

            def flush_input():
                """Flush input.
                """
                keys = env_in.flush_keys()

                key_processor.feed_multiple(keys)
                key_processor.process_keys()

            async def flush_soon():
                await asyncio.sleep(FLUSH_INTERVAL)
                flush_input()

            async def poll_size():
                """Poll terminal dimensions every `POLL_INTERVAL` seconds and resize if dimensions have changed.
                """
                size = env_out.get_size()

                while True:
                    await asyncio.sleep(POLL_INTERVAL)

                    new_size = env_out.get_size()
                    if size != new_size:
                        self._on_resize()
                        size = new_size

            async def auto_refresh():
                """Redraw the screen every `REFRESH_INTERVAL` seconds.
                """
                while True:
                    await asyncio.sleep(REFRESH_INTERVAL)
                    self._refresh()

            with env_in.raw_mode(), env_in.attach(read_from_input):
                tasks.append( asyncio.create_task(poll_size()) )
                tasks.append( asyncio.create_task(auto_refresh()) )
                main = asyncio.create_task(self.on_start())
                tasks.append(main)
                await main


################################################# W ###
# A hack to avoid prompt-toolkit's `App` class. # A ###
def call(self, event):                          # R ###
    if result := self.handler(event):           # N ###
        asyncio.create_task(result)             # I ###
                                                # N ###
Binding.call = call                             # G ###
################################################# ! ###

@contextmanager
def create_environment():
    env_out = create_output()
    env_in = create_input()

    env_out.enter_alternate_screen()
    env_out.hide_cursor()
    env_out.flush()

    env_in.flush_keys()  # Ignoring type-ahead

    try:
        yield env_out, env_in
    finally:
        env_out.flush()
        env_out.quit_alternate_screen()

        env_in.flush_keys()
        env_in.close()

async def _dummy_coroutine():
    """Used to initialize dummy tasks.
    """
    pass
