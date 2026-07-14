from app.agents.llm_client import generate_llm_response

def run_technical_agent(query: str, history: list[dict], context: list[dict]) -> str:
    """Specialized Technical agent that handles device setups, Wi-Fi, resets, and errors."""
    context_str = "\n\n".join([f"Source: {c['source']} ({c['heading']})\nContent: {c['text']}" for c in context])
    history_str = ""
    for msg in history:
        role = "Customer" if msg["role"] == "user" else "Assistant"
        history_str += f"{role}: {msg['content']}\n"
        
    prompt = f"""You are the Technical Support Agent for TechMart Electronics.
You specialize in hardware setup, Wi-Fi pairing issues, factory resets, error codes, and troubleshooting the TechMart Smart Hub (Model SH-200).

Here is the context retrieved from the company documents:
{context_str}

Here is the conversation history:
{history_str}

Customer Query: {query}

Instructions:
1. Provide detailed, step-by-step troubleshooting instructions.
2. If the user is asking about connection issues or factory resets for the Smart Hub, reference the 10-second reset button procedure and LED lights (Blinking Blue = Pairing, Solid Blue = Online, Blinking Red = Lost Wi-Fi, Solid Red = Hardware Error).
3. If troubleshooting fails or the issue is not in the manuals, politely explain that we might need to process a warranty repair or escalate to senior support.
4. Be clear, encouraging, and easy to follow.

Answer:"""
    
    try:
        return generate_llm_response(prompt)
    except Exception as e:
        print(f"Technical Agent LLM call failed: {str(e)}")
        if context:
            docs_summary = "\n\n".join([f"- From {c['source']}: {c['text']}" for c in context])
            return f"I had trouble reaching the AI network, but here are the troubleshooting steps found in our manuals:\n\n{docs_summary}"
        return "I am currently having trouble reaching the technical support network. Please retry in a few seconds."