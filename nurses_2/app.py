from abc import ABC, abstractmethod
import asyncio
from contextlib import contextmanager

from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyProcessor
from prompt_toolkit.input import create_input
from prompt_toolkit.output import create_output

from .widgets import Root

ESCAPE_TIMEOUT = .05  # Seconds before we flush an escape character in the input queue.
POLL_INTERVAL = .5  # Seconds between polling for resize events.
REFRESH_INTERVAL = 0  # Seconds between screen redraws.


class App(ABC):
    """Base for creating terminal applications.
    """
    def __init__(self, *, key_bindings=None):
        self.key_bindings = key_bindings or KeyBindings()

    @abstractmethod
    async def on_start(self):
        """Add widgets to root and kick-off event loop.
        """

    def run(self):
        """Run the app.
        """
        try:
            asyncio.run(self._run_async())
        except asyncio.CancelledError:
            pass

    def exit(self, *args):
        for task in asyncio.all_tasks():
            task.cancel()

    async def _run_async(self):
        """Create root widget and schedule input reading, size polling, auto-rendering, and finally, `on_start`.
        """
        with create_environment() as (env_out, env_in):
            self.env_out = env_out
            self.env_in = env_in

            key_processor = KeyProcessor(self.key_bindings)
            self.root = root = Root(env_out)

            loop = asyncio.get_event_loop()
            flush_timer = asyncio.TimerHandle(0, lambda: None, (), loop)  # dummy handle

            def read_from_input():
                """Read and process input.
                """
                keys = env_in.read_keys()

                key_processor.feed_multiple(keys)
                key_processor.process_keys()

                nonlocal flush_timer
                flush_timer.cancel()
                flush_timer = loop.call_later(ESCAPE_TIMEOUT, flush_input)

            def flush_input():
                """Flush input.
                """
                keys = env_in.flush_keys()

                key_processor.feed_multiple(keys)
                key_processor.process_keys()

            async def poll_size():
                """Poll terminal dimensions every `POLL_INTERVAL` seconds and resize root if dimensions have changed.
                """
                size = env_out.get_size()
                resize = root.resize

                while True:
                    await asyncio.sleep(POLL_INTERVAL)

                    new_size = env_out.get_size()
                    if size != new_size:
                        resize(new_size)
                        size = new_size

            async def auto_render():
                """Render screen every `REFRESH_INTERVAL` seconds.
                """
                render = root.render

                while True:
                    await asyncio.sleep(REFRESH_INTERVAL)
                    render()

            with env_in.raw_mode(), env_in.attach(read_from_input):
                await asyncio.gather(
                    poll_size(),
                    auto_render(),
                    self.on_start(),
                )


@contextmanager
def create_environment():
    """Platform specific output/input. Restores output and closes/flushes input on exit.
    """
    env_out = create_output()
    env_out.enter_alternate_screen()
    env_out.erase_screen()
    env_out.hide_cursor()
    env_out.flush()

    env_in = create_input()
    env_in.flush_keys()  # Ignoring type-ahead

    try:
        yield env_out, env_in
    finally:
        env_in.flush_keys()
        env_in.close()

        env_out.scroll_buffer_to_prompt()
        env_out.quit_alternate_screen()
        env_out.flush()
