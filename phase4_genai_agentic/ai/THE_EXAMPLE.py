import os, sys, base64, time, ast, operator, asyncio, logging
import requests
import streamlit as st
from datetime import date
from io import BytesIO
from typing import Annotated, List, Dict, Any
from pypdf import PdfReader
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
)
from langchain_core.messages import HumanMessage, AIMessage
from langchain.tools import tool
from langchain.agents import create_agent
from tavily import TavilyClient
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import (
    CommaSeparatedListOutputParser,
    JsonOutputKeyToolsParser,
    StrOutputParser,
)
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langchain.agents.middleware import ModelFallbackMiddleware, ModelRetryMiddleware
from langchain_mcp_adapters.client import MultiServerMCPClient


app = FastAPI()

load_dotenv()
GEMINI_FLASH_LITE_MODEL = "gemini-3.5-flash-lite"
INPUT_PLACEHOLDER = "{input}"
UVICORN_APP_COMMAND = "uvicorn THE_EXAMPLE:app --reload"
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# ==========================================
# Intro A: Introduction to LangChain (messages straight to the model)
# ==========================================
# Example and exercise from the early slides
#region
def run_intro_a():
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        api_key=os.getenv("GEMINI_API_KEY")
    )

    messages = [
        (
            "system",
            "tolong sa translate english to german ",
        ),
        (
            "human",
            "i love people with clean feet",
        ),
    ]

    chain = llm | StrOutputParser()
    ai_msg = chain.invoke(messages)
    print(ai_msg)
#endregion

# ==========================================
# Intro B: Introduction to LangChain (prompt template with variables)
# ==========================================
#region
def run_intro_b():
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        api_key=os.getenv("GEMINI_API_KEY")
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "yo nazy, you gotta help me translate {input_language} to {output_language}."
            ),
            (
                "human",
                INPUT_PLACEHOLDER
            )
        ]
    )

    chain = prompt | llm | StrOutputParser()

    # Same chain, different values: try "Malay" -> "Kelantan" with "Cuci kaki awak!"
    ai_msg = chain.invoke({
        "input_language": "german",
        "output_language": "chinese",
        "input": "Wascht eure Füße!"
    })

    print(ai_msg)
#endregion

# ==========================================
# Intro C: Prompt Engineering, Few-Shot (Coffee Review Sentiment)
# ==========================================
#region
def run_intro_c():
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        api_key=os.getenv("GEMINI_API_KEY")
    )

    examples = [
        {"review": "Great quality for reasonable price. Excellent!", "sentiment": "Positive"},
        {"review": "The beans were stale and bitter. Dissapointing", "sentiment": "Negative"},
        {"review": "Standard medium roast coffee. Nothing special.", "sentiment": "Neutral"}
    ]

    example_prompt = PromptTemplate(
        input_variables=["review", "sentiment"],
        template="Coffee Review: {review}\nSentiment: {sentiment}"
    )

    prompt = FewShotPromptTemplate(
        examples=examples,
        example_prompt=example_prompt,
        prefix="Analyze the coffee review sentiment. \nRespond with ONLY ONE WORD: Positive, Negative, Mixed, or Neutral.\n",
        suffix="Coffee Review: {input}\nSentiment:",
        input_variables=["input"]
    )

    chain = prompt | llm | StrOutputParser()

    print("Coffee Review Sentiment Analyzer (type 'quit' to exit)")
    while True:
        review = input("Enter coffee review: ").strip()
        if not review:
            continue
        if review.lower() == "quit":
            break
        try:
            response = chain.invoke({"input": review})
            print(response.strip())
        except Exception as e:
            print(f"Error: {e}")

    print("\nProgram ended")
#endregion

# ==========================================
# Intro D: Prompt Engineering, Chain of Thought (Math Problem)
# ==========================================
#region
def run_intro_d():
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        api_key=os.getenv("GEMINI_API_KEY")
    )

    # Chain of thought: the worked example must be INSIDE the prompt, or the model never sees it.
    prompt_template = """
Question: 11 factories can make 22 cars per hour. How much time would it take 22 factories to make 88 cars?
Answer: Let me solve this step by step:
1. A factory can make 22/11=2 cars per hour.
2. 22 factories can make 22*2=44 cars per hour.
3. Making 88 cars would take 88/44=2 hours.

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

    new_problem = """5 people can create 5 donuts every 5 minutes.
