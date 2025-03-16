from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_community.llms import HuggingFaceEndpoint
import os

app = Flask(__name__)
CORS(app)

load_dotenv()
print("Token:", os.getenv("HUGGINGFACE_API_TOKEN"))

@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    return response

conversation_chain = None

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text

def get_text_chunks(text):
    splitter = CharacterTextSplitter(separator="\n", chunk_size=500, chunk_overlap=100, length_function=len)
    return splitter.split_text(text)

def get_vectorstore(chunks):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return FAISS.from_texts(texts=chunks, embedding=embeddings)

def get_conversation_chain(vectorstore):
    token = os.getenv("HUGGINGFACE_API_TOKEN")
    print("Using token in get_conversation_chain:", token)  # Debug print
    llm = HuggingFaceEndpoint(
        repo_id="mistralai/Mistral-7B-Instruct-v0.2",
        huggingface_api_token=os.getenv("HUGGINGFACE_API_TOKEN"),
        temperature=0.1,
        model_kwargs={"max_length": 1024}
    )

    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 4})
    return ConversationalRetrievalChain.from_llm(llm=llm, retriever=retriever, memory=memory)


@app.route('/process', methods=['POST'])
def process_pdf():
    global conversation_chain
    if 'pdfs' not in request.files:
        return jsonify({'error': 'No PDF files provided'}), 400
    pdf_files = request.files.getlist('pdfs')
    raw_text = get_pdf_text(pdf_files)
    chunks = get_text_chunks(raw_text)
    vectorstore = get_vectorstore(chunks)
    conversation_chain = get_conversation_chain(vectorstore)
    debug_info = {
        "chain_type": str(type(conversation_chain)),
        "memory_type": str(type(conversation_chain.memory)),
        "retriever": str(conversation_chain.retriever)
    }
    return jsonify({
        'message': 'PDF processed and conversation chain created successfully.',
        'debug': debug_info
    })


@app.route('/ask', methods=['POST'])
def ask_question():
    global conversation_chain
    if conversation_chain is None:
        return jsonify({'error': 'No conversation chain found. Please process PDFs first.'}), 400
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({'error': 'No question provided'}), 400
    user_question = data['question']
    response = conversation_chain({'question': user_question})
    chat_history = [{'role': 'user' if i % 2 == 0 else 'bot', 'content': msg.content} for i, msg in enumerate(response['chat_history'])]
    return jsonify({'answer': response.get('answer', ''), 'chat_history': chat_history})

if __name__ == '__main__':
    app.run(debug=True)
