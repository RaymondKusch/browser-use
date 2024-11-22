# 🌐 Browser Use

Make websites accessible for AI agents 🤖.

[![GitHub stars](https://img.shields.io/github/stars/gregpr07/browser-use?style=social)](https://github.com/gregpr07/browser-use/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Discord](https://img.shields.io/discord/1303749220842340412?color=7289DA&label=Discord&logo=discord&logoColor=white)](https://link.browser-use.com/discord)

## Table of Contents

* [Quick Start](#quick-start)
* [Demos](#demos)
* [Features](#features-)
* [Register Custom Actions](#register-custom-actions)
* [Get XPath History](#get-xpath-history)
* [More Examples](#more-examples)
* [Telemetry](#telemetry)
* [Contributing](#contributing)
* [Repository Structure](#repository-structure)
* [Code Organization](#code-organization)
* [Frontend Implementation](#frontend-implementation)
* [Backend Architecture](#backend-architecture)
* [API Integrations](#api-integrations)
* [Testing Implementation](#testing-implementation)

## Quick Start

With pip:

```bash
pip install browser-use
```

Spin up your agent:

```python
from langchain_openai import ChatOpenAI
from browser_use import Agent

agent = Agent(
    task="Find a one-way flight from Bali to Oman on 12 January 2025 on Google Flights. Return me the cheapest option.",
    llm=ChatOpenAI(model="gpt-4o"),
)

# ... inside an async function
await agent.run()
```

And don't forget to add your API keys to your `.env` file.

```bash
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

## Demos

<div style="font-size: 4em;">
    Prompt: Find flights on kayak.com from Zurich to Beijing on 25.12.2024 to 02.02.2025. (8x speed)
</div>

![flight search 8x 10fps](https://github.com/user-attachments/assets/ea605d4a-90e6-481e-a569-f0e0db7e6390)

<div style="font-size: 4em;">
    Prompt: Solve the captcha. (2x speed)
</div>
<img src="https://github.com/MagMueller/examples-browser-use/blob/main/captcha/captcha%20big.gif" alt="Solving Captcha" style="max-width:300px;">

<div style="font-size: 4em;">
    Prompt: Look up models with a license of cc-by-sa-4.0 and sort by most likes on Hugging face, save top 5 to file. (1x speed)
</div>

https://github.com/user-attachments/assets/de73ee39-432c-4b97-b4e8-939fd7f323b3

## Features ⭐

- Vision + html extraction
- Automatic multi-tab management
- Extract clicked elements XPaths and repeat exact LLM actions
- Add custom actions (e.g. save to file, push to database, notify me, get human input)
- Self-correcting
- Use any LLM supported by LangChain (e.g. gpt4o, gpt4o mini, claude 3.5 sonnet, llama 3.1 405b, etc.)

## Register Custom Actions

If you want to add custom actions your agent can take, you can register them like this:

```python
from browser_use.agent.service import Agent
from browser_use.browser.service import Browser
from browser_use.controller.service import Controller

# Initialize controller first
controller = Controller()

@controller.action('Ask user for information')
def ask_human(question: str, display_question: bool) -> str:
	return input(f'\n{question}\nInput: ')
```

Or define your parameters using Pydantic

```python
class JobDetails(BaseModel):
  title: str
  company: str
  job_link: str
  salary: Optional[str] = None

@controller.action('Save job details which you found on page', param_model=JobDetails, requires_browser=True)
def save_job(params: JobDetails, browser: Browser):
	print(params)

  # use the browser normally
  browser.driver.get(params.job_link)
```

and then run your agent:

```python
model = ChatAnthropic(model_name='claude-3-5-sonnet-20240620', timeout=25, stop=None, temperature=0.3)
agent = Agent(task=task, llm=model, controller=controller)

await agent.run()
```

## Get XPath History

To get the entire history of everything the agent has done, you can use the output of the `run` method:

```python
history: list[AgentHistory] = await agent.run()

print(history)
```

## More Examples

For more examples see the [examples](examples) folder or join the [Discord](https://link.browser-use.com/discord) and show off your project.

## Telemetry

We collect anonymous usage data to help us understand how the library is being used and to identify potential issues. There is no privacy risk, as no personal information is collected. We collect data with PostHog.

You can opt out of telemetry by setting the `ANONYMIZED_TELEMETRY=false` environment variable.

## Contributing

Contributions are welcome! Feel free to open issues for bugs or feature requests.

### Local Setup

1. Create a virtual environment and install dependencies:

```bash
# To install all dependencies including dev
pip install . ."[dev]"
```

2. Add your API keys to the `.env` file:

```bash
cp .env.example .env
```

or copy the following to your `.env` file:

```bash
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

You can use any LLM model supported by LangChain by adding the appropriate environment variables. See [langchain models](https://python.langchain.com/docs/integrations/chat/) for available options.

### Building the package

```bash
hatch build
```

Feel free to join the [Discord](https://link.browser-use.com/discord) for discussions and support.

## Repository Structure

The repository is organized into several directories, each serving a specific purpose:

- `browser_use/agent`: Contains the agent-related code, including prompts and services.
- `browser_use/browser`: Contains the browser-related code, including services and views.
- `browser_use/controller`: Contains the controller-related code, including registry and views.
- `ui`: Contains the frontend implementation files.
- `tests`: Contains the testing files.

## Code Organization

The code is organized into different modules to ensure modularity and reusability:

- `browser_use/agent/service.py`: Contains the main agent logic and interactions with the LLM.
- `browser_use/agent/views.py`: Contains the data models and views for the agent.
- `browser_use/browser/service.py`: Contains the browser automation logic using Selenium.
- `browser_use/browser/views.py`: Contains the data models and views for the browser state.
- `browser_use/controller/registry/service.py`: Contains the registry logic for registering and managing actions.
- `browser_use/controller/registry/views.py`: Contains the data models and views for the action registry.
- `browser_use/controller/service.py`: Contains the main controller logic and action execution.
- `browser_use/controller/views.py`: Contains the data models and views for the controller actions.
- `ui/App.js`: Contains the main React component for the frontend.
- `ui/BrowserView.js`: Contains the React component for displaying the browser view.
- `ui/AgentReasoning.js`: Contains the React component for displaying the agent's reasoning.
- `ui/MermaidDiagram.js`: Contains the React component for displaying the mermaid diagram.
- `ui/index.js`: Contains the entry point for the React application.
- `ui/webpack.config.js`: Contains the webpack configuration for the frontend.
- `ui/package.json`: Contains the project setup and dependencies for the frontend.

## Frontend Implementation

The frontend is implemented using React and is organized into several components:

- `App.js`: The main component that manages the state and interactions.
- `BrowserView.js`: Displays the browser view in an iframe.
- `AgentReasoning.js`: Displays the agent's reasoning steps.
- `MermaidDiagram.js`: Displays the mermaid diagram generated by the agent.
- `index.js`: The entry point for the React application.
- `webpack.config.js`: The webpack configuration for bundling the frontend.
- `package.json`: The project setup and dependencies for the frontend.

## Backend Architecture

The backend is implemented using FastAPI and is organized into several modules:

- `browser_use/api.py`: Contains the API endpoints for running tasks and interacting with the agent.
- `browser_use/agent/service.py`: Contains the main agent logic and interactions with the LLM.
- `browser_use/agent/views.py`: Contains the data models and views for the agent.
- `browser_use/browser/service.py`: Contains the browser automation logic using Selenium.
- `browser_use/browser/views.py`: Contains the data models and views for the browser state.
- `browser_use/controller/registry/service.py`: Contains the registry logic for registering and managing actions.
- `browser_use/controller/registry/views.py`: Contains the data models and views for the action registry.
- `browser_use/controller/service.py`: Contains the main controller logic and action execution.
- `browser_use/controller/views.py`: Contains the data models and views for the controller actions.

## API Integrations

The project integrates with several APIs to provide its functionality:

- OpenAI API: Used for interacting with the GPT-4 model.
- Anthropic API: Used for interacting with the Claude model.
- FastAPI: Used for creating the API endpoints.

## Testing Implementation

The project includes several tests to ensure the functionality of the code:

- Unit tests for utilities and helpers.
- Integration tests for API endpoints.
- Component tests for the frontend.
- End-to-end (E2E) tests for critical user flows.
- Performance tests.
- Security tests.

To run the tests, use the following command:

```bash
pytest
```

---

<div align="center">
  <b>Star ⭐ this repo if you find it useful!</b><br>
  Made with ❤️ by the Browser-Use team
</div>
