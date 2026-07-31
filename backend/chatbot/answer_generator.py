import os
from ollama import Client

# Cloud, not local - matches sql_generator.py. This used to call a local
# Ollama daemon (llama3.1), which only worked on machines that happened to
# have one running; moving to Ollama Cloud removes that dependency entirely,
# so the answer step works anywhere the SQL-generation step already does.
client = Client(
    host="https://ollama.com",
    headers={"Authorization": "Bearer " + os.getenv("OLAMA_API_KEY", "")},
)


def generate_natural_answer(question: str, rows: list) -> str:
    response = client.chat(
        model="gpt-oss:120b-cloud",
        messages=[
            {"role": "user", "content": f"Question: {question}\nQuery result: {rows}\n"
                                          f"Answer in one clear, natural sentence using this data. "
                                          f"Do NOT paste raw image URLs in your answer - refer to products "
                                          f"by name; the app shows the images separately."}
        ]
    )
    return response.message.content.strip()
