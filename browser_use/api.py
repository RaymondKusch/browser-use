from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from browser_use.agent.service import Agent
from langchain_openai import ChatOpenAI
import asyncio
from typing import List

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only - configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TaskRequest(BaseModel):
    task: str

class TaskResponse(BaseModel):
    steps: List[dict]
    mermaid_diagram: str

@app.post("/api/run-task")
async def run_task(request: TaskRequest):
    # Initialize agent with GPT-4
    agent = Agent(
        task=request.task,
        llm=ChatOpenAI(model="gpt-4"),
    )
    
    # Run the agent
    history = await agent.run()
    
    # Generate mermaid diagram
    mermaid_diagram = agent.generate_mermaid_diagram()
    
    # Convert history to serializable format
    steps = []
    for step in history:
        step_data = {
            "extracted_content": step.result.extracted_content,
            "error": step.result.error,
            "is_done": step.result.is_done
        }
        steps.append(step_data)
    
    return TaskResponse(steps=steps, mermaid_diagram=mermaid_diagram)
