import os
import sys
import json
from google import genai
from google.genai import types

# Add backend directory to sys path to resolve app imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app.config import settings
from app.rag.retriever import retriever
from app.agents.billing import run_billing_agent
from app.agents.technical import run_technical_agent
from app.agents.product import run_product_agent
from app.agents.complaint import run_complaint_agent
from app.agents.faq import run_faq_agent

# Initialize client using new SDK
client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Map string keys to execution functions
AGENT_MAPPING = {
    "billing": run_billing_agent,
    "technical": run_technical_agent,
    "product": run_product_agent,
    "complaint": run_complaint_agent,
    "faq": run_faq_agent
}

def route_query(query: str, history: list[dict]) -> list[str]:
    """Analyzes query + history and returns the list of agents needed."""
    history_str = ""
    for msg in history:
        role = "Customer" if msg["role"] == "user" else "Assistant"
        history_str += f"{role}: {msg['content']}\n"
        
    prompt = f"""You are the central orchestrator for a multi-agent customer support desk.
Your job is to analyze the customer's query and conversation history, and output a JSON list of specialized agent names that need to handle this query.

Specialized Agents:
- 'billing': handles payment issues, refunds, subscription charges, invoice problems, Premium Membership renewals.
- 'technical': handles hardware/software setup, Wi-Fi pairing issues, factory resets, blinking LEDs, error codes.
- 'product': handles specifications of models, comparing devices, sales pricing, stock availability, price matching.
- 'complaint': handles customers expressing frustration, anger, using caps, criticizing the product/service, demanding a manager.
- 'faq': handles general shipping options/rates, business hours, retail locations, contact phone numbers/emails.

Return a JSON list containing the names of the required agents. You can trigger one or multiple agents if the query covers multiple areas (e.g. billing charge + technical device failure).
Output ONLY a raw JSON array. Example: ["billing"] or ["technical", "billing"]. Do not add markdown formatting or wrapper tags.

Conversation History:
{history_str}

Customer Query: {query}

JSON Output:"""

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',  # Switched to 2.0-flash
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        cleaned_response = response.text.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
        
        agents = json.loads(cleaned_response)
        
        if isinstance(agents, list):
            valid_agents = [a for a in agents if a in AGENT_MAPPING]
            return valid_agents if valid_agents else ["faq"]
        return ["faq"]
    except Exception as e:
        print(f"Routing failed, defaulting to general FAQ. Error: {str(e)}")
        return ["faq"]

def aggregate_responses(query: str, history: list[dict], agent_responses: dict[str, str]) -> str:
    """Combines responses from multiple agents into a single, cohesive customer reply."""
    responses_str = ""
    for agent, resp in agent_responses.items():
        responses_str += f"### {agent.capitalize()} Agent Draft:\n{resp}\n\n"
        
    prompt = f"""You are the Senior Customer Support Coordinator at TechMart Electronics.
Your job is to read drafts written by specialized agents in response to a customer query, and combine them into a single, unified, coherent, and friendly customer reply.

Guidelines:
1. Merge the drafts naturally. Remove any repetitive greetings, standard disclaimers, or redundant sentences.
2. Ensure the tone is highly professional, polite, and helpful.
3. Make sure the transition between different topics (e.g. resolving a billing charge, then helping them reset their device) is smooth.
4. Keep the final response formatting clean using markdown.

Agent Response Drafts:
{responses_str}

Customer Query: {query}

Cohesive Response:"""

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',  # Switched to 2.0-flash
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Aggregation failed. Returning concatenated drafts. Error: {str(e)}")
        return "\n\n".join(agent_responses.values())

def process_customer_query(query: str, history: list[dict]) -> dict:
    """Main orchestrator function: Routes, retrieves context, executes agents, and aggregates results."""
    triggered_agents = route_query(query, history)
    print(f"Triggered Agents: {triggered_agents}")
    
    # Retrieve relevant context from RAG
    context = retriever.retrieve(query, top_k=5)
    
    # Execute each triggered agent
    agent_responses = {}
    for agent_name in triggered_agents:
        agent_fn = AGENT_MAPPING[agent_name]
        print(f"Running {agent_name} agent...")
        agent_responses[agent_name] = agent_fn(query, history, context)
        
    # Synthesize the final response
    if len(triggered_agents) == 1:
        final_response = agent_responses[triggered_agents[0]]
    else:
        print("Aggregating responses from multiple agents...")
        final_response = aggregate_responses(query, history, agent_responses)
        
    return {
        "response": final_response,
        "agents": triggered_agents,
        "retrieved_context": context
    }

if __name__ == "__main__":
    retriever.initialize()
    
    print("\n--- Test 1: Technical Query ---")
    res1 = process_customer_query("How do I reset my Smart Hub?", [])
    print(f"Final Reply:\n{res1['response']}")