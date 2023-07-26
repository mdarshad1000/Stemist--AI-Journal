# importing dependencies
from flask import Flask, request, abort
from dotenv import load_dotenv
import pinecone
import os
import openai
from flask_cors import CORS, cross_origin

# initialize app 
app = Flask(__name__)
CORS(app,)

load_dotenv()

def pinecone_initialize():
    index_name = 'ai-journal'
    pinecone.init(
        api_key=os.getenv('PINECONE_API_KEY'),
        environment=os.getenv('ENVIRONMENT')
    )
    if index_name not in pinecone.list_indexes():
        pinecone.create_index(index_name, dimension=1536)
    index = pinecone.Index(index_name)


@app.route("/")
def home():
    pinecone_initialize()
    return "Welcome to AI Journalling, Pinecone Initialized!"


@cross_origin('*')
@app.route('/embed', methods=['POST', 'GET'])
def embed():
    index = pinecone.Index('ai-journal')

    if "user_ID" not in request.json or not request.json["user_ID"]:
        abort(400, "user_ID not found!")
    if "username" not in request.json or not request.json["username"]:
        abort(400, "Username not found!")
    if "title" not in request.json or not request.json["title"]:
        abort(400, "title not found!")
    if "body" not in request.json or not request.json["body"]:
        abort(400, "body not found!")

    user_ID = request.json['user_ID']
    username = request.json['username']
    title = request.json['title']
    body = request.json['body']

    res = openai.Embedding.create(input=title + '\n' +  body, engine='text-embedding-ada-002')
    embeds = [record['embedding'] for record in res['data']]
    meta_data = [{'username': username, 'title': title, 'body': body}]
    to_upsert = zip(user_ID, embeds, meta_data)
    index.upsert(vectors=list(to_upsert))

    return f"Successfully embedded the journal!"


@cross_origin('*')
@app.route('/answer', methods=['POST', 'GET'])
def answer():
    index = pinecone.Index('ai-journal')

    question = request.json['question'] if request.json['question'] else ''
    username = request.json['username'] if request.json['username'] else ''

    xq = openai.Embedding.create(input=question, engine='text-embedding-ada-002')['data'][0]['embedding']
    res = index.query([xq],
                      top_k=1,
                      include_metadata=True,
                      filter={
                        "username": username} 
                    )

    for match in res['matches']:
        context = f"{match['score']:.2f}: {match['metadata']['text']}"

    response = openai.Completion.create(
    model="text-davinci-003",
    prompt=f"Answer the queston based on the following context:\n\nContext: {context}\n\nQuestion: {question}",
    temperature=0,
    max_tokens=4000,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )

    return {"reponse":response}

    
if __name__ == '__main__':
    app.run(debug=True)