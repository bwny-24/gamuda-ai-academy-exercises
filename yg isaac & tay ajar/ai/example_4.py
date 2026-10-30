import os, base64
import streamlit as st
from datetime import date
from io import BytesIO
from typing import Annotated, List
from pypdf import PdfReader
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from fastapi import FastAPI, UploadFile, File, HTTPException
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import (
    CommaSeparatedListOutputParser,
    JsonOutputKeyToolsParser,
    StrOutputParser,
)

app = FastAPI()

load_dotenv()
GEMINI_FLASH_LITE_MODEL = "gemini-3.5-flash-lite"

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
        ("human", "{input}"),
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
#region]

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
    print("uvicorn example_4:app --reload")

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
    print("uvicorn example_4:app --reload")
    print("Then send a POST request to http://127.0.0.1:8000/analyze-image with your image file.")

#endregion

# ==========================================
# Exercise 7: Introduction to Streamlit
# ==========================================
#region

def run_exercise_7():
    print("To run this Streamlit app, you must use this command in your terminal:")
    print("streamlit run example_4.py")
    
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
                    {"type": "text", "text": "{input}"},
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
    print("streamlit run example_4_2.py")
    
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
# Exercise 8: KYC Verification App (Streamlit)
# ==========================================
#region

def run_exercise_8():
    print("To run this Streamlit app, you must use this command in your terminal:")
    print("streamlit run example_4_2.py")
    
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
# Main Menu Configuration
# ==========================================
# HOW TO ADD A NEW EXERCISE:
# Step 1: Write your new function anywhere above (e.g., def run_exercise_4(): )
# Step 2: Add a new line to the EXERCISES dictionary below.
# Format: "Menu Number": ("Description of what it does", name_of_function_without_parentheses)

EXERCISES = {
    "1": ("Comma Separated List Output Parser", run_exercise_1),
    "2": ("Chat with Conversation History", run_exercise_2),
    "3": ("Thinking Level Parameter", run_exercise_3),
    "4": ("Exercise 4 : Text Summarization (Webpage)", run_exercise_4),
    "5": ("Exercise 5 : Text Summarization", run_exercise_5),
    "6" : ("Exercise 6: Exercise 6: LLM and Image Analytics", run_exercise_6),
    "7": ("Introduction to Streamlit", run_exercise_7),
    "8": ("KYC Verification App (Streamlit)", run_exercise_8)
    
    # Example of how to add your next one (remove the '#' to activate it once the function is built):
    # "4": ("My Brand New Exercise", run_exercise_4),
}

if __name__ == "__main__":
    print("Which code do you want to run?")
    
    # This loop automatically reads the dictionary and prints the menu options for you
    for key, (description, _) in EXERCISES.items():
        print(f"{key}. {description}")

    # This dynamically updates the allowed inputs based on the dictionary keys (e.g., "1, 2, 3")
    valid_choices = ", ".join(EXERCISES.keys())
    choice = input(f"Enter choice ({valid_choices}): ").strip()

    if choice in EXERCISES:
        # EXERCISES[choice][1] grabs the function name, and the () executes it
        function_to_run = EXERCISES[choice][1]
        function_to_run()
    else:
        print(f"Invalid choice. Please run the script again and select one of: {valid_choices}")