How much time would it take 25 people to make 100 donuts?
Return the answer immediately."""

    try:
        response = chain.invoke({"question": new_problem})
        print(f"Problem: {new_problem}\n")
        print(f"Solution:\n{response}\n")
        print("-" * 50 + "\n")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
#endregion

# ==========================================
# Exercise 1: Comma Separated List Parser
# ==========================================
#region
def run_exercise_1():
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        api_key=os.getenv("GEMINI_API_KEY")
    )

    output_parser = CommaSeparatedListOutputParser()

    chat_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant"),
            ("human", "{request}\n{format_instructions}")
        ]
    )

    chain = chat_prompt | llm | output_parser

    ai_msg = chain.invoke(
        {
            "request": "Give me 5 characteristics of a Donald Trump",
            "format_instructions": output_parser.get_format_instructions()
        }
    )

    print(output_parser.get_format_instructions())
    print("\n")
    print(ai_msg)
#endregion

# ==========================================
# Exercise 2: Chat with Conversation History
# ==========================================

#region
def run_exercise_2():
    llm = ChatGoogleGenerativeAI(
        model="gemma-4-26b-a4b-it",
        temperature=2.0,
        top_p=0.95,
        top_k=100,
        api_key=os.getenv("GEMINI_API_KEY")
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. Answer all questions to the best of your ability."),
        MessagesPlaceholder(variable_name="history"),
        ("human", INPUT_PLACEHOLDER),
    ])

    chain = prompt | llm | StrOutputParser()
    history = []

    print("\nStarting chat... Type 'quit' or 'exit' to end the conversation.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit"]:
            break
        if not user_input.strip():
            print("Please enter a message.")
            continue

        try:
            response = chain.invoke({"input": user_input, "history": history})
            history.append(HumanMessage(content=user_input))
            history.append(AIMessage(content=response))
            print(f"AI: {response}")
        except Exception as e:
            print(f"An error occurred: {e}")

    print("\nChat ended.")

    print("\n" + "=" * 30 + " Conversation History " + "=" * 30)
    for msg in history:
        print(f"{'Human' if msg.type == 'human' else 'AI'}: {msg.content}")
#endregion

# ==========================================
# Exercise 3: Thinking Level Parameter
# ==========================================
#region
def run_exercise_3():
    THINKING_LEVEL = "low"

    llm = ChatGoogleGenerativeAI(
        model=GEMINI_FLASH_LITE_MODEL,
        google_api_key=os.getenv("GEMINI_API_KEY"),
        thinking_level=THINKING_LEVEL
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant."),
        ("human", "{question}")
    ])

    chain = prompt | llm | StrOutputParser()

    response = chain.invoke({
        "question": "Provide a list of 3 famous physicists and their key contributions."
    })

    print(f"Thinking Level : {THINKING_LEVEL}")
    print(f"Response : \n{response}")

#endregion

# ==========================================
# Exercise 4: Text Summarization (Webpage)
# ==========================================
#region
def run_exercise_4():
    THINKING_LEVEL = "medium"
    
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_FLASH_LITE_MODEL,
        google_api_key=os.getenv("GEMINI_API_KEY"),
        thinking_level=THINKING_LEVEL
    )
    
    llm_with_url = llm.bind_tools([{"url_context": {}}])
    
    # URL wrapped in quotes
    URL = "https://www.msn.com/-my/technology/artificial-intelligence/nvidia-boss-criticises-cheap-ai-doomsday-warnings/ar-AA2fOTyT?ocid=msedgntp&pc=LCTS&cvid=6adabc10f91f40ae810593160d1a566d&ei=14"
    
    # Define the chain before invoking it
    chain = llm_with_url | StrOutputParser()
    
    print(f"Fetching and summarizing content from: {URL}\n...")
    
    response = chain.invoke([
        HumanMessage(content=f"Write a concise summary of this page: {URL}")
    ])

    print("\nSummary:")
    print(response)
#endregion

# ==========================================
# Exercise 5: Introduction of Text Summarization
# ==========================================
#region

# Define the PDF reading helper and route globally
def read_pdf_file(file_contents: BytesIO) -> str:
    try:
        pdf_reader = PdfReader(file_contents)
        return "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {e}")

@app.post("/summarize", responses={
    400: {"description": "Invalid PDF upload or unreadable PDF"},
    500: {"description": "Error summarizing the document"},
})
async def summarize_pdf(file: Annotated[UploadFile, File(...)]):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    contents = await file.read()
    text = read_pdf_file(BytesIO(contents))
    if not text.strip():
        raise HTTPException(status_code=400, detail="No readable text found.")
    
    try:
        # Re-instantiate or use global chain here
        llm = ChatGoogleGenerativeAI(model=GEMINI_FLASH_LITE_MODEL, api_key=os.getenv("GEMINI_API_KEY"))
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that summarizes documents."),
            ("human", "Write a concise summary of the following document:\n\n{text}\n\nCONCISE SUMMARY:"),
        ])
        chain = prompt_template | llm | StrOutputParser()
        summary = await chain.ainvoke({"text": text})
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="An error occured while summarizing the document.")
    
    return {"summary": summary}

def run_exercise_5():
    print("To run this FastAPI endpoint, use Uvicorn in your terminal:")
    print(UVICORN_APP_COMMAND)

#endregion

# ==========================================
# Exercise 6: LLM and Image Analytics
# ==========================================
#region

def encode_image(image_content: bytes) -> str:
    return base64.b64encode(image_content).decode()

@app.post(
    "/analyze-image",
    responses={
        400: {"description": "Invalid image type or image is too large."},
        500: {"description": "Error analyzing the uploaded image."},
    },
)
async def analyze_image(file: Annotated[UploadFile, File(...)]) -> dict:
    if not file.content_type or file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="tia bole bukan JPEG atau PNG ni.")

    contents = await file.read()

    if len(contents) > 10_000_000:
        raise HTTPException(status_code=400, detail="telampau basar file kau. Maximum size is 10mb.")

    image = encode_image(contents)
    
    # Moved the LLM instantiation INSIDE the endpoint so it is accessible
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_FLASH_LITE_MODEL,
        api_key=os.getenv("GEMINI_API_KEY"),
    )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a nutrition expert capable of analyzing food images and providing detailed nutritional advice.",
        ),
        (
            "human",
            [
                {
                    "type": "text",
                    "text": """Analyze the image and provide a comprehensive nutritional breakdown and health advice. Follow these steps:
                    1. Identify the food items: List all visible ingredients and dishes in the image.
                    2. Let me know how can I ask my wife nicely to cook me this.
                    3. What should I tell her if its not delicoeus without getting shot.
                    """,
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{file.content_type};base64,{image}",
                    },
                },
            ],
        ),
    ])
    
    try:
        chain = prompt | llm | StrOutputParser()
        res = await chain.ainvoke({})
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail="masalah oi")

    return {"analysis": res}

def run_exercise_6():
    print("This is a FastAPI endpoint.")
    print("To run the server, use Uvicorn in your terminal:")
    print(UVICORN_APP_COMMAND)
    print("Then send a POST request to http://127.0.0.1:8000/analyze-image with your image file.")

#endregion

# ==========================================
# Exercise 7: Introduction to Streamlit
# ==========================================
#region

def run_exercise_7():
    print("To run this Streamlit app, you must use this command in your terminal:")
    print("streamlit run THE_EXAMPLE.py")
    
    # If running via streamlit, the code below will execute on the web page.
    # We use a check to prevent Streamlit from running inside the basic terminal menu.
    import sys
    if "streamlit" not in sys.argv[0]:
        return

    llm = ChatGoogleGenerativeAI(
        model=GEMINI_FLASH_LITE_MODEL,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant that can describe images."),
            ("human",
                [
                    {"type": "text", "text": INPUT_PLACEHOLDER},
                    {
                        "type": "image_url",
                        "image_url":{
                            "url": "data:{mime_type};base64,{image}", # Fixed typo here
                        },
                    },
                ],
            ),
        ]
    )

    chain = prompt | llm | StrOutputParser()

    st.title("Gemini Check Gambal")

    col1, col2 = st.columns(2)

    with col1:
        uploaded_file = st.file_uploader("Upload your image", type=["jpg", "png"])
        
    with col2:
        if uploaded_file is not None:
            image_bytes = uploaded_file.read()
            st.image(image_bytes)
        else:
            st.write("Image Preview")
            
    question = st.text_input("Enter a question")

    if question and uploaded_file is not None:
        image_b64 = base64.b64encode(image_bytes).decode()
        res = chain.invoke({"input": question, "image": image_b64, "mime_type": uploaded_file.type})
        st.write(res)
        
#endregion

# ==========================================
# Exercise 8: KYC Verification App (Streamlit)
# ==========================================
#region

def run_exercise_8():
    print("To run this Streamlit app, you must use this command in your terminal:")
    print("streamlit run THE_EXAMPLE.py")
    
    # Prevent Streamlit UI from loading in the terminal menu
    import sys
    if "streamlit" not in sys.argv[0]:
        return

    # Initialize LLM locally for this exercise
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_FLASH_LITE_MODEL,
        api_key=os.getenv("GEMINI_API_KEY")
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that can verify identification documents"),
        ("human", [
            {"type": "text", "text": "Verify the identification details"},
            {"type": "text", "text": "Name: {user_name}"},
            {"type": "text", "text": "DOB: {user_dob}"},
            {
                "type": "image_url",
                "image_url": {
                    "url": "data:{mime_type};base64,{image}",
                },
            },
        ]),
    ])

    chain = prompt | llm | StrOutputParser()

    st.title("KYC Verification Application")

    col1, col2 = st.columns(2)

    with col1:
        uploaded_file = st.file_uploader("Upload your ID document", type=["jpg", "png"])

    with col2:
        if uploaded_file is not None:
            image_bytes = uploaded_file.read()
            st.image(image_bytes)
        else:
            st.write("Image Preview")

    user_name = st.text_input("Enter your name")
    user_dob = st.date_input("Enter your date of birth", min_value=date(1900, 1, 1))

    if uploaded_file is not None and user_name and user_dob:
        image = base64.b64encode(image_bytes).decode()
        
        # Invoke the chain with the user inputs and formatted image
        res = chain.invoke({
            "user_name": user_name,
            "user_dob": user_dob,
            "image": image,
            "mime_type": uploaded_file.type
        })
        
        st.write(res)

#endregion

# ==========================================
# Exercise 9: Create Vector Store (MongoDB Atlas)
# ==========================================

#region
# Kept at module level so later exercises (adding docs, searching) can reuse it.
_base = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    output_dimensionality=768,  # must match the Atlas index
)

class PrefixedEmbeddings(Embeddings):
    """gemini-embedding-2 reads the task from a prefix."""

    def embed_documents(self, texts):
        return _base.embed_documents(
            [f"title: none | text: {t}" for t in texts]
        )

    def embed_query(self, text):
        return _base.embed_query(
            f"task: search result | query: {text}"
        )

embeddings = PrefixedEmbeddings()

#endregion

# --- example 1 part: create the vector store ---
#region
DB_NAME = "test_db"
COLLECTION_NAME = "test_collection"
ATLAS_VECTOR_SEARCH_INDEX_NAME = "test-index-1"

def run_exercise_9():
    MONGODB_URI = os.getenv("MONGODB_ATLAS_CLUSTER_URI")

    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    MONGODB_COLLECTION = client[DB_NAME][COLLECTION_NAME]

    # Instantiate the vector store
    vector_store = MongoDBAtlasVectorSearch(
        collection=MONGODB_COLLECTION,
        embedding=embeddings,
        index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
        relevance_score_fn="cosine",
    )

    # Create the vector search index
    print("Creating vector search index...")
    vector_store.create_vector_search_index(
        dimensions=768, wait_until_complete=60
    )
    print("Vector Store Created!")

    client.close()

#endregion

# ==========================================
# Exercise 10: Store the Embeddings(MongoDB Atlas)
# ==========================================
#region

# facts.txt sits next to this script, so it is found no matter where you run from
FACTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "facts.txt")

# Load the text file as one Document
def load_text_document(file_path: str) -> list[Document]:
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return [Document(page_content=text, metadata={"source": file_path})]

def run_exercise_10():
    MONGODB_URI = os.getenv("MONGODB_ATLAS_CLUSTER_URI")

    client = MongoClient(MONGODB_URI)
    MONGODB_COLLECTION = client[DB_NAME][COLLECTION_NAME]

    vector_store = MongoDBAtlasVectorSearch(
        collection=MONGODB_COLLECTION,
        embedding=embeddings,
        index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
        relevance_score_fn="cosine",
    )

    # Start clean: re-embed everything on each run
    MONGODB_COLLECTION.delete_many({})
    print("Previous documents cleared")

    docs = load_text_document(FACTS_FILE)

    # Split into chunks of about 200 characters
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=200,
        chunk_overlap=0,
    )
    split_docs = text_splitter.split_documents(docs)

    # Add the chunks to the vector store
    print("Adding documents...")
    vector_store.add_documents(split_docs)
    print(f"Documents Added ({len(split_docs)} chunks)")

    client.close()

#endregion

# ==========================================
# Exercise 11: Perform the Query (RAG)
# ==========================================
#region
# STEP 0: IMPORTS -> added RunnablePassthrough at the top of the file.
#         Skipped `load_dotenv()` and `from embeddings import embeddings` (already in this file).
#
# STEP 1: SHARED STUFF (outside the function)
#   Reusing from Exercise 9: DB_NAME, COLLECTION_NAME, ATLAS_VECTOR_SEARCH_INDEX_NAME, embeddings

# Merge the retrieved chunks into one string, so it can be pasted into {context}
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# STEP 2: THE FUNCTION
def run_exercise_11():
    # 2a. Setup: LLM + MongoDB connection + vector store (same as Exercise 10)
    # Using the lite model: "gemini-3.8-flash" (the slide's model) was returning 503 "high demand"
    llm = ChatGoogleGenerativeAI(model=GEMINI_FLASH_LITE_MODEL, api_key=os.getenv("GEMINI_API_KEY"))

    client = MongoClient(os.getenv("MONGODB_ATLAS_CLUSTER_URI"))
    MONGODB_COLLECTION = client[DB_NAME][COLLECTION_NAME]

    vector_store = MongoDBAtlasVectorSearch(
        collection=MONGODB_COLLECTION,
        embedding=embeddings,
        index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
        relevance_score_fn="cosine",
    )

    # 2b. The new part: retriever + prompt + RAG chain
    # Retriever = a "search box" over the vector store. k=3 returns the top 3 most relevant chunks
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    # System prompt: tell the AI to answer ONLY from the retrieved context
    system_prompt = (
        """
        You are a helpful assistant that answers questions using ONLY the context below.
        If the answer is not in the context, say "I don't know based on the provided facts."
        Do not use any outside knowledge.
        CONTEXT:\n{context}
        """
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", INPUT_PLACEHOLDER),
    ])

    # Prepare the inputs for the prompt:
    #   "context" -> question goes into the retriever, the found chunks go into format_docs
    #   "input"   -> RunnablePassthrough() passes the question through unchanged
    setup_and_retrieval = {
        "context": retriever | format_docs,
        "input": RunnablePassthrough(),
    }

    # Retrieve -> build the prompt -> call the LLM -> parse the text
    rag_chain = setup_and_retrieval | prompt | llm | StrOutputParser()

    # 2c. Show the result
    print("Querying Vector DB...")
    response = rag_chain.invoke("What animal should I get if I want a pet that is low maintenance and doesn't require much attention?")
    print(f"\nAI Response: {response}")

    # 2d. Clean up
    client.close()

# STEP 3: menu line added in EXERCISES below.



#endregion

# ==========================================
# Exercise 12: Create PDF Vector Store (MongoDB Atlas)
# ==========================================
#region
# STEP 0: IMPORTS -> nothing new, MongoClient / MongoDBAtlasVectorSearch / embeddings already exist.
#
# STEP 1: SHARED STUFF (outside the function)
#   New names so they don't overwrite Exercise 9's COLLECTION_NAME / ATLAS_VECTOR_SEARCH_INDEX_NAME
#   (Exercises 10 & 11 still use those). DB_NAME is reused: same "test_db".
PDF_COLLECTION_NAME = "test_collection_pdf"
PDF_INDEX_NAME = "test-index-pdf"

# STEP 2: THE FUNCTION (same as run_exercise_9, only the collection + index names change)
def run_exercise_12():
    # 2a. Setup: connect and point at the NEW collection
    client = MongoClient(os.getenv("MONGODB_ATLAS_CLUSTER_URI"))
    MONGODB_COLLECTION = client[DB_NAME][PDF_COLLECTION_NAME]

    vector_store = MongoDBAtlasVectorSearch(
        collection=MONGODB_COLLECTION,
        embedding=embeddings,
        index_name=PDF_INDEX_NAME,
        relevance_score_fn="cosine",
    )

    # 2b. The new part: create the index on the new collection
    print("Creating PDF vector search index...")
    vector_store.create_vector_search_index(
        dimensions=768, wait_until_complete=60  # must match output_dimensionality in Exercise 9
    )

    # 2c. Show the result
    print("PDF Vector Store Created!")

    # 2d. Clean up
    client.close()

# STEP 3: menu line added in EXERCISES below.
#endregion

# ==========================================
# Exercise 13: Store the PDF Chunks (MongoDB Atlas)
# ==========================================
#region
# STEP 0: IMPORTS -> added `time` and RecursiveCharacterTextSplitter at the top of the file.
#
# STEP 1: SHARED STUFF (outside the function)
#   Reusing from Exercise 12: DB_NAME, PDF_COLLECTION_NAME, PDF_INDEX_NAME
#   diabetes.pdf sits next to this script, same idea as FACTS_FILE
PDF_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diabetes.pdf")

# Custom PDF loader: one Document per page
def load_pdf_document(file_path: str) -> list[Document]:
    reader = PdfReader(file_path)
    docs = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:  # skip empty pages (e.g. image-only pages)
            # Page numbers tell the LLM where info came from
            docs.append(Document(
                page_content=text,
                metadata={"source": file_path, "page": i + 1},
            ))
    return docs

# STEP 2: THE FUNCTION
def run_exercise_13():
    # 2a. Setup: connect to the PDF collection from Exercise 12
    client = MongoClient(os.getenv("MONGODB_ATLAS_CLUSTER_URI"))
    MONGODB_COLLECTION = client[DB_NAME][PDF_COLLECTION_NAME]

    vector_store = MongoDBAtlasVectorSearch(
        collection=MONGODB_COLLECTION,
        embedding=embeddings,
        index_name=PDF_INDEX_NAME,
        relevance_score_fn="cosine",
    )

    # Start clean, then re-embed everything
    MONGODB_COLLECTION.delete_many({})
    print("Previous documents cleared")

    # 2b. The new part: load PDF -> split -> add in batches
    # Recursive splitter tries paragraphs first, then lines, then words,
    # so chunks break at natural places. overlap=100 keeps context across cuts.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
    )

    print("Loading PDF...")
    pdf_docs = load_pdf_document(PDF_FILE)

    # Split the pages into chunks
    docs = text_splitter.split_documents(pdf_docs)
    print(f"Total chunks: {len(docs)}")

    # Add in batches; wait and retry on errors (free tier: 100 requests per minute)
    BATCH_SIZE = 50
    for i in range(0, len(docs), BATCH_SIZE):
        batch = docs[i:i + BATCH_SIZE]
        for attempt in range(5):
            try:
                vector_store.add_documents(batch)
                break
            except Exception as e:
                wait = 15 * 2 ** attempt  # 15s, 30s, 60s, 120s, 240s
                print(f"Retry in {wait}s: {e}")
                time.sleep(wait)
        # 2c. Show progress
        print(f"Added chunks {i + 1}-{i + len(batch)} of {len(docs)}")
        time.sleep(60)  # free tier: 100 RPM

    # 2d. Clean up
    client.close()

# STEP 3: menu line added in EXERCISES below.
#endregion

# ==========================================
# Exercise 14: Query the PDF (RAG)
# ==========================================
#region
# STEP 0: IMPORTS -> nothing new, all already imported for Exercise 11.
#
# STEP 1: SHARED STUFF
#   Reusing: DB_NAME, PDF_COLLECTION_NAME, PDF_INDEX_NAME (Exercise 12),
#            format_docs (Exercise 11), INPUT_PLACEHOLDER, GEMINI_FLASH_LITE_MODEL

# Builds the PDF RAG chain. Kept outside run_exercise_14 so Exercise 15 (FastAPI) can reuse it.
# The caller opens the MongoClient and is responsible for closing it.
def build_pdf_rag_chain(client):
    # Lite model instead of the slide's "gemini-3.8-flash" (that one gave 503 "high demand" in Exercise 11)
    llm = ChatGoogleGenerativeAI(model=GEMINI_FLASH_LITE_MODEL, api_key=os.getenv("GEMINI_API_KEY"))

    MONGODB_COLLECTION = client[DB_NAME][PDF_COLLECTION_NAME]

    vector_store = MongoDBAtlasVectorSearch(
        collection=MONGODB_COLLECTION,
        embedding=embeddings,
        index_name=PDF_INDEX_NAME,
        relevance_score_fn="cosine",
    )

    # k=10 returns the top 10 most relevant chunks (more than Exercise 11's 3,
    # because PDF chunks are pieces of longer explanations)
    retriever = vector_store.as_retriever(search_kwargs={"k": 10})

    # System prompt: answer only from the PDF, and say what to do when it has NO answer
    system_prompt = (
        """
        You are a helpful medical information assistant. Answer the question using ONLY the context below,
        which comes from a document about diabetes.
        - Keep the answer clear and concise; use bullet points for lists.
        - If the context does not contain the answer, reply exactly:
          "Sorry, I couldn't find that information in the diabetes document."
          Do not guess or use outside knowledge.
        - Do not give personal medical advice; suggest consulting a doctor for personal decisions.
        Context:\n{context}
        """
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", INPUT_PLACEHOLDER),
    ])

    # Retrieve, build the prompt, call the LLM, parse the text
    return (
        {"context": retriever | format_docs, "input": RunnablePassthrough()}
        | prompt | llm | StrOutputParser()
    )

# STEP 2: THE FUNCTION
def run_exercise_14():
    # 2a. Setup: connect, then build the chain with the helper above
    client = MongoClient(os.getenv("MONGODB_ATLAS_CLUSTER_URI"))
    rag_chain = build_pdf_rag_chain(client)

    # 2c. Execute the query (change the question here)
    print("Querying Vector DB...")
    response = rag_chain.invoke("Can diabetes be prevented, and how?")
    print(f"\nAI Response: {response}")

    # 2d. Clean up
    client.close()

# STEP 3: menu line added in EXERCISES below.
#endregion

# ==========================================
# Exercise 15: Ask the PDF via FastAPI (GET endpoint)
# ==========================================
#region
# STEP 0: IMPORTS -> nothing new (FastAPI, HTTPException already imported for Exercise 5/6).
#
# STEP 1: SHARED STUFF
#   FastAPI special case: the route lives at module level (like Exercise 5/6),
#   because uvicorn looks for `app` and its routes when it imports this file.

# GET /ask-pdf?question=...
# A plain `question: str` parameter (not in the path) = FastAPI reads it from the query string
@app.get("/ask-pdf", responses={
    400: {"description": "Question is empty"},
    500: {"description": "Error answering the question"},
})
async def ask_pdf(question: str) -> dict:
    if not question.strip():
        raise HTTPException(status_code=400, detail="Please provide a question.")

    # Reuse the chain from Exercise 14. `with` closes the MongoDB connection automatically
    with MongoClient(os.getenv("MONGODB_ATLAS_CLUSTER_URI")) as client:
        rag_chain = build_pdf_rag_chain(client)
        try:
            answer = await rag_chain.ainvoke(question)
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail="An error occurred while answering the question.")

    return {"question": question, "answer": answer}

# STEP 2: THE FUNCTION (FastAPI special case: just prints how to start the server)
def run_exercise_15():
    print("This is a FastAPI endpoint. To run the server, use Uvicorn in your terminal:")
    print(UVICORN_APP_COMMAND)
    print("Then open the Swagger UI at http://127.0.0.1:8000/docs and try GET /ask-pdf")

# STEP 3: menu line added in EXERCISES below.
#endregion

# ==========================================
# Exercise 16: Diabetes RAG Chatbot Frontend (Option 2: own frontend)
# ==========================================
#region
# STEP 0: IMPORTS -> added CORSMiddleware and FileResponse at the top of the file.
#
# STEP 1: SHARED STUFF (FastAPI special case: module level)
#   The page itself is frontend/chatbot.html; it calls GET /ask-pdf from Exercise 15.

# CORS: lets a page from another origin (e.g. chatbot.html opened by double-click = file://)
# call this API. "*" is fine for local development only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CHATBOT_PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "chatbot.html")

# Serves the chat page from the same server, so http://127.0.0.1:8000/chat just works
@app.get("/chat", include_in_schema=False)
async def chat_page():
    return FileResponse(CHATBOT_PAGE)

# STEP 2: THE FUNCTION (FastAPI special case: just prints how to start it)
def run_exercise_16():
    print("To run the chatbot, start the server in your terminal:")
    print(UVICORN_APP_COMMAND)
    print("Then open http://127.0.0.1:8000/chat in your browser")

# STEP 3: menu line added in EXERCISES below.
#endregion

# ==========================================
# Exercise 17: AI Agent with Tool Calling
# ==========================================
#region
# STEP 0: IMPORTS -> added ast, operator, `tool` and `create_agent` at the top of the file.
#
# STEP 1: SHARED STUFF (outside the function)

# Safe maths instead of the slide's eval(): eval() runs ANY Python code the LLM sends
# (e.g. deleting files), so we only allow numbers and + - * / // % ** and brackets.
_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

def _safe_eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Only numbers and + - * / // % ** ( ) are allowed")

# Define a tool with custom name and description.
# The LLM reads the name + description to decide WHEN to call it,
# and the type hint (expression: str) to know WHAT to send.
@tool("calculator", description="Performs mathematical calculations. Input is a Python maths expression, e.g. '10000 * (1 + 0.08) ** 5'.")
def calculator(expression: str) -> str:
    try:
        result = _safe_eval(ast.parse(expression, mode="eval").body)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

# STEP 2: THE FUNCTION
def run_exercise_17():
    # 2a. Setup: LLM + agent
    llm = ChatGoogleGenerativeAI(model=GEMINI_FLASH_LITE_MODEL, api_key=os.getenv("GEMINI_API_KEY"))

    tools = [calculator]
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt="You are a helpful assistant. Use the calculator tool for any maths.",
    )

    # 2b. The new part: ask a question; the agent decides by itself whether to call the tool
    question = HumanMessage(content="What's the result of an investment of $10,000 growing at 8% annually for 5 years with compound interest?")
    response = agent.invoke({"messages": [question]})

    # 2c. Show the result
    # Print every step so you can SEE the tool call happen (not on the slide, just for learning)
    for msg in response["messages"]:
        if msg.type == "ai" and msg.tool_calls:
            for call in msg.tool_calls:
                print(f"[Agent calls tool] {call['name']}({call['args']})")
        elif msg.type == "tool":
            print(f"[Tool returns] {msg.content}")

    # The last message is the agent's final answer
    final_message = response["messages"][-1]
    print(f"\nAI Response: {final_message.text}")

# STEP 3: menu line added in EXERCISES below.
#endregion

# ==========================================
# Exercise 18: AI Agent with Two Tools (Calculator + Web Search)
# ==========================================
#region
# STEP 0: IMPORTS -> TavilyClient added at the top of the file.
#
# STEP 1: SHARED STUFF (outside the function)
#   Tool 1: reusing the safe `calculator` tool from Exercise 17 (no eval needed).

# Tavily = a search engine made for AI agents. The key comes from .env
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# Tool 2: web search
@tool("web_search", description="Searches the web for up-to-date information, news and facts.")
def web_search(query: str) -> Dict[str, Any] | str:
    try:
        return tavily_client.search(query)
    except Exception as e:
        return f"Error: {e}"

# STEP 2: THE FUNCTION
def run_exercise_18():
    # 2a. Setup: LLM + agent with BOTH tools
    llm = ChatGoogleGenerativeAI(model=GEMINI_FLASH_LITE_MODEL, api_key=os.getenv("GEMINI_API_KEY"))

    tools = [calculator, web_search]
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt="You are a helpful assistant. Use the calculator tool for any maths and the web_search tool for any information.",
    )

    # 2b. Ask a question that needs both tools
    question = HumanMessage(content="If I got 10 cats and each of them eat 4 cans of fish everyday, search typical can of fish price online, and the price increasing every year around 15%, how much is feeding a cat cost in 4 years? Also, search the web for news funny cats.")
    response = agent.invoke({"messages": [question]})

    # 2c. Show each tool call, then the final answer (same as Exercise 17)
    for msg in response["messages"]:
        if msg.type == "ai" and msg.tool_calls:
            for call in msg.tool_calls:
                print(f"[Agent calls tool] {call['name']}({call['args']})")

    final_message = response["messages"][-1]
    print(f"\nAI Response: {final_message.text}")

# STEP 3: menu line added in EXERCISES below.
#endregion

# ==========================================
# Exercise 19: Currency Exchange Agent (Frankfurter API) + LangSmith tracing
# ==========================================
#region
# STEP 0: IMPORTS -> added `requests` at the top of the file.
#   LangSmith needs no import: load_dotenv() at the top already loads LANGCHAIN_TRACING_V2,
#   LANGCHAIN_API_KEY and LANGCHAIN_PROJECT from .env, and LangChain sends traces by itself.
#
# STEP 1: SHARED STUFF (outside the function)

# Frankfurter: free exchange rates from the European Central Bank, no API key needed
FRANKFURTER_URL = "https://api.frankfurter.dev/v1/latest"

@tool(
    "get_exchange_rate",
    description="Gets the latest exchange rate between two currencies. "
                "Use 3-letter ISO currency codes, e.g. from_currency='USD', to_currency='MYR'.",
)
def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    try:
        # GET https://api.frankfurter.dev/v1/latest?base=USD&symbols=MYR
        response = requests.get(
            FRANKFURTER_URL,
            params={"base": from_currency.upper(), "symbols": to_currency.upper()},
            timeout=10,  # don't let a slow API hang the agent
        )
        response.raise_for_status()  # 4xx/5xx (e.g. unknown currency) -> exception
        data = response.json()       # {"amount":1.0,"base":"USD","date":"...","rates":{"MYR":4.077}}
        rate = data["rates"][to_currency.upper()]
        return f"1 {data['base']} = {rate} {to_currency.upper()} (date: {data['date']})"
    except requests.RequestException as e:
        return f"Error: could not get the rate for {from_currency}->{to_currency} ({e})"
    except (KeyError, ValueError):
        return "Error: unexpected response from the exchange rate API"

# STEP 2: THE FUNCTION
def run_exercise_19():
    # 2a. Setup: LLM + agent with the currency tool
    llm = ChatGoogleGenerativeAI(model=GEMINI_FLASH_LITE_MODEL, api_key=os.getenv("GEMINI_API_KEY"))

    agent = create_agent(
        model=llm,
        tools=[get_exchange_rate],
        system_prompt="You are a helpful assistant. Use the get_exchange_rate tool for any currency exchange rate question, and mention the date of the rate.",
    )

    # 2b. Ask the exercise question
    question = HumanMessage(content="What is the current exchange rate from US dollars to Malaysian Ringgit?")
    response = agent.invoke({"messages": [question]})

    # 2c. Show the tool calls/results, then the final answer
    for msg in response["messages"]:
        if msg.type == "ai" and msg.tool_calls:
            for call in msg.tool_calls:
                print(f"[Agent calls tool] {call['name']}({call['args']})")
        elif msg.type == "tool":
            print(f"[Tool returns] {msg.content}")

    final_message = response["messages"][-1]
    print(f"\nAI Response: {final_message.text}")
    print("\n(See the full trace at https://smith.langchain.com, under your LANGCHAIN_PROJECT)")

# STEP 3: menu line added in EXERCISES below.
#endregion

# ==========================================
# Exercise 20: Simple Agent with Memory
# ==========================================
#region

def run_exercise_20():
    llm = ChatGoogleGenerativeAI(model=GEMINI_FLASH_LITE_MODEL, api_key=os.getenv("GEMINI_API_KEY"))
    agent = create_agent(
        model=llm,
        checkpointer=InMemorySaver()
    )
    
    config = {"configurable": {"thread_id": "1"}}
    
    response = agent.invoke({"messages": [HumanMessage(content="Hi!I am Jack, can you AI not take over the world?")]}, config)
    print(response["messages"][-1].text)
    
    response = agent.invoke({"messages": [HumanMessage(content="Hi! Whats my name?")]}, config)
    print(response["messages"][-1].text)
    
    
#endregion


# ==========================================
# Exercise 21: Agent Memory in PostgreSQL (PostgresSaver)
# ==========================================
#region
# STEP 0: IMPORTS -> added PostgresSaver at the top of the file.
#   Needs in .env:  DB_URI=postgresql://postgres:<your password>@localhost:5432/agentdb
#   (the "agentdb" database must exist in PostgreSQL first)
#
# STEP 1: SHARED STUFF -> nothing new.

# STEP 2: THE FUNCTION
def run_exercise_21():
    DB_URI = os.getenv("DB_URI")
    if not DB_URI:
        print("DB_URI is missing palui")
        return

    llm = ChatGoogleGenerativeAI(model=GEMINI_FLASH_LITE_MODEL, api_key=os.getenv("GEMINI_API_KEY"))

    # 2a. Setup: open a connection to Postgres. `with` closes it automatically at the end
    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        # Creates the tables the checkpointer needs. Safe to run every time
        # (it skips tables that already exist); the slide says you can comment it out after the first run.
        checkpointer.setup()

        agent = create_agent(
            model=llm,
            checkpointer=checkpointer,  # memory is saved in PostgreSQL instead of RAM
        )

        # Same thread_id = same conversation, even across separate runs of this program
        config = {"configurable": {"thread_id": "2"}}

        # 2b. Talk to the agent
        response = agent.invoke({"messages": [HumanMessage(content="Hi! My name is Ali.")]}, config)
        print(f"AI: {response['messages'][-1].text}")

        # Not on the slide: a follow-up question to prove the memory works
        response = agent.invoke({"messages": [HumanMessage(content="What's my name?")]}, config)
        print(f"AI: {response['messages'][-1].text}")

        # 2c. Show how much this thread remembers (grows every time you run it)
        print(f"\n(Thread '{config['configurable']['thread_id']}' now has {len(response['messages'])} messages stored in PostgreSQL)")

# STEP 3: menu line added in EXERCISES below.
#endregion


# ==========================================
# Exercise 22: LangChain Middleware
# ==========================================
#region

def run_exercise_22():
    primary_llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", api_key=os.getenv("GEMINI_API_KEY"))
    fallback1 = ChatGoogleGenerativeAI(model="gemini-3.8-flash-lite", api_key=os.getenv("GEMINI_API_KEY"))
    fallback2 = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", api_key=os.getenv("GEMINI_API_KEY"))

    agent = create_agent(
        model=primary_llm,
        middleware=[ModelFallbackMiddleware(fallback1, fallback2)],
        system_prompt = "you are a clever assistant."
    )
    
    response = agent.invoke(
        {"messages": [HumanMessage(
            content="Hi! I am Jack, can you AI not take over the world?")]})
    
    print(response["messages"][-1].text)
    print(response["messages"][-1].response_metadata["model_name"])
#endregion


# ==========================================
# Exercise 23: MCP Agent (stdio + HTTP servers)
# ==========================================
#region

# STEP 0: IMPORTS -> added sys, asyncio, logging, ModelRetryMiddleware and
#         MultiServerMCPClient at the top of the file.

# STEP 1: SHARED STUFF (outside the function)
#   The MCP SERVERS can't live in this file: each one must run as its own program.
#   They sit in mcp/backend/server/ (stdio/random_number.py, http/roll_dice.py).
#   The CLIENT side (the course's servers.py + main.py) lives here.
# Course says gemini-2.5-flash, but Google retired it (404 NOT_FOUND).
# gemini-3.8-flash kept timing out (504 DEADLINE_EXCEEDED), so use the fast lite model.
MCP_MODEL = GEMINI_FLASH_LITE_MODEL
MCP_SERVER_DIR = os.path.join(os.path.dirname(__file__), "mcp", "backend", "server")

# = the course's servers.py: every MCP server the agent can use
SERVERS = {
    # stdio: the client starts this file itself as a child process (nothing to run by hand)
    "random_number": {
        "command": sys.executable,
        "args": [os.path.join(MCP_SERVER_DIR, "stdio", "random_number.py")],
        "transport": "stdio",
    },
    # HTTP: must ALREADY be running (terminal 1: python mcp/backend/server/http/roll_dice.py)
    "roll_dice": {
        "url": "http://localhost:8001/mcp",  # 8001: uvicorn app uses 8000
        "transport": "streamable_http",
    },
}

MCP_SYSTEM_PROMPT = (
    "You are a helpful assistant. Use your tools when they fit. "
    "If no tool can do the job, say so. Answer in plain sentences."
)

# Gemini prints warnings about MCP tool schemas it doesn't fully support; hide that noise
logging.getLogger("langchain_google_genai._function_utils").setLevel(logging.ERROR)

# = the course's main.py. Kept outside run_exercise_23 so Exercise 24 can reuse it.
# async because MCP tools are async: loading and calling them needs `await`.

def _get_mcp_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY is missing from .env")
    return api_key


async def _get_mcp_tools(servers: dict):
    # Connect to every server and collect their tools as normal LangChain tools
    client = MultiServerMCPClient(servers)
    tools = await client.get_tools()
    print("Tools Available:", [t.name for t in tools])
    return tools


def _make_mcp_llm(api_key: str):
    # By default Gemini retries 6 times with growing waits and NO timeout, so a rate
    # limit (429) looks like a silent freeze for minutes. Fail fast and show the error.
    return ChatGoogleGenerativeAI(model=MCP_MODEL, api_key=api_key,
                                 timeout=60, max_retries=1)


def _make_mcp_agent(llm, tools):
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=MCP_SYSTEM_PROMPT,
        middleware=[ModelRetryMiddleware(max_retries=2)],
    )


def _log_mcp_message(m):
    if m.type == "ai" and m.tool_calls:
        for call in m.tool_calls:
            print(f"  -> calling {call['name']} {call['args']}")
    elif m.type == "tool":
        print(f"  <- {m.name} answered")


def _collect_mcp_messages(step: dict):
    messages = []
    for update in step.values():
        for m in (update or {}).get("messages", []):
            messages.append(m)
            _log_mcp_message(m)
    return messages


async def ask_mcp_agent(servers: dict, question: str):
    api_key = _get_mcp_api_key()
    tools = await _get_mcp_tools(servers)
    llm = _make_mcp_llm(api_key)
    agent = _make_mcp_agent(llm, tools)

    # astream instead of ainvoke: same result, but we get each step AS IT HAPPENS,
    # so you can watch the agent work instead of staring at a blank screen.
    print("Thinking... (web searches can take 30s+)")
    messages = []
    async for step in agent.astream({"messages": [HumanMessage(content=question)]},
                                    stream_mode="updates"):
        messages.extend(_collect_mcp_messages(step))

    # Every tool result comes back as a message with type "tool"
    print("Tools used:", [m.name for m in messages if m.type == "tool"])
    print(messages[-1].text)

# STEP 2: THE FUNCTION (asyncio.run = starts the async code from the normal menu)
def run_exercise_23():
    asyncio.run(ask_mcp_agent(
        SERVERS,
        "Roll two dice, then give me a random number between 1 and 10."
    ))

# STEP 3: menu line added in EXERCISES below.
#endregion


# ==========================================
# Exercise 24: MCP Remote Search (Tavily)
# ==========================================
#region

# STEP 0: IMPORTS -> nothing new.

# STEP 1: SHARED STUFF
#   Reusing: SERVERS + ask_mcp_agent (Exercise 23), TAVILY_API_KEY (top of the file,
#   read AFTER load_dotenv() so it is set).
#   Tavily hosts this MCP server on the internet: nothing to start yourself.
#   The key goes in the header, NEVER in the URL (URLs end up in logs).
TAVILY_MCP_SERVERS = {
    **SERVERS,  # keep random_number + roll_dice unchanged
    "tavily": {
        "url": "https://mcp.tavily.com/mcp/",
        "transport": "streamable_http",
        "headers": {"Authorization": f"Bearer {TAVILY_API_KEY}"},
    },
}

# STEP 2: THE FUNCTION
def run_exercise_24():
    if not TAVILY_API_KEY:
        raise SystemExit("TAVILY_API_KEY is missing from .env")
    asyncio.run(ask_mcp_agent(
        TAVILY_MCP_SERVERS,
        "What are the top AI news headlines today? "
        "Then give me a random number between 1 and 10."
    ))

# STEP 3: menu line added in EXERCISES below.
#endregion

# ==========================================
# Exercise 25: Read-only PostgreSQL MCP Server
# ==========================================
#region

# STEP 0: IMPORTS -> nothing new.

# STEP 1: SHARED STUFF
#   Reusing: SERVERS, MCP_SERVER_DIR, ask_mcp_agent (Exercise 23).
#   New server file: mcp/backend/server/stdio/postgres_server.py (tools: list_tables, run_query)
#   New data file:   mcp/backend/books.sql
#   ONE-TIME SETUP (PowerShell, from "phase4_genai_agentic/ai"):
#     & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -c "CREATE DATABASE books_db"
#     & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d books_db -f mcp/backend/books.sql
#   DATABASE_URL goes in mcp/backend/.env (the server's load_dotenv finds that one first):
#     DATABASE_URL=postgresql+psycopg://postgres:<password>@localhost:5432/books_db
POSTGRES_MCP_SERVERS = {
    **SERVERS,  # keep random_number + roll_dice unchanged
    # stdio again: the client launches postgres_server.py itself
    "postgres": {
        "command": sys.executable,
        "args": [os.path.join(MCP_SERVER_DIR, "stdio", "postgres_server.py")],
        "transport": "stdio",
    },
}

# STEP 2: THE FUNCTION
def run_exercise_25():
    asyncio.run(ask_mcp_agent(
        POSTGRES_MCP_SERVERS,
        "How many books are there in books_db, and who wrote the first one?"
    ))

# STEP 3: menu line added in EXERCISES below.
#endregion

# ==========================================
# Main Menu Configuration
# ==========================================
# HOW TO ADD A NEW EXERCISE:
# Step 1: Write your new function anywhere above (e.g., def run_exercise_4(): )
# Step 2: Add a new line to the EXERCISES dictionary below.
# Format: "Menu Number": ("Description of what it does", name_of_function_without_parentheses)

EXERCISES = {
    "a": ("Intro A : LangChain Basics (Messages)", run_intro_a),
    "b": ("Intro B : LangChain Basics (Prompt Template)", run_intro_b),
    "c": ("Intro C : Few-Shot Prompting (Coffee Review Sentiment)", run_intro_c),
    "d": ("Intro D : Chain of Thought (Math Problem)", run_intro_d),
    "1": ("Exercise 1 : Comma Separated List Output Parser", run_exercise_1),
    "2": ("Exercise 2 : Chat with Conversation History", run_exercise_2),
    "3": ("Exercise 3 : Thinking Level Parameter", run_exercise_3),
    "4": ("Exercise 4 : Text Summarization (Webpage)", run_exercise_4),
    "5": ("Exercise 5 : Text Summarization", run_exercise_5),
    "6" : ("Exercise 6 : LLM and Image Analytics", run_exercise_6),
    "7": ("Exercise 7 : Introduction to Streamlit", run_exercise_7),
    "8": ("Exercise 8 : KYC Verification App (Streamlit)", run_exercise_8),
    "9": ("Exercise 9 : Create Vector Store (MongoDB Atlas)", run_exercise_9),
    "10": ("Exercise 10 : Store the Embeddings (MongoDB Atlas)", run_exercise_10),
    "11": ("Exercise 11 : Perform the Query (RAG)", run_exercise_11),
    "12": ("Exercise 12 : Create PDF Vector Store (MongoDB Atlas)", run_exercise_12),
    "13": ("Exercise 13 : Store the PDF Chunks (MongoDB Atlas)", run_exercise_13),
    "14": ("Exercise 14 : Query the PDF (RAG)", run_exercise_14),
    "15": ("Exercise 15 : Ask the PDF via FastAPI (GET endpoint)", run_exercise_15),
    "16": ("Exercise 16 : Diabetes RAG Chatbot Frontend", run_exercise_16),
    "17": ("Exercise 17 : AI Agent with Tool Calling", run_exercise_17),
    "18": ("Exercise 18 : AI Agent with Two Tools (Calculator + Web Search)", run_exercise_18),
    "19": ("Exercise 19 : Currency Exchange Agent (Frankfurter API) + LangSmith", run_exercise_19),
    "20": ("Exercise 20 : Simple Agent with Memory", run_exercise_20),
    "21": ("Exercise 21 : Agent Memory in PostgreSQL (PostgresSaver)", run_exercise_21),
    "22": ("Exercise 22 : LangChain Middleware", run_exercise_22),
    "23": ("Exercise 23 : MCP Agent (stdio + HTTP servers)", run_exercise_23),
    "24": ("Exercise 24 : MCP Remote Search (Tavily)", run_exercise_24),
    "25": ("Exercise 25 : Read-only PostgreSQL MCP Server", run_exercise_25),

    # Example of how to add your next one (remove the '#' to activate it once the function is built):
    # "26": ("Exercise 26 : <slide title>", run_exercise_26),
    #   - the key is a STRING ("26"), it's what you type in the menu
    #   - the function name has NO () — the menu calls it for you
}

if __name__ == "__main__":
    print("Which code do you want to run?")
    
    # This loop automatically reads the dictionary and prints the menu options for you
    for key, (description, _) in EXERCISES.items():
        print(f"{key}. {description}")

    # This dynamically updates the allowed inputs based on the dictionary keys (e.g., "1, 2, 3")
    valid_choices = ", ".join(EXERCISES.keys())
    choice = input(f"Enter choice ({valid_choices}): ").strip().lower()  # lower: "A" works like "a"

    if choice in EXERCISES:
        # EXERCISES[choice][1] grabs the function name, and the () executes it
        function_to_run = EXERCISES[choice][1]
        function_to_run()
    else:
        print(f"Invalid choice. Please run the script again and select one of: {valid_choices}")

