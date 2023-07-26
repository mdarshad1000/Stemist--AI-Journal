import pinecone
import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from uuid import uuid4

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


def split_text(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=150,
        chunk_overlap=10,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_text(text)
    return chunks


def data_prep(chunks, texts: None, metadatas: None,  **metadata):
    texts = texts or []
    metadatas = metadatas or []
    chunk_metadata = [{ "chunk": j, "chunk_text": text, **metadata} for j, text in enumerate(chunks)]
    texts.extend(chunks)
    metadatas.extend(chunk_metadata)
    ids = [str(uuid4()) for _ in range(len(texts))]

    return ids, texts, metadatas


def embed_and_upsert(ids, texts, metadatas):
    index = pinecone.Index('ai-journal')
    model_name = 'text-embedding-ada-002'
    embed = OpenAIEmbeddings(
        document_model_name=model_name,
        query_model_name=model_name,
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    embeds = embed.embed_documents(texts)
    index.upsert(vectors=zip(ids, embeds, metadatas))
    return "Successfully embedded and upserted the journal to Pinecone!"




