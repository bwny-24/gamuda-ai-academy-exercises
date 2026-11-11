import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, FewShotPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 1. Initialize FastAPI app
app = FastAPI()

# 3. Initialize your LangChain model and prompt template
llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash", api_key=GEMINI_API_KEY)

# 2. Define the Pydantic schema matching the Exercise request body
class TranslationRequest(BaseModel):
    input_language: str
    output_language: str
    text_input: str





# Allow cross-origin requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins during local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

### Introduction to LangChain ###

#region


# prompt = ChatPromptTemplate.from_messages(
#     [
#         (
#             "system",
#             "You are a helpful translator. Translate the given text from {input_language} to {output_language}."
#         ),
#         (
#             "human",
#             "{text_input}"
#         )
#     ]
# )

# # Build the LCEL chain
# chain = prompt | llm | StrOutputParser()

# # 4. Define the /translate POST endpoint
# @app.post("/translate")
# async def translate_text(request: TranslationRequest):
#     # Pass input from API request into your LangChain LCEL chain
#     translated = chain.invoke({
#         "input_language": request.input_language,
#         "output_language": request.output_language,
#         "text_input": request.text_input
#     })
    
#     # Return JSON body matching the required response schema: {"translated_text": "..."}
#     return {"translated_text": translated}


#endregion