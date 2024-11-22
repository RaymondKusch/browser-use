from __future__ import annotations

import json
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Any, Optional, Type, TypeVar

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from openai import RateLimitError
from pydantic import BaseModel, ValidationError

from browser_use.agent.prompts import AgentMessagePrompt, SystemPrompt
from browser_use.agent.views import (
	ActionResult,
	AgentError,
	AgentHistory,
	AgentOutput,
	ModelPricingCatalog,
	TokenDetails,
	TokenUsage,
)
from browser_use.browser.views import BrowserState
from browser_use.controller.service import Controller
from browser_use.telemetry.service import ProductTelemetry
from browser_use.telemetry.views import (
	AgentEndTelemetryEvent,
	AgentRunTelemetryEvent,
	AgentStepErrorTelemetryEvent,
)
from browser_use.utils import time_execution_async

load_dotenv()
logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class Agent:
	"""
	Agent class responsible for executing tasks using a language model and a browser controller.

	Attributes:
		agent_id (str): Unique identifier for the agent.
		task (str): The task to be executed by the agent.
		llm (BaseChatModel): The language model used by the agent.
		controller (Optional[Controller]): The browser controller used by the agent.
		use_vision (bool): Flag to indicate if vision should be used.
		save_conversation_path (Optional[str]): Path to save the conversation history.
		max_failures (int): Maximum number of consecutive failures allowed.
		retry_delay (int): Delay between retries in case of failures.
		system_prompt_class (Type[SystemPrompt]): The class used for system prompts.
		messages (list): List of messages exchanged during the task.
		history (list): List of AgentHistory objects representing the task history.
		n_steps (int): Number of steps executed.
		consecutive_failures (int): Number of consecutive failures encountered.
		usage_metadata (TokenUsage): Metadata for token usage.
	"""

	def __init__(
		self,
		task: str,
		llm: BaseChatModel,
		controller: Optional[Controller] = None,
		use_vision: bool = True,
		save_conversation_path: Optional[str] = None,
		max_failures: int = 5,
		retry_delay: int = 10,
		system_prompt_class: Type[SystemPrompt] = SystemPrompt,
	):
		self.agent_id = str(uuid.uuid4())  # unique identifier for the agent

		self.task = task
		self.use_vision = use_vision
		self.llm = llm
		self.save_conversation_path = save_conversation_path

		# Controller setup
		self.controller_injected = controller is not None
		self.controller = controller or Controller()

		self.system_prompt_class = system_prompt_class

		# Telemetry setup
		self.telemetry = ProductTelemetry()

		# Action and output models setup
		self._setup_action_models()

		self.messages = []
		self._initialize_messages()

		# Tracking variables
		self.history: list[AgentHistory] = []
		self.n_steps = 1
		self.consecutive_failures = 0
		self.max_failures = max_failures
		self.retry_delay = retry_delay

		if save_conversation_path:
			logger.info(f'Saving conversation to {save_conversation_path}')

		self.usage_metadata = TokenUsage(
			input_tokens=0,
			output_tokens=0,
			total_tokens=0,
			input_token_details=TokenDetails(),
			output_token_details=TokenDetails(),
		)

	def _setup_action_models(self) -> None:
		"""Setup dynamic action models from controller's registry"""
		# Get the dynamic action model from controller's registry
		self.ActionModel = self.controller.registry.create_action_model()
		# Create output model with the dynamic actions
		self.AgentOutput = AgentOutput.type_with_custom_actions(self.ActionModel)

	def _initialize_messages(self) -> None:
		"""Initialize message history with system and first message"""
		# Get action descriptions from controller's registry
		action_descriptions = self.controller.registry.get_prompt_description()
		self.system_prompt = self.system_prompt_class(action_descriptions, datetime.now())
		self.messages.append(self.system_prompt.get_system_message())
		self.set_task(self.task)

	def set_task(self, task: str) -> None:
		"""
		Set the task for the agent and add it to the message history.

		Args:
			task (str): The task to be executed by the agent.
		"""
		self.messages.append(HumanMessage(content=f'Your task is: {task}'))

	@time_execution_async('--step')
	async def step(self) -> None:
		"""
		Execute one step of the task.

		Retrieves the current state of the browser, gets the next action from the language model,
		and performs the action using the controller.
		"""
		logger.info(f'\n📍 Step {self.n_steps}')
		state = self.controller.browser.get_state(use_vision=self.use_vision)

		try:
			model_output = await self.get_next_action(state)
			result = self.controller.act(model_output.action)
			if result.extracted_content:
				logger.info(f'📄 Result: {result.extracted_content}')
			self.consecutive_failures = 0

		except Exception as e:
			result = self._handle_step_error(e, state)
			model_output = None

			if result.error:
				self.telemetry.capture(
					AgentStepErrorTelemetryEvent(
						agent_id=self.agent_id,
						error=result.error,
					)
				)

		self._update_messages_with_result(result)
		self._make_history_item(model_output, state, result)

	def _handle_step_error(self, error: Exception, state: BrowserState) -> ActionResult:
			"""
			Handle errors that occur during a step.

			Args:
				error (Exception): The error that occurred.
				state (BrowserState): The current state of the browser.

			Returns:
				ActionResult: The result of handling the error.
			"""
			error_msg = AgentError.format_error(error)
			prefix = f'❌ Result failed {self.consecutive_failures + 1}/{self.max_failures} times:\n '

			if isinstance(error, (ValidationError, ValueError)):
				logger.error(f'{prefix}{error_msg}')
				self.consecutive_failures += 1
			elif isinstance(error, RateLimitError):
				logger.warning(f'{prefix}{error_msg}')
				time.sleep(self.retry_delay)
				self.consecutive_failures += 1
			else:
				logger.error(f'{prefix}{error_msg}')
				self.consecutive_failures += 1

			return ActionResult(error=error_msg)

	def _update_messages_with_result(self, result: ActionResult) -> None:
		"""
		Update the message history with the result of an action.

		Args:
			result (ActionResult): The result of the action.
		"""
		if result.extracted_content:
			self.messages.append(HumanMessage(content=result.extracted_content))
		if result.error:
			self.messages.append(HumanMessage(content=result.error))

	def _make_history_item(
		self,
		model_output: AgentOutput | None,
		state: BrowserState,
		result: ActionResult,
	) -> None:
			"""
			Create and store a history item.

			Args:
				model_output (AgentOutput | None): The output from the language model.
				state (BrowserState): The current state of the browser.
				result (ActionResult): The result of the action.
			"""
			history_item = AgentHistory(model_output=model_output, result=result, state=state)
			self.history.append(history_item)

	@time_execution_async('--get_next_action')
	async def get_next_action(self, state: BrowserState) -> AgentOutput:
		"""
		Get the next action from the language model based on the current state.

		Args:
			state (BrowserState): The current state of the browser.

		Returns:
			AgentOutput: The output from the language model.
		"""
		new_message = AgentMessagePrompt(state).get_user_message()
		input_messages = self.messages + [new_message]

		structured_llm = self.llm.with_structured_output(self.AgentOutput, include_raw=True)
		response: dict[str, Any] = await structured_llm.ainvoke(input_messages)  # type: ignore

		parsed: AgentOutput = response['parsed']

		self._update_message_history(state, parsed)
		self._log_response(parsed)
		self._save_conversation(input_messages, parsed)
		# self._update_usage_metadata(response['raw'])
		return parsed

	def _calc_token_cost(self) -> float:
		"""
		Calculate the cost of tokens used in a request based on the model.

		Returns:
			float: The cost of the tokens used.
		"""
		if isinstance(self.llm, ChatOpenAI):
			model_name = self.llm.model_name
		elif isinstance(self.llm, ChatAnthropic):
			model_name = self.llm.model
		else:
			logger.debug('Model name not supported for pricing calculation')
			return 0

		pricing_catalog = ModelPricingCatalog()

		if model_name == 'gpt-4o':
			model_pricing = pricing_catalog.gpt_4o
		elif model_name == 'gpt-4o-mini':
			model_pricing = pricing_catalog.gpt_4o_mini
		elif model_name == 'claude-3-5-sonnet-20240620':
			model_pricing = pricing_catalog.claude_3_5_sonnet
		else:
			logger.debug(f'Unsupported model: {model_name}')
			return 0

		uncached_input_tokens = (
			self.usage_metadata.input_tokens - self.usage_metadata.input_token_details.cache_read
		)
		factor = 1e6
		cost = (
			(uncached_input_tokens / factor) * model_pricing.uncached_input
			+ (self.usage_metadata.input_token_details.cache_read / factor)
			* model_pricing.cached_input
			+ (self.usage_metadata.output_tokens / factor) * model_pricing.output
		)
		return cost

	def _update_usage_metadata(self, raw_response: AIMessage) -> None:
		"""
		Process the response and update usage metadata.

		Args:
			raw_response (AIMessage): The raw response from the language model.
		"""
		# only supported for openai models for now
		if isinstance(self.llm, ChatAnthropic):
			token_usage_data: dict[str, Any] = raw_response.response_metadata['usage']
			usage_metadata = TokenUsage(
				input_tokens=token_usage_data.get('input_tokens', 0),
				output_tokens=token_usage_data.get('output_tokens', 0),
				total_tokens=token_usage_data.get('input_tokens', 0)
				+ token_usage_data.get('output_tokens', 0),
			)
			self.usage_metadata.input_tokens += usage_metadata.input_tokens
			self.usage_metadata.output_tokens += usage_metadata.output_tokens
			self.usage_metadata.total_tokens += usage_metadata.total_tokens

		elif isinstance(self.llm, ChatOpenAI):
			token_usage_data: dict[str, Any] = raw_response.response_metadata['token_usage']
			usage_metadata = TokenUsage(
				input_tokens=token_usage_data.get('prompt_tokens', 0),
				output_tokens=token_usage_data.get('completion_tokens', 0),
				total_tokens=token_usage_data.get('total_tokens', 0),
				input_token_details=TokenDetails(
					audio=token_usage_data.get('prompt_tokens_details', {}).get('audio_tokens', 0),
					cache_read=token_usage_data.get('prompt_tokens_details', {}).get(
						'cached_tokens', 0
					),
					reasoning=0,  # Assuming reasoning is not part of prompt_tokens_details
				),
				output_token_details=TokenDetails(
					audio=token_usage_data.get('completion_tokens_details', {}).get(
						'audio_tokens', 0
					),
					cache_read=0,  # Assuming cache_read is not part of completion_tokens_details
					reasoning=token_usage_data.get('completion_tokens_details', {}).get(
						'reasoning_tokens', 0
					),
				),
			)

			self.usage_metadata.input_tokens += usage_metadata.input_tokens
			self.usage_metadata.output_tokens += usage_metadata.output_tokens
			self.usage_metadata.total_tokens += usage_metadata.total_tokens

			# update usage metadata
			if usage_metadata.input_token_details:
				for detail_key in usage_metadata.input_token_details.model_dump():
					setattr(
						self.usage_metadata.input_token_details,
						detail_key,
						getattr(self.usage_metadata.input_token_details, detail_key)
						+ getattr(usage_metadata.input_token_details, detail_key),
					)

			if usage_metadata.output_token_details:
				for detail_key in usage_metadata.output_token_details.model_dump():
					setattr(
						self.usage_metadata.output_token_details,
						detail_key,
						getattr(self.usage_metadata.output_token_details, detail_key)
						+ getattr(usage_metadata.output_token_details, detail_key),
					)

		else:
			logger.debug('Model name not supported for pricing calculation')
			return

		self._log_usage_metadata(usage_metadata)

	def _log_usage_metadata(self, current_tokens: Optional[TokenUsage] = None) -> None:
		"""
		Log the usage metadata.

		Args:
			current_tokens (Optional[TokenUsage]): The current token usage.
		"""
		total_cost = self._calc_token_cost()
		total_tokens = self.usage_metadata.total_tokens
		logger.debug(
			f'🔢 Total Tokens: input: {self.usage_metadata.input_tokens} (cached: {self.usage_metadata.input_token_details.cache_read}) + output: {self.usage_metadata.output_tokens} = {total_tokens} = ${total_cost:.4f} 💰'
		)

		if current_tokens:
			logger.debug(
				f'🔢 Last  Tokens: input: {current_tokens.input_tokens} (cached: {current_tokens.input_token_details.cache_read}) + output: {current_tokens.output_tokens} = {current_tokens.total_tokens} '
			)

	def _update_message_history(self, state: BrowserState, response: Any) -> None:
		"""
		Update the message history with new interactions.

		Args:
			state (BrowserState): The current state of the browser.
			response (Any): The response from the language model.
		"""
		history_message = AgentMessagePrompt(state).get_message_for_history()
		self.messages.append(history_message)
		self.messages.append(AIMessage(content=response.model_dump_json(exclude_unset=True)))
		self.n_steps += 1

	def _log_response(self, response: Any) -> None:
		"""
		Log the model's response.

		Args:
			response (Any): The response from the language model.
		"""
		if 'Success' in response.current_state.valuation_previous_goal:
			emoji = '👍'
		elif 'Failed' in response.current_state.valuation_previous_goal:
			emoji = '⚠️'
		else:
			emoji = '🤷'

		logger.info(f'{emoji} Evaluation: {response.current_state.valuation_previous_goal}')
		logger.info(f'🧠 Memory: {response.current_state.memory}')
		logger.info(f'🎯 Next Goal: {response.current_state.next_goal}')
		logger.info(f'🛠️ Action: {response.action.model_dump_json(exclude_unset=True)}')

	def _save_conversation(self, input_messages: list[BaseMessage], response: Any) -> None:
		"""
		Save conversation history to file if path is specified.

		Args:
			input_messages (list[BaseMessage]): The list of input messages.
			response (Any): The response from the language model.
		"""
		if not self.save_conversation_path:
			return

		# create folders if not exists
		os.makedirs(os.path.dirname(self.save_conversation_path), exist_ok=True)

		with open(self.save_conversation_path + f'_{self.n_steps}.txt', 'w') as f:
			self._write_messages_to_file(f, input_messages)
			self._write_response_to_file(f, response)

	def _write_messages_to_file(self, f: Any, messages: list[BaseMessage]) -> None:
		"""
		Write messages to conversation file.

		Args:
			f (Any): The file object to write to.
			messages (list[BaseMessage]): The list of messages to write.
		"""
		for message in messages:
			f.write(f' {message.__class__.__name__} \n')

			if isinstance(message.content, list):
				for item in message.content:
					if isinstance(item, dict) and item.get('type') == 'text':
						f.write(item['text'].strip() + '\n')
			elif isinstance(message.content, str):
				try:
					content = json.loads(message.content)
					f.write(json.dumps(content, indent=2) + '\n')
				except json.JSONDecodeError:
					f.write(message.content.strip() + '\n')

			f.write('\n')

	def _write_response_to_file(self, f: Any, response: Any) -> None:
		"""
		Write model response to conversation file.

		Args:
			f (Any): The file object to write to.
			response (Any): The response from the language model.
		"""
		f.write(' RESPONSE\n')
		f.write(json.dumps(json.loads(response.model_dump_json(exclude_unset=True)), indent=2))

	async def run(self, max_steps: int = 100) -> list[AgentHistory]:
		"""
		Execute the task with a maximum number of steps.

		Args:
			max_steps (int): The maximum number of steps to execute.

		Returns:
			list[AgentHistory]: The history of the task execution.
		"""
		try:
			logger.info(f'🚀 Starting task: {self.task}')

			self.telemetry.capture(
				AgentRunTelemetryEvent(
					agent_id=self.agent_id,
					task=self.task,
				)
			)

			for step in range(max_steps):
				if self._too_many_failures():
					break

				await self.step()

				if self._is_task_complete():
					logger.info('✅ Task completed successfully')
					break
			else:
				logger.info('❌ Failed to complete task in maximum steps')

			return self.history

		finally:
			self.telemetry.capture(
				AgentEndTelemetryEvent(
					agent_id=self.agent_id,
					task=self.task,
					success=self._is_task_complete(),
					steps=len(self.history),
				)
			)
			if not self.controller_injected:
				self.controller.browser.close()

	def _too_many_failures(self) -> bool:
		"""
		Check if the task should stop due to too many consecutive failures.

		Returns:
			bool: True if the task should stop, False otherwise.
		"""
		if self.consecutive_failures >= self.max_failures:
			logger.error(f'❌ Stopping due to {self.max_failures} consecutive failures')
			return True
		return False

	def _is_task_complete(self) -> bool:
		"""
		Check if the task has been completed successfully.

		Returns:
			bool: True if the task is complete, False otherwise.
		"""
		return bool(self.history and self.history[-1].result.is_done)

	def generate_mermaid_diagram(self) -> str:
		"""
		Generate a mermaid diagram from the agent's steps.

		Returns:
			str: The mermaid diagram representing the task steps.
		"""
		diagram = "graph TD\n"
		for i, step in enumerate(self.history):
			content = step.result.extracted_content or step.result.error or "No content"
			diagram += f"    step{i}['{content}']\n"
			if i > 0:
				diagram += f"    step{i-1} --> step{i}\n"
		logger.debug(f'Generated Mermaid Diagram:\n{diagram}')
		return diagram
