# PDFs Chatbox using LangChain and Hugging Face Inference
This is a Python gui application that demonstrates how to build a custom PDF chatbot using LangChain and GPT 3.5 / Llama 2. 


## How it works (GPT 3.5)
1. The application gui is built using react
2. The application reads text from PDF files, splits it into chunks
3. Uses Sbert embedding vectors used to find the most relevant content to a user's question 
4. Build a conversational retrieval chain using Langchain
5. Use OpenAI GPT API to generate respond based on content in PDF


## Requirements
1. Install the following Python packages:
```
pip install streamlit pypdf2 langchain python-dotenv faiss-cpu openai sentence_transformers
```

2. Create a `.env` file in the root directory of the project and add the following environment variables:
```
OPENAI_API_KEY= # Your OpenAI API key
```


## Code Structure

The code is structured as follows:

- `app.py`: The main application file that defines the Streamlit gui app and the user interface.
    * get_pdf_text function: reads text from PDF files
    * get_text_chunks function: splits text into chunks
    * get_vectorstore function: creates a FAISS vectorstore from text chunks and their embeddings
    * get_conversation_chain function: creates a retrieval chain from vectorstore
    * handle_userinput function: generates response from OpenAI GPT API
- `htmlTemplates.py`: A module that defines HTML templates for the user interface.


## How to run
```
npm start
```


## Run the backend
1. Install Python bindings
```
pip install flask flask-cors python-dotenv PyPDF2 langchain langchain-huggingface faiss-cpu huggingface_hub sentence_transformers

```
2. run
```
python app.py
```
   
