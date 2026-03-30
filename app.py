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
import PyPDF2
import io
import re
import docx

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "clh-secret-dev-key")

# MongoDB Setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client['clh_db']
users_collection = db['users']
topics_collection = db['topics']
documents_collection = db['documents']
def get_available_subjects():
    sources_dir = os.path.join(os.path.dirname(__file__), 'sources')
    if not os.path.exists(sources_dir):
        return []
    # Return list of subdirectories (subjects)
    return [d for d in os.listdir(sources_dir) if os.path.isdir(os.path.join(sources_dir, d))]

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
            model="Meta-Llama-3.1-8B-Instruct",
            messages=[
                {"role": "system", "content": "You are a helpful learning assistant. Provide 'Golden Points' (very concise summary) for the following topic content. Use bullet points."},
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            top_p=0.1
        )
        return response.choices[0].message.content
    except Exception as e:
        error_msg = str(e)
        print(f"SambaNova Error: {error_msg}")
        if "rate limit" in error_msg.lower():
            return "AI Rate Limit Reached (429). Please wait a few minutes before trying again."
        return f"Failed to generate AI summary. (Error: {error_msg})"

def sanitize_mermaid(text):
    """Clean up AI-generated Mermaid code."""
    if not text:
        return "graph TD\nRoot[\"Error\"]"
    
    # Remove markdown code blocks if present
    if "```mermaid" in text:
        text = text.split("```mermaid")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    
    # Sanitize labels: Mermaid labels are sensitive to certain chars
    # We look for nodes with labels in brackets A["Label"]
    def clean_label(match):
        node_id = match.group(1)
        label = match.group(2)
        # Escape double quotes inside labels
        label = label.replace('"', "'")
        # Remove other problematic symbols
        label = re.sub(r'[\[\]\(\)\{\}#]', '', label)
        return f'{node_id}["{label}"]'
    
    # Matches A["Label"] or A[Label]
    text = re.sub(r'(\w+)\s*\["?(.*?)"?\]', clean_label, text)
    
    # Ensure it starts with graph TD if not specified
    if "graph " not in text.lower():
        text = "graph TD\n" + text
        
    return text

PHOTONICS_MAP = """
graph TD
    Root["PHOTONICS"]
    
    Root --> C1["1. Introduction"]
    C1 --> C1a["Definition"]
    C1 --> C1b["Optics"]
    C1 --> C1c["Quantum Mechanics"]
    C1 --> C1d["Electromagnetism"]
    
    Root --> C2["2. Advantages over Electronics"]
    C2 --> C2a["High Bandwidth"]
    C2 --> C2b["Low Power Consumption"]
    C2 --> C2c["Increased Security"]
    C2 --> C2d["Higher Reliability"]
    
    Root --> C3["3. Photodetectors"]
    C3 --> C3a["Types"]
    C3a --> C3a1["Junction Photodiode"]
    C3a --> C3a2["PIN Photodiode"]
    C3a --> C3a3["Avalanche Photodiode"]
    C3a --> C3a4["Schottky Photodiode"]
    C3a --> C3a5["Phototransistors"]
    C3 --> C3b["Requirements"]
    C3b --> C3b1["High Sensitivity"]
    C3b --> C3b2["Short Response Time"]
    C3b --> C3b3["Low Bias Voltage"]
    
    Root --> C4["4. Solar Cells"]
    C4 --> C4a["Photovoltaic Effect"]
    C4 --> C4b["I-V Characteristics"]
    C4b --> C4b1["Open Circuit Voltage"]
    C4b --> C4b2["Short Circuit Current"]
    C4b --> C4b3["Maximum Power Point"]
    C4b --> C4b4["Fill Factor"]
    C4b --> C4b5["Efficiency"]
    C4 --> C4c["Configuration"]
    C4c --> C4c1["Series Stringing"]
    C4c --> C4c2["Parallel Stringing"]
    C4 --> C4d["Pros and Cons"]
    C4d --> C4d1["No Pollution"]
    C4d --> C4d2["Low Maintenance"]
    C4d --> C4d3["Brittle Material"]
    C4d --> C4d4["Space Intensive"]
    
    Root --> C5["5. Light Emitting Diodes (LED)"]
    C5 --> C5a["Electron-hole Recombination"]
    C5 --> C5b["Materials and Color"]
    C5b --> C5b1["GaAs – Infrared"]
    C5b --> C5b2["GaAsP – Yellow"]
    C5b --> C5b3["GaP – Green"]
    C5 --> C5c["Features"]
    C5c --> C5c1["Point Source"]
    C5c --> C5c2["Fast Switching"]
    C5c --> C5c3["Long Lifespan"]
    
    Root --> C6["6. Applications"]
    C6 --> C6a["Communication"]
    C6 --> C6b["Medicine"]
    C6 --> C6c["Consumer Electronics"]
    C6 --> C6d["Satellites"]
    C6 --> C6e["Automotive Lighting"]
"""

