from app.agents.llm_client import generate_llm_response

def run_faq_agent(query: str, history: list[dict], context: list[dict]) -> str:
    """Specialized FAQ agent that replies to basic business operational details."""
    context_str = "\n\n".join([f"Source: {c['source']} ({c['heading']})\nContent: {c['text']}" for c in context])
    history_str = ""
    for msg in history:
        role = "Customer" if msg["role"] == "user" else "Assistant"
        history_str += f"{role}: {msg['content']}\n"
        
    prompt = f"""You are the General FAQ & Policy Agent for TechMart Electronics.
You specialize in general company details: business hours, locations, phone support numbers, email contacts, and shipping options/rates.

Here is the context retrieved from the company documents:
{context_str}

Here is the conversation history:
{history_str}

Customer Query: {query}

Instructions:
1. Provide concise, direct answers regarding basic company operations and logistics.
2. Clearly state shipping options (Standard: free over $50, otherwise $4.99; Express: $12.99; Overnight: $24.99) and store hours/locations if asked.
3. Be professional and brief.

Answer:"""
    
    try:
        return generate_llm_response(prompt)
    except Exception as e:
        print(f"FAQ Agent LLM call failed: {str(e)}")
        if context:
            docs_summary = "\n\n".join([f"- From {c['source']}: {c['text']}" for c in context])
            return f"I had trouble reaching the AI network, but here is what I found in our policies:\n\n{docs_summary}"
        return "I am currently having trouble reaching the support network. Please contact support@techmartelectronics.com."