const API_URL = '/api';

// State
let subjects = [];
let activeSubject = null;
let activeMindMapRoot = null;
let activeTopicNode = null;
let expandedNodes = new Set();
let searchQuery = "";
let activeFlashcards = [];
let currentUser = JSON.parse(localStorage.getItem('clh_user')) || null;
let authMode = 'login'; // login or register

// Init
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    initSearch();
});

function checkAuth() {
    const overlay = document.getElementById('auth-overlay');
    const app = document.getElementById('app-container');

    if (currentUser) {
        if (overlay) overlay.classList.add('hidden');
        if (app) app.classList.remove('blur-xl', 'pointer-events-none');
        initApp();
        updateUserProfile();
        showView('dashboard-view');
        initDashboard();
    } else {
        if (overlay) overlay.classList.remove('hidden');
    }
}

async function initApp() {
    await fetchSubjects();
    populateSubjectDropdown();
    populateFlashSubjectDropdown();
}

function updateUserProfile() {
    // ALWAYS display Raj Raswin (as per user request)
    const nameEl = document.getElementById('user-profile-name');
    const roleEl = document.getElementById('user-profile-role');
    const initialsEl = document.getElementById('user-initials-circle');

    if (!nameEl || !roleEl || !initialsEl) return;

    nameEl.innerText = "Raj Raswin";
    roleEl.innerText = "Pro Student";
    initialsEl.innerText = "RR";
}

// View Logic Fix
function showView(viewId) {
    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));

    // Fix for style tags in Sidebar
    document.querySelectorAll('nav a').forEach(a => {
        a.classList.remove('bg-blue-600/20', 'text-blue-400', 'border-blue-500/30');
        a.classList.add('hover:bg-white/5', 'text-slate-400');
    });

    const target = document.getElementById(viewId);
    if (target) {
        target.classList.remove('hidden');
        target.classList.add('active');

        // Update Sidebar Active State
        const sidebarLink = document.querySelector(`a[onclick="showView('${viewId}')"]`);
        if (sidebarLink) {
            // Check if it's flashcards to use orange
            if (viewId === 'flashcards-view') {
                sidebarLink.classList.add('bg-orange-600/20', 'text-orange-400', 'border-orange-500/30');
            } else {
                sidebarLink.classList.add('bg-blue-600/20', 'text-blue-400', 'border-blue-500/30');
            }
            sidebarLink.classList.remove('hover:bg-white/5', 'text-slate-400');
        }

        if (viewId === 'mindmap-view' && !activeSubject) {
            resetSetup();
        }
        if (viewId === 'flashcards-view') {
            resetFlashSetup();
        }
        if (viewId === 'dashboard-view') {
            initDashboard();
        }
    }
}

// Stats & Charts
function initDashboard() {
    const ctx = document.getElementById('retentionChart');
    if (!ctx) return;

    // Destroy existing chart if any
    if (window.myRetentionChart) window.myRetentionChart.destroy();

    window.myRetentionChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Memory Retention',
                data: [65, 78, 72, 85, 82, 88, 92],
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4,
                borderWidth: 3,
                pointRadius: 4,
                pointBackgroundColor: '#3b82f6'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { display: false, min: 0, max: 100 },
                x: {
                    grid: { display: false },
                    ticks: { color: '#64748b', font: { size: 10, weight: 'bold' } }
                }
            }
        }
    });
}

// Data Fetching
async function fetchSubjects() {
    try {
        console.log('Fetching subjects from:', API_URL + '/subjects/');
        const res = await fetch(`${API_URL}/subjects/`);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        subjects = await res.json();
        console.log('Loaded subjects:', subjects);
        if (subjects.length === 0) {
            console.warn('No subjects returned from API. Check if DB is empty or seeded corectly.');
        }
    } catch (err) {
        console.error('Error loading subjects:', err);
    }
}

function populateSubjectDropdown() {
    const select = document.getElementById('subject-select');
    if (!select) return;

    if (subjects.length === 0) {
        select.innerHTML = '<option value="" disabled selected>No Subjects Available</option>';
        return;
    }

    select.innerHTML = '<option value="" disabled selected>Select Subject</option>';
    subjects.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.name;
        opt.innerText = s.name;
        select.appendChild(opt);
    });
}

