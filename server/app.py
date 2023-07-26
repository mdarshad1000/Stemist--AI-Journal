# importing dependencies
from flask import Flask, request, abort
from flask_cors import CORS, cross_origin
from sql_db import Journal
from vector_db import pinecone_initialize, split_text, data_prep, embed_and_upsert, generative_qna
from datetime import datetime
import threading
import time

# initialize app
app = Flask(__name__)
CORS(app,)

last_retrieval_time = datetime.now().replace(microsecond=0)


def retrieve_and_upsert_continuously(interval):
    global last_retrieval_time
    while True:
        sql = Journal()
        sql.connect()
        pinecone_initialize()
        received_data = sql.retrieve_new_entries(
            last_retrieval_time=last_retrieval_time)

        if received_data:

            user_ID = received_data[0]['user_id']
            content = received_data[0]['content']
            title = received_data[0]['title']
            created_at = received_data[0]['created_at']

            journal_entry = title + '\n' + content

            metadata = {
                'user_id': user_ID,
                'content': content,
                'title': title,
                'created_at': created_at
            }

            chunks = split_text(journal_entry)
            print("Chunking Done", chunks)

            prepared_data = data_prep(chunks, metadata, texts=[], metadatas=[])
            print("metadata prepared", prepared_data)

            embed_and_upsert(*prepared_data, user_id=user_ID)
            print("embed and upserted", embed_and_upsert)

        last_retrieval_time = datetime.now().replace(microsecond=0)

        time.sleep(interval)


def start_data_retrieval_thread(interval):
    data_thread = threading.Thread(
        target=retrieve_and_upsert_continuously, args=(interval,))
    data_thread.daemon = True
    data_thread.start()


@app.route("/")
def home():

    return "Welcome to AI Journalling, Pinecone Initialized!"


@cross_origin('*')
@app.route('/ask', methods=['POST', 'GET'])
def ask():
    question = request.json['question'] if request.json['question'] else abort(
        400, "Question not found!")
    user_ID = request.json['user_id'] if request.json['user_id'] else abort(
        400, "userID not found!")
    response = generative_qna(question, user_ID)
    return {"response": response}, 200


if __name__ == '__main__':
    # Run the flask app and the data retrieval thread parallely
    start_data_retrieval_thread(5)
    app.run(debug=True)
