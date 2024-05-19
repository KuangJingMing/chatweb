from flask import Flask, request, render_template, session, redirect, url_for, jsonify
from datetime import datetime
import os
from openai import OpenAI
import uuid
import traceback

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'SECRET_KEY')
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
MAX_MESSAGES = 40
SYSTEM_ROLE = ""

with open("./SystemRole/role.txt", "r") as f:
    SYSTEM_ROLE = f.read()

@app.route("/", methods=["GET", "POST"])
def chat():
    ensure_session_keys()
    if request.method == "POST":
        user_input = request.json.get("user_input", "")
        return post_chat(user_input)
    return get_chat()

def ensure_session_keys():
    session.setdefault('session_id', str(uuid.uuid4()))
    session.setdefault('chat_history', [])

def post_chat(user_input):
    chat_history = session.get('chat_history', [])
    chat_history.append({"role": "user", "content": user_input})
    chat_history = handle_system_response(chat_history, user_input)
    session['chat_history'] = chat_history
    session.modified = True
    save_chat_history(chat_history)
    return jsonify({"system_message": chat_history[-1]["content"]})

def handle_system_response(chat_history, user_input):
    try:
        last_messages = chat_history[-MAX_MESSAGES:] if len(chat_history) > MAX_MESSAGES else chat_history
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[{"role": "system", "content": SYSTEM_ROLE}] + last_messages
        )
        system_response = response.choices[0].message.content
        chat_history.append({"role": "system", "content": system_response})
    except Exception as e:
        chat_history.append({"role": "system", "content": "An error occurred: " + str(e)})
        traceback.print_exc()
    return chat_history

def get_chat():
    return render_template("index.html", history=session.get('chat_history', []))

def save_chat_history(chat_history):
    directory = os.path.join(os.getcwd(), "chat_histories")
    os.makedirs(directory, exist_ok=True)

    current_time = datetime.now().strftime("%Y-%m-%d-%H:%M")
    filename = f"chat_history_{current_time}.txt"
    file_path = os.path.join(directory, filename)

    try:
        with open(file_path, 'w') as file:
            for index, entry in enumerate(chat_history, start=1):
                file.write(f"{index}. {entry['role']}: {entry['content']}\n")
    except IOError as e:
        print(f"Failed to save chat history to {file_path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while saving chat history: {e}")

    print(f"Chat history successfully saved to {file_path}")

@app.route('/clear_history', methods=['POST'])
def clear_history():
    save_chat_history(session.get('chat_history', []))
    session['chat_history'] = []
    session.modified = True
    return redirect(url_for('chat'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
