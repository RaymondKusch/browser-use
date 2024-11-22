from typing import Literal, Optional

from pydantic import BaseModel


# Action Input Models
class SearchGoogleAction(BaseModel):
    """
    Model for the 'Search Google' action.

    Attributes:
        query (str): The search query.
    """
    query: str


class GoToUrlAction(BaseModel):
    """
    Model for the 'Go to URL' action.

    Attributes:
        url (str): The URL to navigate to.
    """
    url: str


class ClickElementAction(BaseModel):
    """
    Model for the 'Click element' action.

    Attributes:
        index (int): The index of the element to click.
        num_clicks (int): The number of times to click the element.
    """
    index: int
    num_clicks: int = 1


class InputTextAction(BaseModel):
    """
    Model for the 'Input text' action.

    Attributes:
        index (int): The index of the element to input text into.
        text (str): The text to input.
    """
    index: int
    text: str


class DoneAction(BaseModel):
    """
    Model for the 'Done' action.

    Attributes:
        text (str): The text to indicate completion.
    """
    text: str


class SwitchTabAction(BaseModel):
    """
    Model for the 'Switch tab' action.

    Attributes:
        handle (str): The handle of the tab to switch to.
    """
    handle: str


class OpenTabAction(BaseModel):
    """
    Model for the 'Open new tab' action.

    Attributes:
        url (str): The URL to open in the new tab.
    """
    url: str


class ExtractPageContentAction(BaseModel):
    """
    Model for the 'Extract page content' action.

    Attributes:
        value (Literal['text', 'markdown', 'html']): The format of the extracted content.
    """
    value: Literal['text', 'markdown', 'html'] = 'text'


class ScrollDownAction(BaseModel):
    """
    Model for the 'Scroll down' action.

    Attributes:
        amount (Optional[int]): The number of pixels to scroll down. If None, scroll down one page.
    """
    amount: Optional[int] = None
