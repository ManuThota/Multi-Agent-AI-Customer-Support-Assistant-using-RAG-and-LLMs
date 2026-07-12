from google import genai
from app.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def run_product_agent(query: str, history: list[dict], context: list[dict]) -> str:
    """Specialized Product agent that answers price-matching, availability, and specs."""
    context_str = "\n\n".join([f"Source: {c['source']} ({c['heading']})\nContent: {c['text']}" for c in context])
    history_str = ""
    for msg in history:
        role = "Customer" if msg["role"] == "user" else "Assistant"
        history_str += f"{role}: {msg['content']}\n"
        
    prompt = f"""You are the Product & Sales Agent for TechMart Electronics.
You specialize in product features, pricing, model comparisons, stock availability, and our Price Match Guarantee.

Here is the context retrieved from the company documents:
{context_str}

Here is the conversation history:
{history_str}

Customer Query: {query}

Instructions:
1. Enthusiastically explain product features, specifications, and pricing.
2. For Price Match Guarantee questions, specify the 14-day window for identical in-stock items from authorized competitors, and exclusions (clearance, open-box, auction sites).
3. Help the customer choose the right product based on their needs.
4. Keep the tone helpful, commercial, and clear.

Answer:"""
    
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=prompt
    )
    return response.text.strip()