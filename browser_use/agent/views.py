from __future__ import annotations

from typing import Optional, Type

from pydantic import BaseModel, ConfigDict, Field, ValidationError, create_model

from browser_use.browser.views import BrowserState
from browser_use.controller.registry.views import ActionModel


class TokenDetails(BaseModel):
	"""
	Represents the details of token usage.

	Attributes:
		audio (int): Number of audio tokens used.
		cache_read (int): Number of cache read tokens used.
		reasoning (int): Number of reasoning tokens used.
	"""
	audio: int = 0
	cache_read: int = 0
	reasoning: int = 0


class TokenUsage(BaseModel):
	"""
	Represents the usage of tokens.

	Attributes:
		input_tokens (int): Number of input tokens used.
		output_tokens (int): Number of output tokens used.
		total_tokens (int): Total number of tokens used.
		input_token_details (TokenDetails): Details of input token usage.
		output_token_details (TokenDetails): Details of output token usage.
	"""
	input_tokens: int
	output_tokens: int
	total_tokens: int
	input_token_details: TokenDetails = Field(default=TokenDetails())
	output_token_details: TokenDetails = Field(default=TokenDetails())

	# allow arbitrary types
	model_config = ConfigDict(arbitrary_types_allowed=True)


class Pricing(BaseModel):
	"""
	Represents the pricing details for token usage.

	Attributes:
		uncached_input (float): Price per 1M uncached input tokens.
		cached_input (float): Price per 1M cached input tokens.
		output (float): Price per 1M output tokens.
	"""
	uncached_input: float  # per 1M tokens
	cached_input: float
	output: float


class ModelPricingCatalog(BaseModel):
	"""
	Represents the pricing catalog for different models.

	Attributes:
		gpt_4o (Pricing): Pricing details for GPT-4o model.
		gpt_4o_mini (Pricing): Pricing details for GPT-4o mini model.
		claude_3_5_sonnet (Pricing): Pricing details for Claude 3.5 Sonnet model.
	"""
	gpt_4o: Pricing = Field(default=Pricing(uncached_input=2.50, cached_input=1.25, output=10.00))
	gpt_4o_mini: Pricing = Field(
		default=Pricing(uncached_input=0.15, cached_input=0.075, output=0.60)
	)
	claude_3_5_sonnet: Pricing = Field(
		default=Pricing(uncached_input=3.00, cached_input=1.50, output=15.00)
	)


class ActionResult(BaseModel):
	"""
	Represents the result of executing an action.

	Attributes:
		is_done (Optional[bool]): Indicates if the action is done.
		extracted_content (Optional[str]): The content extracted as a result of the action.
		error (Optional[str]): The error message if the action failed.
	"""
	is_done: Optional[bool] = False
	extracted_content: Optional[str] = None
	error: Optional[str] = None


class AgentBrain(BaseModel):
	"""
	Represents the current state of the agent's brain.

	Attributes:
		valuation_previous_goal (str): Valuation of the previous goal.
		memory (str): Memory of the agent.
		next_goal (str): The next goal of the agent.
	"""
	valuation_previous_goal: str
	memory: str
	next_goal: str


class AgentOutput(BaseModel):
	"""
	Represents the output model for the agent.

	Attributes:
		current_state (AgentBrain): The current state of the agent's brain.
		action (ActionModel): The action to be performed by the agent.
	"""
	model_config = ConfigDict(arbitrary_types_allowed=True)

	current_state: AgentBrain
	action: ActionModel

	@staticmethod
	def type_with_custom_actions(custom_actions: Type[ActionModel]) -> Type['AgentOutput']:
		"""
		Extend actions with custom actions.

		Args:
			custom_actions (Type[ActionModel]): The custom actions to be added.

		Returns:
			Type['AgentOutput']: The extended AgentOutput model.
		"""
		return create_model(
			'AgentOutput',
			__base__=AgentOutput,
			action=(custom_actions, Field(...)),  # Properly annotated field with no default
			__module__=AgentOutput.__module__,
		)


class AgentHistory(BaseModel):
	"""
	Represents a history item for agent actions.

	Attributes:
		model_output (AgentOutput | None): The output from the agent model.
		result (ActionResult): The result of the action.
		state (BrowserState): The state of the browser.
	"""
	model_output: AgentOutput | None
	result: ActionResult
	state: BrowserState

	model_config = ConfigDict(arbitrary_types_allowed=True, protected_namespaces=())


class AgentError:
	"""
	Container for agent error handling.

	Attributes:
		VALIDATION_ERROR (str): Error message for validation errors.
		RATE_LIMIT_ERROR (str): Error message for rate limit errors.
		NO_VALID_ACTION (str): Error message for no valid action found.
	"""
	VALIDATION_ERROR = 'Invalid model output format. Please follow the correct schema.'
	RATE_LIMIT_ERROR = 'Rate limit reached. Waiting before retry.'
	NO_VALID_ACTION = 'No valid action found'

	@staticmethod
	def format_error(error: Exception) -> str:
		"""
		Format error message based on error type.

		Args:
			error (Exception): The error that occurred.

		Returns:
			str: The formatted error message.
		"""
		if isinstance(error, ValidationError):
			return f'{AgentError.VALIDATION_ERROR}\nDetails: {str(error)}'
		return f'Unexpected error: {str(error)}'
