# AI Agent with External Tools — University Project

An AI agent built with **Python**, **LangChain**, and the **OpenAI GPT API** that
answers user questions by automatically selecting and calling external APIs.

The agent decides which tool to use based on the question, calls one or more
APIs, and combines the results into a single coherent answer.

---

## Assignment Alignment

This project satisfies the following requirements:

| Requirement                              | Status |
|------------------------------------------|--------|
| OpenAI GPT API as the LLM               | ✅      |
| LangChain agent with tool-calling        | ✅      |
| At least 2 external APIs as tools        | ✅      |
| Agent chooses tools automatically        | ✅      |
| Agent combines results from multiple tools | ✅    |
| Clean modular architecture               | ✅      |
| Error handling for all failure modes     | ✅      |

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  User Query                     │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│           LangChain Agent (ReAct)               │
│           LLM: OpenAI GPT-4o-mini               │
│                                                 │
│   The agent reads the query, decides which      │
│   tool(s) to call, and synthesizes a response.  │
└────────┬───────────────┬───────────────┬────────┘
         ▼               ▼               ▼
   ┌───────────┐   ┌───────────┐   ┌───────────────┐
   │  Weather  │   │   News    │   │   Currency    │
   │   Tool    │   │   Tool    │   │    Tool       │
   │(OpenWeath-│   │ (NewsAPI) │   │(ExchangeRate) │
   │ erMap)    │   │           │   │  [bonus]      │
   └─────┬─────┘   └─────┬─────┘   └──────┬────────┘
         ▼               ▼                ▼
    External API    External API     External API
         │               │                │
         └───────────────┴────────────────┘
                         ▼
                  Combined Answer
```

**How it works (ReAct pattern):**

1. The agent **reasons** about which tools are needed.
2. It **acts** by calling one or more tools.
3. It **observes** the returned data.
4. It **responds** with a unified answer combining all results.

---

## Tools / APIs Used

### Core Tools (required)

| Tool | API Provider | What It Does |
|------|-------------|--------------|
| `get_weather` | [OpenWeatherMap](https://openweathermap.org/api) | Returns current weather for any city (temperature, conditions, humidity, wind) |
| `get_news` | [NewsAPI](https://newsapi.org/) | Searches recent news articles by topic and returns headlines with sources |

### Bonus Tool (optional)

| Tool | API Provider | What It Does |
|------|-------------|--------------|
| `get_currency_rate` | [ExchangeRate-API](https://www.exchangerate-api.com/) | Returns the live exchange rate between two currencies |

The currency tool is included as a bonus to demonstrate that the agent can
scale to more than two tools. The core assignment functionality is fully
covered by the weather and news tools.

---

## Project Structure

```
├── README.md            Documentation (this file)
├── requirements.txt     Python dependencies
├── .env.example         Template for API keys
├── utils.py             HTTP helper, formatting, custom exceptions
├── tools.py             LangChain tool definitions (weather, news, currency)
├── agent.py             Agent creation with system prompt
└── demo.py              Demo script with example queries
```

---

## Setup

### 1. Prerequisites

- Python 3.10 or higher
- API keys (all services have free tiers):
  - [OpenAI](https://platform.openai.com/api-keys)
  - [OpenWeatherMap](https://home.openweathermap.org/api_keys)
  - [NewsAPI](https://newsapi.org/register)
  - [ExchangeRate-API](https://app.exchangerate-api.com/sign-up) *(optional, for bonus tool)*

### 2. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 3. Configure API keys

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder values with your real keys:

```
OPENAI_API_KEY=sk-...
WEATHER_API_KEY=your_key
NEWS_API_KEY=your_key
EXCHANGE_RATE_API_KEY=your_key    # optional
```

### 4. Run the demo

```bash
python demo.py
```

---

## Demo Queries

The demo script runs these queries to show different agent behaviors:

| # | Query | Expected Behavior |
|---|-------|-------------------|
| 1 | "What is the weather in London?" | Calls weather tool only |
| 2 | "Latest news about artificial intelligence" | Calls news tool only |
| 3 | "Weather in Tokyo and latest news about Japan" | Calls both tools, combines results |
| 4 | "What is the weather in Qwxyzville?" | Handles non-existent city gracefully |
| 5 | "Who painted the Mona Lisa?" | Politely explains this is outside tool scope |
| 6 | "USD to EUR exchange rate" | Calls currency tool (bonus) |

---

## Example Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Query 1: What is the weather in London?

Weather in London, GB:
  Conditions: Overcast clouds
  Temperature: 12.5°C (feels like 11.1°C)
  Humidity: 78%
  Wind: 4.2 m/s

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Query 4: What is the weather in Qwxyzville?

I couldn't find weather data for "Qwxyzville." The city may not exist or
could be misspelled. Please check the name and try again.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

*(Actual responses will vary based on live API data.)*

---

## Error Handling

The project handles the following failure cases:

- **City not found** — clear message asking user to check the spelling
- **API timeout** — friendly "service unavailable, try again" message
- **Missing API key** — tells user which key is missing
- **Empty results** — informs user that no data was found
- **Network failure** — reports connection issue
- **Unrelated question** — agent explains it can only help with weather, news, and currency

No unhandled exceptions will crash the program.

---

## Known Limitations

- **News language:** The news tool searches English-language articles by default.
  This is configurable via the `language` parameter in `tools.py` if needed.
- **Free API tiers:** OpenWeatherMap allows ~1000 calls/day, NewsAPI allows
  100 calls/day on the free plan. The demo uses a small number of calls.
- **Currency tool** requires a separate API key. If the key is not set, the
  tool returns a clear message and the agent continues working with the
  other tools.

---