function updateTopicDropdown() {
    const subjectName = document.getElementById('subject-select').value;
    const topicSelect = document.getElementById('topic-select');
    const selectedSub = subjects.find(s => s.name === subjectName);

    if (!selectedSub) return;

    topicSelect.innerHTML = '<option value="" disabled selected>Select Topic</option>';
    selectedSub.topics.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.title;
        opt.innerText = t.title;
        topicSelect.appendChild(opt);
    });
}

// Step 3: Simulation
async function generateMindMapAction() {
    const subName = document.getElementById('subject-select').value;
    const topicName = document.getElementById('topic-select').value;

    if (!subName || !topicName) {
        alert("Please select both a subject and a topic.");
        return;
    }

    // New generation starts: clear state
    expandedNodes.clear();

    // UI Transition
    document.getElementById('mindmap-setup').classList.add('hidden');
    document.getElementById('mindmap-loading').classList.remove('hidden');

    const loaderMsg = document.getElementById('loading-messages');
    const messages = [
        "Generating Mind Map...",
        "Analyzing Topic...",
        "Extracting Concepts...",
        "Building Knowledge Graph..."
    ];

    // Simulate AI Generation (2 seconds total: 4 messages * 500ms)
    for (let i = 0; i < messages.length; i++) {
        loaderMsg.innerText = messages[i];
        await new Promise(r => setTimeout(r, 500));
    }

    // Set Active State
    activeSubject = subjects.find(s => s.name === subName);
    const rootTopic = activeSubject.topics.find(t => t.title === topicName);

    displayGeneratedMap(subName, rootTopic);
}

function displayGeneratedMap(subjectName, rootTopic) {
    document.getElementById('mindmap-loading').classList.add('hidden');
    document.getElementById('mindmap-content').classList.remove('hidden');

    activeMindMapRoot = rootTopic;

    // Set Header
    document.getElementById('current-subject-title').innerText = `${subjectName} Mind Map`;

    // Setup tree
    const treeRoot = document.getElementById('tree-root');
    treeRoot.innerHTML = '';

    // Automatically expand the first level of children for better visibility
    if (rootTopic.children) {
        rootTopic.children.forEach((child, idx) => {
            const id = `gen-root-${idx}`;
            if (!expandedNodes.has(id)) expandedNodes.add(id); // Expand by default if not already interacted with
            treeRoot.appendChild(createTreeNode(child, 0, id));
        });
    } else {
        treeRoot.appendChild(createTreeNode(rootTopic, 0, 'gen-root'));
    }

    const count = countAllNodes([rootTopic]);
    document.getElementById('topic-count-stats').innerText = `${count} Nodes Analyzed`;

    // Reset notes
    document.getElementById('notes-empty-state').classList.remove('hidden');
    document.getElementById('active-note-view').classList.add('hidden');
}

function resetSetup() {
    document.getElementById('mindmap-setup').classList.remove('hidden');
    document.getElementById('mindmap-loading').classList.add('hidden');
    document.getElementById('mindmap-content').classList.add('hidden');

    // Reset dropdowns if needed
    document.getElementById('subject-select').value = "";
    document.getElementById('topic-select').innerHTML = '<option value="" disabled selected>Select subject first</option>';
}

// Tree Rendering
function renderTree() {
    const treeRoot = document.getElementById('tree-root');
    // For the generated map, activeSubject is set but we use the selected topic as root
    // This is handled in displayGeneratedMap.
    // Searching/filtering will refresh the current root.
}

function countAllNodes(nodes) {
    let count = 0;
    nodes.forEach(node => {
        count++;
        if (node.children && node.children.length > 0) {
            count += countAllNodes(node.children);
        }
    });
    return count;
}

