import os
import datetime
import json
import networkx as nx
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "clh-secret-dev-key")

# MongoDB Setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client['clh_db']
users_collection = db['users']
topics_collection = db['topics']
subject_choices = ['Physics', 'C Programming', 'Mathematics', 'Biology', 'Engineering Mechanics', 'Electrical Engineering', 'Computer Programming']

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self.selected_subjects = user_data.get('selected_subjects', [])

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

# Color Psychology Mapping (Confidence Score 1-5)
COLOR_MAP = {
    1: '#FF4D4D', # Strong Red (Weak)
    2: '#FFA64D', # Orange
    3: '#FFFF4D', # Yellow
    4: '#B3FF66', # Light Green
    5: '#4DFF4D'  # Strong Green (Strong)
}

def apply_knowledge_decay(topic):
    """
    If topic not reviewed for 7 days, downgrade color.
    Green → Yellow → Red.
    We convert the confidence score (1-5) accordingly.
    """
    last_reviewed = topic.get('last_reviewed', datetime.datetime.utcnow())
    if isinstance(last_reviewed, str):
        last_reviewed = datetime.datetime.fromisoformat(last_reviewed)
    
    days_since = (datetime.datetime.utcnow() - last_reviewed).days
    
    score = topic.get('confidence_score', 3)
    if days_since >= 7:
        # Score reduction based on decay
        score = max(1, score - (days_since // 7))
        # Update in DB
        topics_collection.update_one(
            {'_id': topic['_id']},
            {'$set': {'confidence_score': score, 'last_decay_check': datetime.datetime.utcnow()}}
        )
    return score

# AI Summarization using SambaNova (DeepSeek-R1)
SAMBA_API_KEY = os.getenv("SAMBANOVA_API_KEY")
client_ai = OpenAI(
    api_key=SAMBA_API_KEY, 
    base_url="https://api.sambanova.ai/v1"
) if SAMBA_API_KEY else None

def get_ai_summary(text):
    if not client_ai:
        return "AI Summarization unavailable. Please set SAMBANOVA_API_KEY."
    
    try:
        response = client_ai.chat.completions.create(
            model="DeepSeek-R1-0528",
            messages=[
                {"role": "system", "content": "You are a helpful learning assistant. Provide 'Golden Points' (very concise summary) for the following topic content. Use bullet points."},
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            top_p=0.1
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"SambaNova Error: {e}")
        return "Failed to generate AI summary."

def get_ai_mindmap(topics_data):
    if not client_ai:
        return "graph TD\nRoot[Cognitive Hub]"
    
    # Prepare a condensed list of topics for the LLM
    topics_list = []
    for t in topics_data:
        topics_list.append({
            "id": f"T{str(t['_id'])[-4:]}", # Use last 4 chars of ID for safety
            "name": t['name'],
            "subject": t['subject']
        })
    
    prompt = f"""
    Based on the following list of study topics, create a Mermaid.js Mind Map (graph TD).
    Group topics by their subjects first. 
    Create a logical flow or hierarchy if possible (e.g., math topics might lead to physics).
    
    Rules:
    1. Use 'graph TD' syntax.
    2. Start with a central node 'Root[Cognitive Hub]'.
    3. Connect subjects to Root.
    4. Connect topics to their respective subjects.
    5. VERY IMPORTANT: Only output the Mermaid code, nothing else. No markdown blocks.
    
    Topics: {json.dumps(topics_list)}
    """
    
    try:
        response = client_ai.chat.completions.create(
            model="DeepSeek-R1-0528",
            messages=[
                {"role": "system", "content": "You are a graph architect. You only output valid Mermaid.js graph code."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        content = response.choices[0].message.content.strip()
        # Clean up code blocks if LLM included them
        if "```mermaid" in content:
            content = content.split("```mermaid")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return content
    except Exception as e:
        print(f"Mindmap Error: {e}")
        return "graph TD\nRoot[Cognitive Hub]"

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if users_collection.find_one({'email': email}):
            flash('Email already exist!')
            return redirect(url_for('signup'))
        
        user_id = users_collection.insert_one({
            'username': username,
            'email': email,
            'password': password,
            'selected_subjects': []
        }).inserted_id
        
        return redirect(url_for('login'))
        
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_data = users_collection.find_one({'email': email, 'password': password})
        if user_data:
            user_obj = User(user_data)
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user_topics = list(topics_collection.find({'user_id': current_user.id}))
    # Apply decay on dashboard load for each topic
    for topic in user_topics:
        topic['confidence_score'] = apply_knowledge_decay(topic)
        topic['color'] = COLOR_MAP.get(topic['confidence_score'], '#FFFFFF')
        
    return render_template('dashboard.html', topics=user_topics, subjects=subject_choices)

@app.route('/add_topic', methods=['POST'])
@login_required
def add_topic():
    topic_name = request.form.get('topic_name')
    subject = request.form.get('subject')
    confidence = int(request.form.get('confidence', 3))
    
    topics_collection.insert_one({
        'user_id': current_user.id,
        'name': topic_name,
        'subject': subject,
        'confidence_score': confidence,
        'last_reviewed': datetime.datetime.utcnow(),
        'content': f"Detailed info on {topic_name}..." # Placeholder content
    })
    return redirect(url_for('dashboard'))

@app.route('/topic_details/<topic_id>')
@login_required
def topic_details(topic_id):
    topic = topics_collection.find_one({'_id': ObjectId(topic_id), 'user_id': current_user.id})
    if not topic:
        return "Topic not found", 404
        
    # Always generate summary on request
    summary = get_ai_summary(topic.get('content', 'No content available.'))
        
    return jsonify({
        'name': topic['name'],
        'summary': summary,
        'score': topic['confidence_score'],
        'color': COLOR_MAP.get(topic['confidence_score'], '#FFFFFF')
    })

@app.route('/api/mindmap')
@login_required
def api_mindmap():
    user_topics = list(topics_collection.find({'user_id': current_user.id}))
    if not user_topics:
        return jsonify({'graph': "graph TD\nRoot[Cognitive Hub]"})
    
    graph_code = get_ai_mindmap(user_topics)
    # Post-process to add colors (Mermaid styles)
    for topic in user_topics:
        tid = f"T{str(topic['_id'])[-4:]}"
        color = COLOR_MAP.get(topic.get('confidence_score', 3), '#FFFFFF')
        graph_code += f"\nstyle {tid} fill:{color},stroke:#333,stroke-width:2px,color:#000"
        
    return jsonify({'graph': graph_code})

@app.route('/study/<topic_id>')
@login_required
def study_topic(topic_id):
    topic = topics_collection.find_one({'_id': ObjectId(topic_id), 'user_id': current_user.id})
    if not topic:
        return "Topic not found", 404
        
    summary = get_ai_summary(topic.get('content', 'No content available.'))
    # Formatting for markdown if needed
    summary_html = summary.replace('\n', '<br>') if summary else ""
    # Map color
    topic['color'] = COLOR_MAP.get(topic.get('confidence_score', 3), '#FFFFFF')
        
    return render_template('study.html', topic=topic, summary=summary_html)

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    if not client_ai:
        return jsonify({'error': 'AI not configured.'}), 500
        
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'error': 'No message provided.'}), 400
        
    try:
        response = client_ai.chat.completions.create(
            model="DeepSeek-R1-0528",
            messages=[
                {"role": "system", "content": "You are a specialized Cognitive Learning Assistant for engineering students. Help them understand complex topics, solve problems, and suggest study plans. Be concise and encouraging."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1,
            top_p=0.1
        )
        return jsonify({'response': response.choices[0].message.content})
    except Exception as e:
        error_msg = str(e)
        print(f"Chat Error: {error_msg}")
        return jsonify({'error': 'AI is currently unavailable (SambaNova).'}), 500

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

SYLLABUS_TEMPLATES = {
    'Physics': [
        {'name': "Ohm's Law", 'content': "Ohm's law states that the current through a conductor between two points is directly proportional to the voltage across the two points. V=IR."},
        {'name': "Photoelectric Effect", 'content': "The ejection of electrons from a metal surface when light of sufficient frequency shines on it."}
    ],
    'C Programming': [
        {'name': "Pointers", 'content': "A pointer is a variable that stores the memory address of another variable."},
        {'name': "Recursion", 'content': "Recursion in C refers to the process where a function calls themselves, either directly or indirectly."}
    ],
    'Mathematics': [
        {'name': "Derivations", 'content': "Calculus focuses on limits, functions, derivatives, integrals, and infinite series."},
        {'name': "Linear Algebra", 'content': "Branch of mathematics concerning linear equations, linear maps, and their representations in vector spaces."}
    ],
    'Biology': [
        {'name': "Photosynthesis", 'content': "Process by which green plants and some other organisms use sunlight to synthesize foods from carbon dioxide and water."},
        {'name': "Cell Structure", 'content': "The cell is the basic structural, functional, and biological unit of all known organisms."}
    ],
    'Engineering Mechanics': [
        {'name': "Force Systems", 'content': "A system of forces where all forces act in the same plane. Includes tension, compression, and shear."},
        {'name': "Centroids", 'content': "The geometric center of a plane area or the point where the entire area can be considered to be concentrated."}
    ],
    'Electrical Engineering': [
        {'name': "Kirchhoff's Laws", 'content': "KCL: The algebraic sum of currents entering a node is zero. KVL: The algebraic sum of voltages in a loop is zero."},
        {'name': "Magnetic Circuits", 'content': "Reluctance, magnetomotive force (MMF), and flux density in ferromagnetic materials."}
    ],
    'Computer Programming': [
        {'name': "Data Structures", 'content': "Ways to organize and store data in a computer so that it can be accessed and modified efficiently. e.g. Arrays, Linked Lists."},
        {'name': "Algorithms", 'content': "A finite set of instructions to solve a particular problem. e.g. Sorting, Searching."}
    ]
}

@app.route('/pre_load_subjects', methods=['POST'])
@login_required
def pre_load_subjects():
    selected_subjects = request.form.getlist('subjects')
    for subj in selected_subjects:
        if subj in SYLLABUS_TEMPLATES:
            for topic in SYLLABUS_TEMPLATES[subj]:
                # Check if topic already exists for user
                if not topics_collection.find_one({'user_id': current_user.id, 'name': topic['name']}):
                    topics_collection.insert_one({
                        'user_id': current_user.id,
                        'name': topic['name'],
                        'subject': subj,
                        'confidence_score': 3,
                        'last_reviewed': datetime.datetime.utcnow(),
                        'content': topic['content']
                    })
    flash('Syllabus pre-loaded successfully!')
    return redirect(url_for('dashboard'))

@app.route('/review_topic/<topic_id>', methods=['POST'])
@login_required
def review_topic(topic_id):
    confidence = int(request.form.get('confidence', 3))
    topics_collection.update_one(
        {'_id': ObjectId(topic_id), 'user_id': current_user.id},
        {'$set': {
            'confidence_score': confidence,
            'last_reviewed': datetime.datetime.utcnow()
        }}
    )
    return redirect(url_for('dashboard'))

@app.route('/delete_topic/<topic_id>')
@login_required
def delete_topic(topic_id):
    topics_collection.delete_one({'_id': ObjectId(topic_id), 'user_id': current_user.id})
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
