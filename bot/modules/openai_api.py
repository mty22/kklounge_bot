from openai import OpenAI

class _OpenAI:
    """Class for our custom OpenAI queries"""
    def __init__(self):
        pass

    def openai_query(openai_url,openai_key,openai_model,payload):
        """Send query to OpenAI API with data"""

        try:
            client = OpenAI(api_key=openai_key, base_url=openai_url)
        except Exception as e:
            return (f"Failed to connect to OpenAI API: {e}")

        try:
            completion = client.chat.completions.create(
                        model=openai_model,
                        messages=payload,
                    )
            ai_message = completion.choices[0].message.content
        except Exception as e:
            return (f"There was an error trying to generate a response: {e}")

        return ai_message
