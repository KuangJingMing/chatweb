from flask import Flask, request, render_template, session, redirect, url_for, jsonify
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate
import os
from openai import OpenAI
import uuid
import traceback
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'SECRET_KEY')
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
MAX_MESSAGES = 40

db_dir = "/root/chatweb/chatWab"
db_path = os.path.join(db_dir, "chat.db")

if not os.path.exists(db_dir):
    os.makedirs(db_dir)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

with open("./SystemRole/role.txt", "r") as f:
    SYSTEM_ROLE = f.read()

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('session_id', 'content', name='_session_content_uc'),)

    def __repr__(self):
        return f'<ChatHistory {self.role}: {self.content[:20]}>'

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
    session_id = session.get('session_id')
    chat_history = [
        {'role': entry.role, 'content': entry.content}
        for entry in ChatHistory.query.filter_by(session_id=session_id).all()
    ]
    chat_history.append({"role": "user", "content": user_input})
    chat_history = handle_system_response(chat_history, user_input)
    save_chat_history(chat_history)
    return jsonify({"system_message": chat_history[-1]["content"]})

def handle_system_response(chat_history, user_input):
    try:
        last_messages = chat_history[-MAX_MESSAGES:] if len(chat_history) > MAX_MESSAGES else chat_history
        messages = [{"role": "system", "content": SYSTEM_ROLE}] + [
            {"role": entry["role"], "content": entry["content"]} for entry in last_messages
        ]
        response = client.chat.completions.create(model="gpt-4o-mini",
        messages=messages)
        system_response = response.choices[0].message.content
        chat_history.append({"role": "system", "content": system_response})
    except Exception as e:
        chat_history.append({"role": "system", "content": "An error occurred: " + str(e)})
        traceback.print_exc()
    return chat_history

def get_chat():
    session_id = session.get('session_id')
    history = [
        {'role': entry.role, 'content': entry.content}
        for entry in ChatHistory.query.filter_by(session_id=session_id).all()
    ]
    return render_template("index.html", history=history)

def save_chat_history(chat_history):
    session_id = session.get('session_id')

    # 获取现有记录的内容
    existing_entries = {entry.content for entry in ChatHistory.query.filter_by(session_id=session_id).all()}

    # 插入新记录
    new_entries = [
        entry for entry in chat_history
        if entry['content'] not in existing_entries
    ]
    for entry in new_entries:
        if not ChatHistory.query.filter_by(session_id=session_id, content=entry['content']).first():
            chat_entry = ChatHistory(
                session_id=session_id,
                role=entry['role'],
                content=entry['content']
            )
            db.session.add(chat_entry)

    db.session.commit()

@app.route('/clear_history', methods=['POST'])
def clear_history():
    session_id = session.get('session_id')
    ChatHistory.query.filter_by(session_id=session_id).delete()
    db.session.commit()
    session['chat_history'] = []
    session.modified = True
    return redirect(url_for('chat'))

@app.route('/view_data')
def view_data():
    return render_template('view_data.html')

@app.route("/get_sessions", methods=["GET"])
def get_sessions():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20  # 每页加载20个会话
        pagination = db.session.query(ChatHistory.session_id).distinct().paginate(page=page, per_page=per_page, error_out=False)
        sessions = [{'session_id': session.session_id} for session in pagination.items]
        return jsonify({'sessions': sessions, 'total_pages': pagination.pages})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route("/get_messages/<session_id>", methods=["GET"])
def get_messages(session_id):
    try:
        messages = ChatHistory.query.filter_by(session_id=session_id).all()
        message_data = [
            {
                'id': message.id,
                'session_id': message.session_id,
                'role': message.role,
                'content': message.content,
                'timestamp': message.timestamp
            }
        for message in messages]
        return jsonify({'messages': message_data})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
