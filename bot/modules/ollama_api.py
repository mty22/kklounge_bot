from ollama import Client

class _Ollama:
    """Class for our custom Ollama queries"""
    def __init__(self):
        pass

    def ollama_query(ollama_url,ollama_key,ollama_model,payload):
        """Send query to Ollama API with data"""

        try:
            client = Client(
                host=ollama_url,
                headers={
                    "Authorization": f"Bearer {ollama_key}",
                    "Content-Type": "application/json",
                },
            )
        except Exception as e:
            return (f"Failed to connect to Ollama API: {e}")

        try:
            completion = client.chat(
                    model=ollama_model,
                    messages=payload
                )
            ai_message = completion.message.content
        except Exception as e:
            return (f"There was an error trying to generate a response: {e}")

        return ai_message