function createTreeNode(topic, depth, id) {
    const container = document.createElement('div');
    container.className = 'tree-node flex flex-col';

    const hasChildren = topic.children && topic.children.length > 0;
    const isExpanded = expandedNodes.has(id) || (searchQuery && hasChildren);

    // Confidence Color
    let statusClass = "status-green";
    if (topic.confidence <= 1) statusClass = "status-red";
    else if (topic.confidence <= 3) statusClass = "status-yellow";

    const nodeContent = document.createElement('div');
    nodeContent.className = `tree-node-content flex items-center gap-2 py-2 px-3 rounded-lg cursor-pointer transition-all duration-200 group`;
    nodeContent.style.marginLeft = `${depth * 1.5}rem`;

    const arrowIcon = hasChildren
        ? `<i class="fas fa-caret-right text-slate-500 transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}"></i>`
        : `<i class="fas fa-circle text-[6px] text-slate-700 ml-1 mr-1"></i>`;

    nodeContent.innerHTML = `
        <div class="flex items-center gap-2 flex-1">
            <span class="w-4 flex justify-center">${arrowIcon}</span>
            <span class="${statusClass} status-dot"></span>
            <span class="text-sm font-medium ${hasChildren ? 'text-slate-200' : 'text-slate-400'} group-hover:text-white transition-colors">
                ${topic.title}
            </span>
        </div>
    `;

    nodeContent.onclick = (e) => {
        e.stopPropagation();
        if (hasChildren && e.target.closest('.fa-caret-right')) {
            toggleNode(id, topic);
        } else {
            selectTopic(topic);
            if (hasChildren && !isExpanded) toggleNode(id, topic);
        }
    };

    container.appendChild(nodeContent);

    if (hasChildren && isExpanded) {
        const childrenContainer = document.createElement('div');
        childrenContainer.className = 'children-container flex flex-col mt-1';
        topic.children.forEach((child, idx) => {
            childrenContainer.appendChild(createTreeNode(child, depth + 1, `${id}-${idx}`));
        });
        container.appendChild(childrenContainer);
    }

    return container;
}

function toggleNode(id, topic) {
    if (expandedNodes.has(id)) {
        expandedNodes.delete(id);
    } else {
        expandedNodes.add(id);
    }
    // Simple re-render of the specific root
    displayGeneratedMap(activeSubject.name, activeMindMapRoot);
}

function selectTopic(topic) {
    activeTopicNode = topic;

    document.getElementById('notes-empty-state').classList.add('hidden');
    const view = document.getElementById('active-note-view');
    view.classList.remove('hidden');

    document.getElementById('note-title').innerText = topic.title;

    const badge = document.getElementById('note-status-badge');
    let statusText = "Strong";
    let badgeClass = "bg-green-500/20 text-green-400 border-green-500/20";

    if (topic.confidence <= 1) {
        statusText = "Weak";
        badgeClass = "bg-red-500/20 text-red-400 border-red-500/20";
    } else if (topic.confidence <= 3) {
        statusText = "Medium";
        badgeClass = "bg-yellow-500/20 text-yellow-400 border-yellow-500/20";
    }

    badge.innerText = statusText;
    badge.className = `px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${badgeClass}`;

    const notesContainer = document.getElementById('note-sections-container');
    notesContainer.innerHTML = '';

    if (topic.note) {
        renderTopicNote(topic.note);
    } else {
        document.getElementById('note-description').innerText = "Generating AI Core Definition...";
        fetch(`${API_URL}/ai/topic_info?topic=${encodeURIComponent(topic.title)}&subject=${encodeURIComponent(activeSubject ? activeSubject.name : '')}`, {
            method: 'POST'
        })
            .then(res => res.json())
            .then(data => {
                if (data.note) {
                    topic.note = data.note; // Cache it
                    renderTopicNote(data.note);
                }
            })
            .catch(err => {
                document.getElementById('note-description').innerText = "AI Assistant is currently offline. Definition unavailable.";
            });
    }

    document.getElementById('note-confidence-val').innerText = (topic.confidence * 0.96).toFixed(1);
    document.getElementById('note-confidence-bar').style.width = `${topic.confidence * 20}%`;
}

