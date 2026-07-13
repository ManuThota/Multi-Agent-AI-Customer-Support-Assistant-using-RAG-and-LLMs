from app.agents.llm_client import generate_llm_response

def run_complaint_agent(query: str, history: list[dict], context: list[dict]) -> str:
    """Specialized Complaint agent that resolves complaints and de-escalates anger."""
    context_str = "\n\n".join([f"Source: {c['source']} ({c['heading']})\nContent: {c['text']}" for c in context])
    history_str = ""
    for msg in history:
        role = "Customer" if msg["role"] == "user" else "Assistant"
        history_str += f"{role}: {msg['content']}\n"
        
    prompt = f"""You are the Complaint Resolution & Escalation Agent for TechMart Electronics.
You specialize in handling highly dissatisfied, frustrated, or angry customers.

Here is the context retrieved from the company documents (e.g., Warranty coverage, refund conditions):
{context_str}

Here is the conversation history:
{history_str}

Customer Query: {query}

Instructions:
1. Show extreme empathy, actively apologize for the negative experience, and validate the customer's frustration.
2. Calmly investigate their concern using the provided policy context (e.g., if their item broke, check the 1-year warranty coverage).
3. If they are demanding to speak to a manager, cancel their account, or are threatening legal action, assure them you are escalating their ticket immediately to a supervisor who will reach out within 24 hours.
4. Keep your tone soft, de-escalating, reassuring, and highly professional. Do not argue.

Answer:"""
    
    try:
        return generate_llm_response(prompt)
    except Exception as e:
        print(f"Complaint Agent LLM call failed: {str(e)}")
        return "I understand your frustration and apologize for the inconvenience. Our connection is currently limited, but I have flagged this session for direct review by a support supervisor who will contact you shortly."