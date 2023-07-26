import os
import pinecone
from dotenv import load_dotenv
from uuid import uuid4
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQAWithSourcesChain, RetrievalQA
from langchain.vectorstores import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings

load_dotenv()


class Embedding:
    pass


def pinecone_initialize():
    index_name = 'ai-journal'
    pinecone.init(
        api_key=os.getenv('PINECONE_API_KEY'),
        environment=os.getenv('ENVIRONMENT')
    )
    if index_name not in pinecone.list_indexes():
        pinecone.create_index(index_name, dimension=1536)

    return "Pinecone Initialized!"


def split_text(text: str):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=2,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_text(text)
    return chunks


def data_prep(chunks: list, metadata: dict, texts: None, metadatas: None, ):
    texts = [] or texts
    metadatas = [] or metadatas
    chunk_metadata = [{"chunk": j, "chunk_text": text, **metadata}
                      for j, text in enumerate(chunks)]
    texts.extend(chunks)
    metadatas.extend(chunk_metadata)
    ids = [str(uuid4()) for _ in range(len(texts))]

    return ids, texts, metadatas


def embed_and_upsert(ids, texts, metadatas, user_id):
    index = pinecone.Index('ai-journal')
    model_name = 'text-embedding-ada-002'
    embed = OpenAIEmbeddings(
        document_model_name=model_name,
        query_model_name=model_name,
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    embeds = embed.embed_documents(texts)
    index.upsert(vectors=zip(ids, embeds, metadatas), namespace=user_id)
    return "Successfully embedded and upserted the journal to Pinecone!"


def generative_qna(question, user_ID):
    index = pinecone.Index('ai-journal')
    model_name = 'text-embedding-ada-002'

    embed = OpenAIEmbeddings(
        document_model_name=model_name,
        query_model_name=model_name,
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )

    text_field = "text"

    vectorstore = Pinecone(
        index, embed.embed_query, text_field, namespace=user_ID
    )

    llm = ChatOpenAI(
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        model_name='gpt-3.5-turbo',
        temperature=0.0
    )

    # qa_with_sources = RetrievalQAWithSourcesChain.from_chain_type(
    #     llm=llm,
    #     chain_type="stuff",
    #     retriever=vectorstore.as_retriever()
    # )

    qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever()
    )

    response = qa.run(question)
    print("This is the response", response)
    return response