function renderTopicNote(note) {
    const notesContainer = document.getElementById('note-sections-container');
    notesContainer.innerHTML = '';

    let points = [];
    if (note.includes('\n')) {
        points = note.split('\n').filter(p => p.trim().length > 0);
    } else {
        points = note.split('.').filter(p => p.trim().length > 0).map(p => p.trim());
    }

    // Set top highlight note
    document.getElementById('note-description').innerText = points[0] || "";

    // Add additional points as bullet sections
    if (points.length > 1) {
        points.slice(1).forEach((p, index) => {
            let title = `Key Insight ${index + 1}`;
            let content = p;

            // Try to extract a title if the AI formatted it with ":"
            if (p.includes(':')) {
                const parts = p.split(':');
                if (parts[0].length < 30) { // Only if it looks like a title
                    title = parts[0].trim();
                    content = parts.slice(1).join(':').trim();
                }
            }
            // Clean up common bullet prefixes
            content = content.replace(/^[-*•]\s+/, '');
            title = title.replace(/^[-*•]\s+/, '');

            notesContainer.appendChild(createNoteSection(title, content));
        });
    }
}

function createNoteSection(title, content) {
    const div = document.createElement('div');
    div.className = 'space-y-2';
    div.innerHTML = `
        <h4 class="text-xs font-bold uppercase tracking-widest text-slate-500">${title}</h4>
        <p class="text-slate-300 font-light leading-relaxed">${content}</p>
    `;
    return div;
}

// Search Logic
function initSearch() {
    const searchInput = document.getElementById('global-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            searchQuery = e.target.value.trim();
            // Just for demo, we only search in current view
        });
    }
}

// Expand/Collapse All
function expandAll() {
    if (!activeMindMapRoot) return;

    function recurse(nodes, parentId) {
        nodes.forEach((node, idx) => {
            const id = `${parentId}-${idx}`;
            if (node.children && node.children.length > 0) {
                expandedNodes.add(id);
                recurse(node.children, id);
            }
        });
    }
    recurse(activeMindMapRoot.children || [], 'gen-root');
    displayGeneratedMap(activeSubject.name, activeMindMapRoot);
}

function collapseAll() {
    expandedNodes.clear();
    displayGeneratedMap(activeSubject.name, activeMindMapRoot);
}

function closeModal() {
    document.getElementById('modal-overlay').classList.add('hidden');
}

// Flash Cards Logic
function populateFlashSubjectDropdown() {
    const select = document.getElementById('flash-subject-select');
    if (!select) return;

    const subjectsList = subjects || [];
    select.innerHTML = '<option value="" disabled selected>Select Subject</option>';

    subjectsList.forEach(sub => {
        const opt = document.createElement('option');
        opt.value = sub.name;
        opt.innerText = sub.name;
        select.add(opt);
    });
}

function updateFlashTopicDropdown() {
    const subName = document.getElementById('flash-subject-select').value;
    const topicSelect = document.getElementById('flash-topic-select');
    topicSelect.innerHTML = '<option value="" disabled selected>Select Topic</option>';

    const subject = subjects.find(s => s.name === subName);
    if (subject && subject.topics) {
        subject.topics.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.title;
            opt.innerText = t.title;
            topicSelect.add(opt);
        });
    }
}

async function generateFlashCardsAction() {
    const subName = document.getElementById('flash-subject-select').value;
    const topicName = document.getElementById('flash-topic-select').value;

    if (!subName || !topicName) {
        alert("Please select both a subject and a topic.");
        return;
    }

    const setup = document.getElementById('flashcards-setup');
    const loading = document.getElementById('flashcards-loading');
    const content = document.getElementById('flashcards-content');
    const msg = document.getElementById('flash-loading-messages');

    setup.classList.add('hidden');
    loading.classList.remove('hidden');

    const steps = [
        "Analyzing Topic Structure...",
        "Identifying Educational Objectives...",
        "Synthesizing Question-Answer Pairs...",
        "Finalizing Interactive Memory Cards..."
    ];

    for (let i = 0; i < steps.length; i++) {
        msg.innerText = steps[i];
        await new Promise(r => setTimeout(r, 500));
    }

    const subject = subjects.find(s => s.name === subName);
    const topic = subject.topics.find(t => t.title === topicName);
    activeFlashcards = topic.flashcards || [];

    document.getElementById('flash-current-subject').innerText = subName;
    document.getElementById('flash-current-topic').innerText = topicName;

    renderFlashcardSections();

    loading.classList.add('hidden');
    content.classList.remove('hidden');
}

