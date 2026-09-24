"""
mistune
~~~~~~~

A fast yet powerful Python Markdown parser with renderers and
plugins, compatible with CommonMark 0.31.2.

Documentation: https://mistune.lepture.com/
"""

from copy import copy
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple, Union

from .block_parser import BlockParser
from .core import BaseRenderer, BlockState, InlineState
from .inline_parser import InlineParser
from .markdown import Markdown
from .plugins import Plugin, PluginRef, import_plugin
from .renderers.html import HTMLRenderer
from .util import escape, escape_url, safe_entity, unikey

RendererRef = Union[Literal["html", "ast"], BaseRenderer]


class _EscapeUnset:
    pass


_escape_unset = _EscapeUnset()


def create_markdown(
    escape: Union[bool, _EscapeUnset] = _escape_unset,
    hard_wrap: bool = False,
    renderer: Optional[RendererRef] = "html",
    plugins: Optional[Iterable[PluginRef]] = None,
) -> Markdown:
    """Create a Markdown instance based on the given condition.

    :param escape: Boolean for HTML output. An explicit value overrides the
        renderer setting; omit it to keep the renderer setting.
    :param hard_wrap: Boolean. Break every new line into ``<br>``.
    :param renderer: renderer instance, default is HTMLRenderer.
    :param plugins: List of plugins.

    This method is used when you want to re-use a Markdown instance::

        markdown = create_markdown(
            escape=False,
            hard_wrap=True,
        )
        # re-use markdown function
        markdown('.... your text ...')
    """
    escape_html = True if isinstance(escape, _EscapeUnset) else escape

    if renderer == "ast":
        # explicit and more similar to 2.x's API
        renderer = None
    elif isinstance(renderer, HTMLRenderer):
        if not isinstance(escape, _EscapeUnset):
            renderer = copy(renderer)
            renderer._escape = escape
    elif renderer == "html":
        renderer = HTMLRenderer(escape=escape_html)

    inline = InlineParser(hard_wrap=hard_wrap)
    real_plugins: Optional[Iterable[Plugin]] = None
    if plugins is not None:
        real_plugins = [import_plugin(n) for n in plugins if n != "speedup"]
    return Markdown(renderer=renderer, inline=inline, plugins=real_plugins)


html: Markdown = create_markdown(escape=False, plugins=["strikethrough", "footnotes", "table"])


__cached_parsers: Dict[
    Tuple[Union[bool, _EscapeUnset], Optional[RendererRef], Optional[Iterable[Any]]],
    Markdown,
] = {}


def markdown(
    text: str,
    escape: Union[bool, _EscapeUnset] = _escape_unset,
    renderer: Optional[RendererRef] = "html",
    plugins: Optional[Iterable[Any]] = None,
) -> Union[str, List[Dict[str, Any]]]:
    if renderer == "ast":
        # explicit and more similar to 2.x's API
        renderer = None
    key = (escape, renderer, plugins)
    if key in __cached_parsers:
        return __cached_parsers[key](text)

    md = create_markdown(escape=escape, renderer=renderer, plugins=plugins)
    # improve the speed for markdown parser creation
    __cached_parsers[key] = md
    return md(text)


__all__ = [
    "Markdown",
    "HTMLRenderer",
    "BlockParser",
    "BlockState",
    "BaseRenderer",
    "InlineParser",
    "InlineState",
    "escape",
    "escape_url",
    "safe_entity",
    "unikey",
    "html",
    "create_markdown",
    "markdown",
]

__version__ = "3.4.0"
__homepage__ = "https://mistune.lepture.com/"
