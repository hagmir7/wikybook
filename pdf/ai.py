import openai

def book_content_ai(book):
    prompt = f"""Give me a long description about this book '{book.name}' by {book.author}. 
            Please follow these guidelines:

            1. Use html format.
            3. Use <strong>bold</strong> for important words or phrases.
            4. Include a brief introduction, main themes, key points
            6. Ensure the content is SEO-friendly with relevant keywords (Don't use h1, Don't use EO-friendly word in the content).
            
            7. Content must be as long as posible 
            8. Add Human Touch to the content
            9. the content most be with this language ({book.language.name})
            Please don't make mstiks return just a result no anothor text
        """
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that give books info for our site, Please don't make mestiks ",
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content