def get_ai_mindmap(topics_data, context="global", target_name=None):
    # Static override for Photonics while AI is rate-limited
    if target_name and "photonics" in target_name.lower():
        return PHOTONICS_MAP
        
    if not client_ai:
        return "graph TD\nRoot[Cognitive Hub]"
    
    if context == "topic":
        # Mind map for a single topic (breaking it down)
        content = topics_data[0].get('content', '') if topics_data else ''
        prompt = f"""
        Create a detailed Mermaid.js Mind Map (graph TD) for the topic: '{target_name}'.
        Break down this topic into 5-8 logical sub-concepts or key points based on this content:
        {content}
        
        Rules:
        1. Use 'graph TD' syntax.
        2. Start with a central node Root["{target_name}"].
        3. Connect sub-concepts directly to Root.
        4. CRITICAL: Use DOUBLE QUOTES for all labels like: A["Label Name"].
        5. CRITICAL: Avoid using symbols like [], (), {{}}, or # inside labels. Use plain text and dots only.
        6. VERY IMPORTANT: Only output the Mermaid code, nothing else. No markdown blocks.
        """
    else:
        # Prepare a condensed list of topics for the LLM
        topics_list = []
        for t in topics_data:
            topics_list.append({
                "id": f"T{str(t['_id'])[-4:]}", 
                "name": t['name'],
                "subject": t['subject']
            })
        
        scope = f"for the subject '{target_name}'" if context == "subject" else "for all my study topics"
        prompt = f"""
        Based on the following list of study topics {scope}, create a Mermaid.js Mind Map (graph TD).
        
        Rules:
        1. Use 'graph TD' syntax.
        2. Start with a central node Root["{target_name if target_name else "Cognitive Hub"}"].
        3. Connect subjects to Root (if global) or themes to Root (if subject-specific).
        4. CRITICAL: Use the provided 'id' keys as the node identifiers in your graph code. 
           Example: {topics_list[0]['id'] if topics_list else "T123"}["Topic Name"].
        5. Connect topics to their respective parents.
        6. CRITICAL: Use DOUBLE QUOTES for all labels like: A["Label Name"].
        7. CRITICAL: Avoid using symbols like [], (), {{}}, or # inside labels.
        8. VERY IMPORTANT: Only output the Mermaid code, nothing else. No markdown blocks.
        
        Topics: {json.dumps(topics_list)}
        """
    
    try:
        response = client_ai.chat.completions.create(
            model="Meta-Llama-3.1-8B-Instruct",
            messages=[
                {"role": "system", "content": "You are a graph architect. You only output valid Mermaid.js graph code."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        content = sanitize_mermaid(response.choices[0].message.content.strip())
        
        # Ensure the AI actually produced a graph definition
        if "graph " not in content:
            return f"graph TD\nRoot[\"{target_name if target_name else 'Cognitive Hub'}\"]"
            
        return content
    except Exception as e:
        print(f"Mindmap Error: {e}")
        return f"graph TD\nRoot[{target_name if target_name else 'Cognitive Hub'}]"

def get_ai_mindmap_json(text, target_name="Mind Map"):
    """
    Generate a JSON-based hierarchy for Mind-Elixir.
    """
    if not client_ai:
        return {"id": "root", "topic": "AI Not Configured", "root": True}
    
    prompt = f"""
    Create a deep hierarchical Mind Map in JSON format for the topic: '{target_name}'.
    Analyze the following text and extract 5-10 main branches, each with 2-4 sub-branches.
    
    Rules:
    1. Output ONLY a valid JSON object.
    2. Every node MUST have an 'id' and 'topic' (the label).
    3. Use 'children': [...] for sub-nodes.
    4. The root node must have "root": true.
    5. Be professional and academic.
    
    Text: {text[:15000]}
    
    Example Structure:
    {{
      "id": "root",
      "topic": "{target_name}",
      "root": true,
      "children": [
        {{ "id": "1", "topic": "Theme 1", "children": [...] }}
      ]
    }}
    """
    
    try:
        response = client_ai.chat.completions.create(
            model="Meta-Llama-3.1-8B-Instruct",
            messages=[
                {"role": "system", "content": "You are a JSON graph architect. You only output valid JSON. No markdown blocks."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        resp = response.choices[0].message.content.strip()
        if "```json" in resp: resp = resp.split("```json")[1].split("```")[0].strip()
        elif "```" in resp: resp = resp.split("```")[1].split("```")[0].strip()
        
        return json.loads(resp)
    except Exception as e:
        print(f"JSON Mindmap Error: {e}")
        return {"id": "root", "topic": f"Error: {str(e)}", "root": True}

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
        
    return render_template('dashboard.html', topics=user_topics, subjects=get_available_subjects())

@app.route('/mindmap_pro')
@login_required
def mindmap_pro():
    docs = list(documents_collection.find({'user_id': current_user.id}))
    return render_template('mindmap_pro.html', documents=docs)

@app.route('/api/mindmap/pro', methods=['POST'])
@login_required
def api_mindmap_pro():
    if not client_ai:
        return jsonify({'error': 'AI not configured.'}), 500
        
    source_type = request.json.get('source_type') # 'text' or 'doc_id'
    target_name = "New Exploration"
    content = ""
    
    if source_type == 'doc_id':
        doc_id = request.json.get('doc_id')
        doc = documents_collection.find_one({'_id': ObjectId(doc_id), 'user_id': current_user.id})
        if doc:
            content = doc['content']
            target_name = doc['filename']
    else:
        content = request.json.get('text', '')
        target_name = request.json.get('name', 'My Note')
        
    if not content:
        return jsonify({'error': 'No content provided.'}), 400
        
    mind_data = get_ai_mindmap_json(content, target_name)
    return jsonify({'nodeData': mind_data})

@app.route('/add_topic', methods=['GET', 'POST'])
@login_required
def add_topic():
    if request.method == 'GET':
        return redirect(url_for('dashboard'))
    
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

@app.context_processor
def inject_subjects():
    return dict(get_available_subjects=get_available_subjects())

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
    subject = request.args.get('subject')
    query = {'user_id': current_user.id}
    if subject and subject != 'All':
        query['subject'] = subject
        
    user_topics = list(topics_collection.find(query))
    if not user_topics:
        return jsonify({'graph': f"graph TD\nRoot[{subject if subject else 'Cognitive Hub'}]"})
    
    context = "subject" if subject and subject != 'All' else "global"
    graph_code = get_ai_mindmap(user_topics, context=context, target_name=subject)
    
    # Post-process to add colors (Mermaid styles)
    for topic in user_topics:
        tid = f"T{str(topic['_id'])[-4:]}"
        # ONLY add style if the node exists in the graph to avoid syntax errors
        if tid in graph_code:
            color = COLOR_MAP.get(topic.get('confidence_score', 3), '#FFFFFF')
            graph_code += f"\nstyle {tid} fill:{color},stroke:#333,stroke-width:2px,color:#000"
        
    return jsonify({'graph': graph_code})

@app.route('/api/topic_mindmap/<topic_id>')
@login_required
def api_topic_mindmap(topic_id):
    topic = topics_collection.find_one({'_id': ObjectId(topic_id), 'user_id': current_user.id})
    if not topic:
        return jsonify({'error': 'Topic not found'}), 404
        
    graph_code = get_ai_mindmap([topic], context="topic", target_name=topic['name'])
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
            model="Meta-Llama-3.1-8B-Instruct",
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

# Removed SYLLABUS_TEMPLATES as requested. Loading from files now.

@app.route('/pre_load_subjects', methods=['GET', 'POST'])
@login_required
def pre_load_subjects():
    if request.method == 'GET':
        return redirect(url_for('dashboard'))
    
    selected_subjects = request.form.getlist('subjects')
    sources_dir = os.path.join(os.path.dirname(__file__), 'sources')
    
    # Remove existing preloaded data for the current user to start fresh
    topics_collection.delete_many({'user_id': current_user.id})
    
    for subj in selected_subjects:
        subj_path = os.path.join(sources_dir, subj)
        if os.path.isdir(subj_path):
            # Each file in this directory is a "Module / Topic"
            for filename in os.listdir(subj_path):
                file_path = os.path.join(subj_path, filename)
                if os.path.isfile(file_path):
                    # Extract module name from filename (e.g. photonics.txt -> Photonics)
                    topic_name = os.path.splitext(filename)[0].title()
                    
                    # Check if topic already exists for user
                    if not topics_collection.find_one({'user_id': current_user.id, 'name': topic_name, 'subject': subj}):
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                            
                            topics_collection.insert_one({
                                'user_id': current_user.id,
                                'name': topic_name,
                                'subject': subj,
                                'confidence_score': 3,
                                'last_reviewed': datetime.datetime.utcnow(),
                                'content': content
                            })
                        except Exception as e:
                            print(f"Error reading {file_path}: {e}")
                            
    flash(f'Syllabus documents loaded successfully from sources!')
    return redirect(url_for('dashboard'))

@app.route('/review_topic/<topic_id>', methods=['GET', 'POST'])
@login_required
def review_topic(topic_id):
    if request.method == 'GET':
        return redirect(url_for('dashboard'))
    
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

# --- Document Workspace / Special AI Section ---

@app.route('/workspace')
@login_required
def workspace():
    user_docs = list(documents_collection.find({'user_id': current_user.id}))
    return render_template('workspace.html', documents=user_docs)

@app.route('/upload_document', methods=['GET', 'POST'])
@login_required
def upload_document():
    if request.method == 'GET':
        return redirect(url_for('workspace'))
    
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('workspace'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('workspace'))

    text = ""
    filename = file.filename
    
    try:
        if filename.endswith('.pdf'):
            reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif filename.endswith('.docx'):
            doc = docx.Document(io.BytesIO(file.read()))
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif filename.endswith('.txt'):
            text = file.read().decode('utf-8')
        else:
            flash('Unsupported file type (PDF/DOCX/TXT only)')
            return redirect(url_for('workspace'))
            
        if not text.strip():
            flash('Empty document or failed to extract text.')
            return redirect(url_for('workspace'))

        doc_id = documents_collection.insert_one({
            'user_id': current_user.id,
            'filename': filename,
            'content': text,
            'timestamp': datetime.datetime.utcnow()
        }).inserted_id
        
        flash(f'Document "{filename}" uploaded and processed!')
        return redirect(url_for('workspace'))
    except Exception as e:
        print(f"Upload Error: {e}")
        flash('Error processing document.')
        return redirect(url_for('workspace'))

@app.route('/api/workspace/generate', methods=['GET', 'POST'])
@login_required
def workspace_generate():
    if request.method == 'GET':
        return redirect(url_for('workspace'))
        
    if not client_ai:
        return jsonify({'error': 'AI not configured.'}), 500
        
    doc_id = request.json.get('doc_id')
    type_requested = request.json.get('type') # 'mindmap', 'flowchart', 'flashcards', 'study_guide', 'faq'
    
    doc = documents_collection.find_one({'_id': ObjectId(doc_id), 'user_id': current_user.id})
    if not doc:
        return jsonify({'error': 'Document not found.'}), 404
        
    content = doc['content'][:15000] # Limit content length for prompt safety
    
    system_prompts = {
        'mindmap': "You are an expert at information visualization. Output ONLY valid Mermaid.js mindmap code (graph TD). Use DOUBLE QUOTES for labels: A[\"Label\"]. Avoid [],(),{},# inside labels. Use provided text AS ONLY SOURCE OF TRUTH.",
        'flowchart': "You are a process visualization expert. Output ONLY valid Mermaid.js flowchart code (graph LR). Use DOUBLE QUOTES for labels: A[\"Label\"]. Avoid [],(),{},# inside labels. Use provided text AS ONLY SOURCE OF TRUTH.",
        'flashcards': "You are a memory specialist. Output 5-8 flashcards as a JSON array of objects with 'question' and 'answer' fields. Use provided text AS ONLY SOURCE OF TRUTH.",
        'study_guide': "You are an academic tutor. Create a comprehensive study guide with key definitions, concepts, and a summary. Use Markdown.",
        'faq': "You are an educator. Create 5-10 Frequently Asked Questions and their detailed answers based on the text. Use Markdown."
    }
    
    prompt_templates = {
        'mindmap': f"Create a comprehensive mind map of the following text:\n\n{content}",
        'flowchart': f"Convert the logic or process in the following text into a flowchart:\n\n{content}",
        'flashcards': f"Generate high-quality study flashcards based on the following text:\n\n{content}",
        'study_guide': f"Create a detailed study guide for the following text:\n\n{content}",
        'faq': f"Create an FAQ based on the following text:\n\n{content}"
    }
    
    try:
        response = client_ai.chat.completions.create(
            model="Meta-Llama-3.1-8B-Instruct",
            messages=[
                {"role": "system", "content": system_prompts.get(type_requested, "Help the student.")},
                {"role": "user", "content": prompt_templates.get(type_requested, "N/A")}
            ],
            temperature=0.1
        )
        ai_resp = sanitize_mermaid(response.choices[0].message.content.strip()) if type_requested in ['mindmap', 'flowchart'] else response.choices[0].message.content.strip()
        
        if type_requested == 'flashcards':
            if "```json" in ai_resp:
                ai_resp = ai_resp.split("```json")[1].split("```")[0].strip()
            elif "```" in ai_resp:
                ai_resp = ai_resp.split("```")[1].split("```")[0].strip()
            # Try to return as JSON if possible
            try:
                ai_resp = json.loads(ai_resp)
            except:
                pass

        return jsonify({'result': ai_resp})
    except Exception as e:
        print(f"Workspace AI Error: {e}")
        return jsonify({'error': 'AI failed to process the document.'}), 500

@app.route('/api/workspace/chat', methods=['POST'])
@login_required
def workspace_chat():
    if not client_ai:
        return jsonify({'error': 'AI not configured.'}), 500
        
    doc_id = request.json.get('doc_id')
    user_message = request.json.get('message')
    
    doc = documents_collection.find_one({'_id': ObjectId(doc_id), 'user_id': current_user.id})
    if not doc:
        return jsonify({'error': 'Document not found.'}), 404
        
    content = doc['content'][:15000]
    
    try:
        response = client_ai.chat.completions.create(
            model="Meta-Llama-3.1-8B-Instruct",
            messages=[
                {"role": "system", "content": f"You are a helpful AI assistant grounded in the following document: {doc['filename']}. Answer questions ONLY based on this content:\n\n{content}"},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1
        )
        return jsonify({'response': response.choices[0].message.content})
    except Exception as e:
        print(f"Workspace Chat Error: {e}")
        return jsonify({'error': 'AI failed to answer.'}), 500

@app.route('/delete_document/<doc_id>')
@login_required
def delete_document(doc_id):
    documents_collection.delete_one({'_id': ObjectId(doc_id), 'user_id': current_user.id})
    return redirect(url_for('workspace'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
