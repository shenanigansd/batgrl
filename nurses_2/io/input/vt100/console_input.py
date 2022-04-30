"""
Parse and create events from a VT100 input stream.
"""
import os
import re
import select
import sys
from codecs import getincrementaldecoder

from ....data_structures import Point
from ..events import Key, KeyPressEvent, MouseEvent, PasteEvent
from .ansi_escapes import NO_MODS, ALT, ANSI_ESCAPES
from .mouse_bindings import TERM_SGR, TYPICAL, URXVT

MOUSE_RE = re.compile("^" + re.escape("\x1b[") + r"(<?[\d;]+[mM]|M...)\Z")
DECODER = getincrementaldecoder("utf-8")("surrogateescape")
FILENO = sys.stdin.fileno()
SELECT_ARGS = [FILENO], [], [], 0

def read_stdin():
    """
    Read (non-blocking) from stdin and return it decoded.
    """
    if not select.select(*SELECT_ARGS)[0]:
        return ""

    try:
        return DECODER.decode(os.read(FILENO, 2048))
    except OSError:
        return ""

def _create_mouse_event(data):
    """
    Create a MouseEvent from ansi escapes.
    """
    if data[2] == "M":  # Typical: "Esc[MaB*"
        mouse_event, x, y = map(ord, data[3:])
        mouse_info = TYPICAL.get(mouse_event)

        if x >= 0xDC00:
            x -= 0xDC00
        if y >= 0xDC00:
            y -= 0xDC00

        x -= 32
        y -= 32

    else:
        if data[2] == "<":  # Xterm SGR: "Esc[<64;85;12M"
            mouse_event, x, y = map(int, data[3:-1].split(";"))
            mouse_info = TERM_SGR.get((mouse_event, data[-1]))

        else:  # Urxvt: "Esc[96;14;13M"
            mouse_event, x, y = map(int, data[2:-1].split(";"))
            mouse_info = URXVT.get(mouse_event)

        x -= 1
        y -= 1

    if mouse_info is not None:
        _EVENTS.append(MouseEvent(Point(y, x), *mouse_info))

def _find_longest_match(data):
    """
    Iteratively look for key matches in data.
    """
    for i in range(len(data), 0, -1):
        prefix = data[:i]
        suffix = data[i:]

        if MOUSE_RE.match(prefix) is not None:
            _create_mouse_event(prefix)
            return suffix

        match ANSI_ESCAPES.get(prefix):
            case None:
                continue

            case Key.Ignore:
                return suffix

            case Key.Paste:
                match suffix.find("\x1b[201~"):
                    case -1:
                        _EVENTS.append(PasteEvent(suffix))
                        return ""
                    case i:
                        _EVENTS.append(PasteEvent(suffix[:i]))
                        return suffix[i + 6:]

            case KeyPressEvent.ESCAPE if suffix and suffix not in ANSI_ESCAPES:
                if len(suffix) == 1:  # alt + character
                    _EVENTS.append(KeyPressEvent(suffix, ALT))
                else:
                    # Unrecognized escape sequence.
                    _EVENTS.append(KeyPressEvent(data, NO_MODS))
                return ""

            case key_press:
                _EVENTS.append(key_press)
                return suffix

    _EVENTS.append(KeyPressEvent(prefix, NO_MODS))
    return suffix

_EVENTS = [ ]

def read_keys():
    data = ""

    while chars := read_stdin():
        data += chars

    while data:
        data = _find_longest_match(data)

    yield from _EVENTS

    _EVENTS.clear()
