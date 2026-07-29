import ollama

def generate_natural_answer(question: str, rows: list) -> str:
    response = ollama.chat(
        model="llama3.1",
        messages=[
            {"role": "user", "content": f"Question: {question}\nQuery result: {rows}\n"
                                          f"Answer in one clear, natural sentence using this data. "
                                          f"Do NOT paste raw image URLs in your answer - refer to products "
                                          f"by name; the app shows the images separately."}
        ]
    )
    return response['message']['content'].strip()