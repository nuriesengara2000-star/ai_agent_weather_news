"""
agent.py — Creates the LangChain agent powered by OpenAI GPT.

Usage:
    from agent import create_agent

    agent = create_agent()
    result = agent.invoke({"input": "What is the weather in Berlin?"})
    print(result["output"])
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tools import ALL_TOOLS

# ---------------------------------------------------------------------------
# System prompt — guides the model on tool usage and response style
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a helpful AI assistant with access to real-time external tools.

AVAILABLE TOOLS:

1. get_weather — Returns current weather for a city.
   Use when the user asks about weather, temperature, or conditions in a city.

2. get_news — Searches for latest news articles on a topic.
   Use when the user asks about recent events, headlines, or news.

3. get_currency_rate — Returns the exchange rate between two currencies.
   Use when the user asks about currency conversion or exchange rates.

RULES:

- If the question needs multiple tools, call ALL relevant tools before answering.
- Combine the results into one clear, well-organized response.
- If a tool returns an error message, relay it to the user in a helpful way.
- NEVER invent or guess data. Only use information returned by the tools.
- If a city is not found, tell the user to check the spelling.
- If no news results are found, say so clearly.
- If the user asks something unrelated to weather, news, or currency,
  respond politely: explain that you can help with weather lookups,
  news searches, and currency exchange rates, and suggest how they
  might rephrase their question to use one of those tools.
- Keep answers concise but informative.
"""


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def create_agent(
    model_name: str = "gpt-4o-mini",
    temperature: float = 0.0,
    verbose: bool = False,
) -> AgentExecutor:
    """Build and return a ready-to-use LangChain agent.

    Args:
        model_name: OpenAI model to use (default: gpt-4o-mini).
        temperature: Sampling temperature. 0 = deterministic.
        verbose: Print the agent's reasoning steps if True.

    Returns:
        An AgentExecutor that can be called with .invoke({"input": "..."}).

    Raises:
        EnvironmentError: If OPENAI_API_KEY is not set.
    """
    load_dotenv()

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. "
            "Copy .env.example to .env and add your key."
        )

    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=openai_key,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, ALL_TOOLS, prompt)

    return AgentExecutor(
        agent=agent,
        tools=ALL_TOOLS,
        verbose=verbose,
        handle_parsing_errors=True,
        max_iterations=6,
    )
