from google import genai
from app.config import settings

# Initialize client using new SDK
client = genai.Client(api_key=settings.GEMINI_API_KEY)

def run_billing_agent(query: str, history: list[dict], context: list[dict]) -> str:
    """Specialized Billing agent that answers queries using RAG context and memory."""
    context_str = "\n\n".join([f"Source: {c['source']} ({c['heading']})\nContent: {c['text']}" for c in context])
    
    history_str = ""
    for msg in history:
        role = "Customer" if msg["role"] == "user" else "Assistant"
        history_str += f"{role}: {msg['content']}\n"
        
    prompt = f"""You are the Billing Support Agent for TechMart Electronics.
You specialize in resolving payment issues, refunds, subscription charges, invoices, and Premium Membership queries.

Here is the context retrieved from the company documents:
{context_str}

Here is the conversation history:
{history_str}

Customer Query: {query}

Instructions:
1. Provide accurate, helpful, and concise answers using only the provided context.
2. If you are discussing refunds, mention the 30-day return window (60 days for Premium members), the 10% restocking fee on PCs/laptops/TVs/cameras, and refund timelines (credit card: 5-7 days, PayPal: 1-2 days).
3. If the answer cannot be found in the context, politely state that you don't have that specific information and offer to escalate to a billing supervisor.
4. Maintain a professional, polite tone. Do not make up any policies.

Answer:"""
    
    # Use client.models.generate_content
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=prompt
    )
    return response.text.strip()