"""Agent C: Stock Market Literature & Theory Knowledge Agent."""

import os
from openai import OpenAI


class AgentC:
    """Agent C retrieves trading principles citing a specific stock market book."""

    def __init__(self, book_title: str = "Technical Analysis of the Financial Markets by John J. Murphy") -> None:
        """Initializes Agent C with book reference.

        Args:
            book_title: Name of the textbook.
        """
        self.book_title = book_title
        self.client = OpenAI()

    def consult_book(self, topic: str, model: str = "gpt-4o-mini") -> str:
        """Asks the LLM to recall and explain trading rules strictly from the specified book.

        Args:
            topic: Technical pattern or indicator topic.
            model: OpenAI model name.

        Returns:
            The textbook interpretation and rules.
        """
        prompt = (
            f"You are Agent C, an authority on the book: '{self.book_title}'.\n"
            f"Using ONLY the principles taught in '{self.book_title}', "
            f"explain how to interpret: {topic}."
        )

        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"You are an expert tutor on '{self.book_title}'."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()


if __name__ == "__main__":
    agent = AgentC()
    print(agent.consult_book("Moving average crossover and volume confirmation"))
