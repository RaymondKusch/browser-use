from typing import Optional

from pydantic import BaseModel

from browser_use.dom.views import ProcessedDomContent


# Pydantic
class TabInfo(BaseModel):
	"""Represents information about a browser tab"""

	handle: str
	url: str
	title: str


class BrowserState(ProcessedDomContent):
	"""
	Represents the state of the browser.

	Attributes:
		url (str): The current URL of the browser.
		title (str): The title of the current page.
		current_tab_handle (str): The handle of the current tab.
		tabs (list[TabInfo]): List of information about all open tabs.
		screenshot (Optional[str]): Base64 encoded screenshot of the current page.
	"""
	url: str
	title: str
	current_tab_handle: str
	tabs: list[TabInfo]
	screenshot: Optional[str] = None

	def model_dump(self) -> dict:
		"""
		Dump the model data to a dictionary.

		Returns:
			dict: The model data as a dictionary.
		"""
		dump = super().model_dump()
		# Add a summary of available tabs
		if self.tabs:
			dump['available_tabs'] = [
				f'Tab {i+1}: {tab.title} ({tab.url})' for i, tab in enumerate(self.tabs)
			]
		return dump
