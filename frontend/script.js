const API_URL = '/api';

// State
let subjects = [];
let activeSubject = null;
let activeTopic = null;

// DOM Elements
const views = document.querySelectorAll('.view');
const navItems = document.querySelectorAll('.nav-item');

// Init
document.addEventListener('DOMContentLoaded', () => {
    loadSubjects();
    initNavigation();
    initHeatmap();
    initTabs();
});

// Navigation
function initNavigation() {
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = item.getAttribute('href').substring(1) + '-view';
            showView(targetId);

            navItems.forEach(n => n.classList.remove('active'));
            item.classList.add('active');
        });
    });
}

function showView(viewId) {
    views.forEach(v => v.classList.remove('active'));
    document.getElementById(viewId).classList.add('active');
}

// Subjects & Topics
async function loadSubjects() {
    try {
        const res = await fetch(`${API_URL}/subjects/`);
        subjects = await res.json();
        renderSubjects();
        updateDashboardStats();
    } catch (err) {
        console.error('Error loading subjects:', err);
    }
}

function renderSubjects() {
    const grid = document.getElementById('subjects-grid');
    grid.innerHTML = '';

    subjects.forEach(subject => {
        const avgConfidence = subject.topics.length > 0
            ? subject.topics.reduce((acc, t) => acc + t.confidence, 0) / subject.topics.length
            : 0;

        const card = document.createElement('div');
        card.className = 'subject-card glass';
        card.innerHTML = `
            <h3>${subject.name}</h3>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${avgConfidence * 20}%"></div>
            </div>
            <div class="topic-count">${subject.topics.length} Topics</div>
            <button class="btn btn-secondary" onclick="viewSubject('${subject.name}')" style="margin-top:1rem; width:100%">Learn Now</button>
        `;
        grid.appendChild(card);
    });
}

function viewSubject(name) {
    activeSubject = subjects.find(s => s.name === name);
    showView('subjects-view'); // Redirecting to sub-topics in a real app, let's just use the first topic if exists
    if (activeSubject.topics.length > 0) {
        viewTopic(activeSubject.topics[0].name);
    } else {
        alert("Add some topics first!");
    }
}

async function viewTopic(topicName) {
    const topic = activeSubject.topics.find(t => t.name === topicName);
    activeTopic = topic;

    document.getElementById('active-topic-name').innerText = topic.name;
    const tag = document.getElementById('topic-confidence-tag');
    tag.innerText = topic.decay_status;
    tag.className = `tag ${topic.decay_status.toLowerCase().replace(' ', '-')}`;

    document.getElementById('topic-last-reviewed').innerHTML = `<i class="fas fa-clock"></i> Last reviewed: ${new Date(topic.last_reviewed).toLocaleDateString()}`;

    // Add confidence stars
    const meta = document.querySelector('.topic-meta');
    let starsHtml = '<div class="confidence-rating">';
    for (let i = 1; i <= 5; i++) {
        starsHtml += `<i class="fa${i <= topic.confidence ? 's' : 'r'} fa-star star" onclick="updateConfidence(${i})"></i>`;
    }
    starsHtml += '</div>';

    // Remove old rating div if exists
    const oldRating = document.querySelector('.confidence-rating');
    if (oldRating) oldRating.remove();
    meta.insertAdjacentHTML('beforeend', starsHtml);

    showView('topic-view');
    renderMindMap(topic.name);
}

async function updateConfidence(score) {
    if (!activeTopic || !activeSubject) return;

    try {
        const res = await fetch(`${API_URL}/subjects/${activeSubject.name}/topics/${activeTopic.name}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ confidence: score })
        });
        if (res.ok) {
            activeTopic.confidence = score;
            activeTopic.last_reviewed = new Date().toISOString();
            viewTopic(activeTopic.name);
            loadSubjects(); // Refresh overall data
        }
    } catch (err) {
        console.error('Error updating confidence:', err);
    }
}

// AI Generation
async function generateAI(type) {
    const topicName = activeTopic.name;
    const subjectName = activeSubject.name;
    const container = document.getElementById(`${type}-content`);

    // Show loading?

    try {
        if (type === 'mindmap' || type === 'flowchart') {
            const endpoint = type === 'mindmap' ? '/ai/mindmap' : '/ai/mindmap'; // reuse for now
            const res = await fetch(`${API_URL}${endpoint}?topic=${encodeURIComponent(topicName)}&subject=${encodeURIComponent(subjectName)}`, {
                method: 'POST'
            });
            const data = await res.json();

            const target = document.getElementById(`${type}-container`);
            target.removeAttribute('data-processed');
            target.innerHTML = data.mermaid_code;
            mermaid.contentLoaded();
        } else if (type === 'flashcards') {
            const res = await fetch(`${API_URL}/ai/flashcards?topic=${encodeURIComponent(topicName)}`, {
                method: 'POST'
            });
            const data = await res.json();
            renderFlashcards(data.flashcards);
        } else if (type === 'summary') {
            const res = await fetch(`${API_URL}/ai/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: "Generate a summary and golden points for this topic.", topic: topicName, subject: subjectName })
            });
            const data = await res.json();
            document.getElementById('ai-summary-text').innerText = data.reply;
        }
    } catch (err) {
        console.error(`Error generating ${type}:`, err);
    }
}