function renderFlashcardSections() {
    const container = document.getElementById('flashcard-sections-container');
    container.innerHTML = '';

    let totalCards = 0;
    activeFlashcards.forEach((section, sIdx) => {
        const sectionDiv = document.createElement('div');
        sectionDiv.className = 'space-y-6';

        const header = document.createElement('div');
        header.className = 'flex items-center gap-3 pb-2 border-b border-white/5';
        header.innerHTML = `
            <div class="w-8 h-8 rounded-lg bg-orange-600/20 text-orange-400 flex items-center justify-center text-xs font-bold">${sIdx + 1}</div>
            <h3 class="text-lg font-bold text-slate-200">${section.title}</h3>
            <span class="text-[10px] bg-white/5 text-slate-500 px-2 py-0.5 rounded-full uppercase tracking-tighter ml-auto">${section.cards.length} Cards</span>
        `;
        sectionDiv.appendChild(header);

        const grid = document.createElement('div');
        grid.className = 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6';

        section.cards.forEach((card, cIdx) => {
            totalCards++;
            const cardEl = document.createElement('div');
            cardEl.className = 'flashcard-container';
            cardEl.onclick = function () { this.classList.toggle('flipped'); };

            cardEl.innerHTML = `
                <div class="flashcard-inner">
                    <div class="flashcard-front">
                        <p class="text-sm font-medium leading-relaxed font-sans">${card.question}</p>
                        <div class="absolute bottom-4 right-4 text-[10px] text-slate-500 uppercase tracking-widest"><i class="fas fa-redo-alt mr-1"></i> Flip</div>
                    </div>
                    <div class="flashcard-back">
                        <p class="text-sm font-bold leading-relaxed font-sans">${card.answer}</p>
                    </div>
                </div>
            `;
            grid.appendChild(cardEl);
        });

        sectionDiv.appendChild(grid);
        container.appendChild(sectionDiv);
    });

    document.getElementById('flash-stats').innerText = `${totalCards} Cards in ${activeFlashcards.length} Sections`;
}

function resetFlashSetup() {
    document.getElementById('flashcards-content').classList.add('hidden');
    document.getElementById('flashcards-loading').classList.add('hidden');
    document.getElementById('flashcards-setup').classList.remove('hidden');
}

// Authentication Logic
function toggleAuthMode() {
    authMode = authMode === 'login' ? 'register' : 'login';
    const title = document.getElementById('auth-title');
    const subtitle = document.getElementById('auth-subtitle');
    const btn = document.getElementById('auth-main-btn');
    const toggleLink = document.getElementById('auth-toggle-link');

    if (authMode === 'register') {
        title.innerText = 'Create Account';
        subtitle.innerText = 'Join the next generation of visual learning.';
        btn.querySelector('span').innerText = 'Create My Account';
        btn.querySelector('i').className = 'fas fa-user-plus';
        toggleLink.innerText = 'Sign In';
    } else {
        title.innerText = 'Welcome to CLH';
        subtitle.innerText = 'Your intelligent cognitive learning workspace.';
        btn.querySelector('span').innerText = 'Sign In';
        btn.querySelector('i').className = 'fas fa-sign-in-alt';
        toggleLink.innerText = 'Sign Up';
    }
}

async function handleAuthSubmit() {
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;

    if (!email || !password) {
        alert("Please enter both email and password.");
        return;
    }

    const forms = document.getElementById('auth-forms');
    const loading = document.getElementById('auth-loading');
    forms.classList.add('hidden');
    loading.classList.remove('hidden');

    const endpoint = authMode === 'login' ? '/api/auth/login' : '/api/auth/register';

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            if (authMode === 'register') {
                alert("Account created! Please sign in.");
                authMode = 'register';
                toggleAuthMode(); // Switch back to login
                loading.classList.add('hidden');
                forms.classList.remove('hidden');
            } else {
                localStorage.setItem('clh_user', JSON.stringify({ email: data.email }));
                currentUser = data;
                window.location.reload(); // Quickest way to re-init app with user state
            }
        } else {
            alert(data.detail || "Authentication failed.");
            loading.classList.add('hidden');
            forms.classList.remove('hidden');
        }
    } catch (err) {
        alert("Server connection error.");
        loading.classList.add('hidden');
        forms.classList.remove('hidden');
    }
}

function logout() {
    if (confirm("Are you sure you want to log out?")) {
        localStorage.removeItem('clh_user');
        window.location.reload();
    }
}
