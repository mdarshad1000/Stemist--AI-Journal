# importing dependencies
from flask import Flask
from flask_cors import CORS
from sql_db import Journal
from vector_db import pinecone_initialize, split_text, data_prep, embed_and_upsert
import threading
from datetime import datetime
import time

# initialize app 
app = Flask(__name__)
CORS(app,)

last_retrieval_time = datetime.now().replace(microsecond=0)

def retrieve_data_continuously(interval):
    global last_retrieval_time
    while True:
        sql = Journal()
        sql.connect()
        received_data = sql.retrieve_new_entries(last_retrieval_time=last_retrieval_time)

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

            prepared_data = data_prep(chunks, **metadata)

            embed_and_upsert(*prepared_data)








        
        last_retrieval_time = datetime.now().replace(microsecond=0)


        time.sleep(interval)
    
def start_data_retrieval_thread(interval):
    data_thread = threading.Thread(target=retrieve_data_continuously, args=(interval,))
    data_thread.daemon = True
    data_thread.start()


@app.route("/")
def home():

    pinecone_initialize()
    print(retrieve_data_continuously)


if __name__ == '__main__':

    start_data_retrieval_thread(5)

    app.run(debug=True)