function renderFlashcards(cards) {
    const stack = document.getElementById('flashcard-stack');
    stack.innerHTML = '';

    cards.forEach((card, index) => {
        const fc = document.createElement('div');
        fc.className = 'flashcard';
        fc.innerHTML = `
            <div class="front">${card.front}</div>
            <div class="back" style="display:none">${card.back}</div>
        `;
        fc.onclick = () => {
            const front = fc.querySelector('.front');
            const back = fc.querySelector('.back');
            if (front.style.display === 'none') {
                front.style.display = 'block';
                back.style.display = 'none';
            } else {
                front.style.display = 'none';
                back.style.display = 'block';
            }
        };
        stack.appendChild(fc);
    });
}

// Tabs
function initTabs() {
    const btns = document.querySelectorAll('.tab-btn');
    const contents = document.querySelectorAll('.topic-content');

    btns.forEach(btn => {
        btn.addEventListener('click', () => {
            btns.forEach(b => b.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            document.getElementById(`${btn.dataset.tab}-content`).classList.add('active');

            if (btn.dataset.tab === 'mindmap' || btn.dataset.tab === 'flowchart') {
                // Trigger mermaid render if needed
            }
        });
    });
}

// Dashboard Logic
function initHeatmap() {
    const grid = document.getElementById('confidence-heatmap');
    grid.innerHTML = '';
    for (let i = 0; i < 48; i++) {
        const box = document.createElement('div');
        const levels = ['v-weak', 'weak', 'medium', 'strong', 'none'];
        const level = levels[Math.floor(Math.random() * 5)];
        box.className = `heat-box ${level}`;
        grid.appendChild(box);
    }
}

function updateDashboardStats() {
    let weakCount = 0;
    let totalScore = 0;
    let totalTopics = 0;

    subjects.forEach(s => {
        s.topics.forEach(t => {
            if (t.decay_status === 'Weak') weakCount++;
            totalScore += t.confidence;
            totalTopics++;
        });
    });

    document.querySelector('.weak-topics .stat-value').innerText = weakCount;
    document.querySelector('.confidence-score .stat-value').innerText = totalTopics > 0 ? (totalScore / totalTopics).toFixed(1) + ' / 5' : 'N/A';
}

// Modals
function showAddSubjectModal() {
    document.getElementById('add-subject-modal').style.display = 'block';
}

function closeModal(id) {
    document.getElementById(id).style.display = 'none';
}

async function saveSubject() {
    const name = document.getElementById('new-subject-name').value;
    const topicStr = document.getElementById('new-subject-topics').value;
    const topics = topicStr.split(',').map(t => ({ name: t.trim(), confidence: 1 }));

    if (!name) return;

    try {
        const res = await fetch(`${API_URL}/subjects/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, topics })
        });
        if (res.ok) {
            closeModal('add-subject-modal');
            loadSubjects();
        }
    } catch (err) {
        console.error('Error saving subject:', err);
    }
}

// Chat AI
async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const msg = input.value;
    if (!msg) return;

    const history = document.getElementById('chat-history');
    history.innerHTML += `<div class="msg user"><b>You:</b> ${msg}</div>`;
    input.value = '';

    try {
        const res = await fetch(`${API_URL}/ai/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg, subject: activeSubject?.name, topic: activeTopic?.name })
        });
        const data = await res.json();
        history.innerHTML += `<div class="msg ai"><b>AI:</b> ${data.reply}</div>`;
        history.scrollTop = history.scrollHeight;
    } catch (err) {
        console.error('Chat error:', err);
    }
}
