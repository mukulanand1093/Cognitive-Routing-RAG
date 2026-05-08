import os
from typing import TypedDict

from dotenv import load_dotenv

from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from langgraph.graph import StateGraph, END

from pydantic import BaseModel


# =========================================================
# LOAD ENV VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# INITIALIZE GROQ LLM
# =========================================================

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7
)


# =========================================================
# BOT PERSONA
# =========================================================

BOT_PERSONA = """
You are Bot A.

You are a radical tech maximalist.

You strongly believe AI, crypto, and technology
will solve humanity's biggest problems.

You admire Elon Musk, startups, innovation,
space exploration, and disruptive technology.

You dismiss excessive regulation and pessimism.

Your writing style:
- Aggressive
- Confident
- Opinionated
- Twitter/X style
- Under 280 characters
"""


# =========================================================
# MOCK SEARCH TOOL
# =========================================================

@tool
def mock_searxng_search(query: str) -> str:
    """
    Mock web search tool returning recent headlines.
    """

    query = query.lower()

    if "ai" in query:
        return """
        OpenAI launches autonomous software engineering agents.
        Google releases next-generation Gemini model.
        AI startups receive record-breaking funding in 2026.
        """

    elif "crypto" in query:
        return """
        Bitcoin hits new all-time high amid ETF approvals.
        Ethereum scaling upgrades reduce transaction costs.
        Major banks expand crypto trading infrastructure.
        """

    elif "market" in query or "finance" in query:
        return """
        Federal Reserve signals possible interest rate cuts.
        Tech stocks rally after strong AI earnings reports.
        Hedge funds increase AI-related investments.
        """

    elif "space" in query:
        return """
        SpaceX announces next Mars mission timeline.
        Reusable rocket launches reduce space travel costs.
        Private space investment continues accelerating.
        """

    return """
    Global technology investments continue growing rapidly.
    """


# =========================================================
# LANGGRAPH STATE
# =========================================================

class GraphState(TypedDict):

    persona: str

    topic: str

    search_results: str

    final_output: dict


# =========================================================
# STRUCTURED OUTPUT MODEL
# =========================================================

class PostOutput(BaseModel):

    bot_id: str

    topic: str

    post_content: str


# =========================================================
# NODE 1 — DECIDE SEARCH
# =========================================================

def decide_search(state: GraphState):

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            You are deciding what topic to post about today.

            Based on the bot persona,
            generate ONLY a short search query.

            Examples:
            - latest AI breakthroughs
            - crypto ETF adoption
            - AI regulation debate
            - space exploration innovation

            Return ONLY the search query.
            """
        ),
        (
            "human",
            f"""
            Persona:
            {state['persona']}
            """
        )
    ])

    chain = prompt | llm

    response = chain.invoke({})

    topic = response.content.strip()

    print("\n" + "=" * 60)
    print("[NODE 1 — DECIDE SEARCH]")
    print("=" * 60)

    print(f"\nGenerated Topic:\n{topic}")

    return {
        "topic": topic
    }


# =========================================================
# NODE 2 — WEB SEARCH
# =========================================================

def web_search(state: GraphState):

    topic = state["topic"]

    results = mock_searxng_search.invoke(topic)

    print("\n" + "=" * 60)
    print("[NODE 2 — WEB SEARCH]")
    print("=" * 60)

    print(f"\nSearch Query:\n{topic}")

    print(f"\nSearch Results:\n{results}")

    return {
        "search_results": results
    }


# =========================================================
# NODE 3 — DRAFT POST
# =========================================================

def draft_post(state: GraphState):

    structured_llm = llm.with_structured_output(PostOutput)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            You are generating a highly opinionated
            social media post.

            Rules:
            - Stay fully in character
            - Strong opinions
            - Under 280 characters
            - Twitter/X style
            - Sound human and confident
            - Do NOT be polite or neutral

            Return valid structured JSON output.
            """
        ),
        (
            "human",
            f"""
            PERSONA:
            {state['persona']}

            TOPIC:
            {state['topic']}

            SEARCH RESULTS:
            {state['search_results']}

            Generate the final post.
            """
        )
    ])

    chain = prompt | structured_llm

    response = chain.invoke({})

    print("\n" + "=" * 60)
    print("[NODE 3 — DRAFT POST]")
    print("=" * 60)

    print("\nGenerated Structured Output:\n")

    print(response.model_dump())

    return {
        "final_output": response.model_dump()
    }


# =========================================================
# BUILD LANGGRAPH WORKFLOW
# =========================================================

workflow = StateGraph(GraphState)

workflow.add_node("decide_search", decide_search)

workflow.add_node("web_search", web_search)

workflow.add_node("draft_post", draft_post)

workflow.set_entry_point("decide_search")

workflow.add_edge("decide_search", "web_search")

workflow.add_edge("web_search", "draft_post")

workflow.add_edge("draft_post", END)

app = workflow.compile()


# =========================================================
# RUN WORKFLOW
# =========================================================

if __name__ == "__main__":

    print("\nSTARTING LANGGRAPH WORKFLOW...\n")

    result = app.invoke({

        "persona": BOT_PERSONA

    })

    print("\n" + "=" * 60)
    print("FINAL OUTPUT")
    print("=" * 60)

    print("\nFinal JSON Output:\n")

    print(result["final_output"])

    print("\nWORKFLOW COMPLETED SUCCESSFULLY.\n")