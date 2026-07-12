from google import genai
from app.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def run_product_agent(query: str, history: list[dict], context: list[dict]) -> str:
    """Specialized Product agent that answers price-matching, availability, and specs, with fallback."""
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
    
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Product Agent Gemini call failed: {str(e)}")
        if context:
            docs_summary = "\n\n".join([f"- From {c['source']}: {c['text']}" for c in context])
            return f"I had trouble reaching the AI network, but here is what I found in our product catalogs:\n\n{docs_summary}"
        return "I am currently having trouble reaching the sales network. Please retry in a few seconds."