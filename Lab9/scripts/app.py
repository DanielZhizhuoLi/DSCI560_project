import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain_community.llms import LlamaCpp
import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
from langchain.llms import HuggingFaceEndpoint


def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=500,
        chunk_overlap=100,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks


def get_vectorstore(text_chunks):
    # embeddings = OpenAIEmbeddings()
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

def store_vector(vectorstore, index):
    texts = vectorstore.docstore._dict.values()
    upsert_data = []

    for i, text in enumerate(texts):
        vector = vectorstore.index.reconstruct(i)  # Retrieve FAISS vector by index

        text_content = text.page_content if hasattr(text, "page_content") else str(text)
        upsert_data.append((str(i), vector, {"text": text_content})) 

    # Upsert vectors into Pinecone
    index.upsert(vectors=upsert_data)

# def get_conversation_chain(vectorstore):
#     #llm = ChatOpenAI()
#     # llm = HuggingFacePipeline.from_model_id(
#     #     model_id="lmsys/vicuna-7b-v1.3",
#     #     task="text-generation",
#     #     model_kwargs={"temperature": 0.01},
#     # )
#     llm = LlamaCpp(
#         model_path="models/llama-2-7b.Q4_K_M.gguf",  n_ctx=1024, n_batch=512)
    
#     memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)

#     retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 4})

#     conversation_chain = ConversationalRetrievalChain.from_llm(
#         llm=llm,
#         retriever=retriever,
#         memory=memory,
#     )
#     return conversation_chain

def get_conversation_chain(vectorstore):
    # using Mistral 7B
    llm = HuggingFaceEndpoint(
        repo_id="mistralai/Mistral-7B-Instruct-v0.2",
        max_length=1024,
        temperature=0.1,
        token=None  # no token needed for inference API with open models
    )

    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(
            search_type="similarity", search_kwargs={"k": 4}),
        memory=memory,
    )
    return conversation_chain



def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)


def main():
    load_dotenv()

    # Initialize Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

    index_name = "ads-embedding"

    # Check if the index exists, and create it if it doesn't
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=384,
            metric="cosine",  
            spec=ServerlessSpec(cloud="aws", region="us-east-1")  
        )
    # Create the index object
    index = pc.Index(index_name)

    st.set_page_config(page_title="Chat with PDFs",
                       page_icon=":robot_face:")
    st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.header("Chat with PDFs :robot_face:")
    user_question = st.text_input("Ask questions about your documents:")
    if user_question:
        handle_userinput(user_question)

    with st.sidebar:
        st.subheader("Your documents")
        pdf_docs = st.file_uploader(
            "Upload your PDFs here and click on 'Process'", accept_multiple_files=True)
        if st.button("Process"):
            with st.spinner("Processing"):
                # get pdf text
                raw_text = get_pdf_text(pdf_docs)

                # get the text chunks
                text_chunks = get_text_chunks(raw_text)

                # create vector store
                vectorstore = get_vectorstore(text_chunks)

                # store vector into database
                store_vector(vectorstore, index)

                # create conversation chain
                st.session_state.conversation = get_conversation_chain(
                    vectorstore)


if __name__ == '__main__':
    main()
