import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, FewShotPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash", api_key=GEMINI_API_KEY)


### Introduction to LangChain ###

#region
# messages = [
#     (
#         "system",
#         "tolong sa translate english to german ",
#     ),
#     (
#         "human",
#         "i love people with clean feet",
#     ),
# ]

# chain = llm | StrOutputParser()
# ai_msg = chain.invoke(messages)
# print(ai_msg)

# prompt = ChatPromptTemplate.from_messages(
#     [
#         (
#             "system",
#             "yo nazy, you gotta help me translate {input_language} to {output_language}."
#         ),
#         (
#             "human",
#             "{input}"
#         )
#     ]
    
# )

# chain = prompt | llm | StrOutputParser()

# """ ai_msg = chain.invoke({
#     "input_language": "Malay",
#     "output_language" : "Kelantan",
#     "input" : "Cuci kaki awak!"
# }) """

# ai_msg = chain.invoke({
#     "input_language": "german",
#     "output_language" : "chinese",
#     "input" : "Wascht eure Füße!"
# })

# print(ai_msg)

#endregion


### Introduction to Prompt Engineering ####
#region



# examples = [
#     {"review": "Great quality for reasonable price. Excellent!" , "sentiment": "Positive"},
#     {"review": "The beans were stale and bitter. Dissapointing", "sentiment": "Negative"},
#     {"review": "Standard medium roast coffee. Nothing special.", "sentiment": "Neutral"}
# ]

# example_prompt = PromptTemplate(
#     input_variables=["review", "sentiment"],
#     template="Coffee Review: {review}\nSentiment: {sentiment}"
# )

# prompt = FewShotPromptTemplate(
#     examples=examples,
#     example_prompt = example_prompt,
#     prefix = "Analyze the coffee review sentiment. \nRespond with ONLY ONE WORD: Positive, Negative, Mixed, or Neutral.\n",
#     suffix="Coffee Review: {input}\nSentiment:",
#     input_variables=["input"]
# )

# chain = prompt | llm | StrOutputParser()

# print("Coffee Review Sentiment Analyzer (type 'quit' to exit)")
# while True: 
#     review = input("Enter coffee review: ").strip()
#     if not review:
#         continue
#     if review.lower()=='quit':
#         break
#     try: 
#         response = chain.invoke({"input": review})
#         print(response.strip())
#     except Exception as e:
#         print(f"Error: {e}")

# print("\nProgram ended")



# Question: 11 factories can make 22 cars per hour. How much time would it take 22 factories to make 88 cars?
# Answer: Let me solve this step by step:
# 1. A factory can make 22/11=2 cars per hour.
# 2. 22 factories can make 22*2=44 cars per hour.
# 3. Making 88 cars would take 88/44=2 hours.

prompt_template = """

Therefore, the answer is 2 hours.

Now, solve this new problem using the same step-by-step approach:
Question: {question}
Answer:
"""

prompt = PromptTemplate(
    input_variables=["question"],
    template=prompt_template
)

chain = prompt | llm | StrOutputParser()

def solve_math_problem(problem):
    try:
        response = chain.invoke({"question": problem})
        print(f"Problem: {problem}\n")
        print(f"Solution:\n{response}\n")
        print("-" * 50 + "\n")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

new_problem = """5 people can create 5 donuts every 5 minutes.
How much time would it take 25 people to make 100 donuts?
Return the answer immediately."""

solve_math_problem(new_problem)

#endregion
