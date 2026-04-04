const API_URL = '/api';

// State
let subjects = [];
let activeSubject = null;
let activeMindMapRoot = null;
let activeTopicNode = null;
let expandedNodes = new Set();
let searchQuery = "";
let activeFlashcards = [];
let currentFlashCardIndex = 0;
let activeSectionCards = [];
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
    if (!currentUser) return;

    const nameEl = document.getElementById('user-profile-name');
    const roleEl = document.getElementById('user-profile-role');
    const initialsEl = document.getElementById('user-initials-circle');

    if (!nameEl || !roleEl || !initialsEl) return;

    // Use name if available, otherwise format from email
    let displayName = currentUser.name || currentUser.email.split('@')[0].replace(/[._-]/g, ' ').replace(/\w\S*/g, (txt) => txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase());

    // Extract initials
    const words = displayName.split(' ').filter(w => w.length > 0);
    let initials = "";
    if (words.length >= 2) {
        initials = words[0][0] + words[1][0];
    } else if (words.length === 1) {
        initials = words[0].slice(0, 2);
    } else {
        initials = displayName[0] || "?";
    }

    nameEl.innerText = displayName;
    roleEl.innerText = currentUser.name ? currentUser.email : "Pro Student";
    initialsEl.innerText = initials.toUpperCase();
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
            initFlashKeyboardControls();
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

    // Safety check: Filter out <think> blocks if any still exist
    const cleanNote = note.replace(/<think>[\s\S]*?<\/think>/g, '').trim();

    let points = cleanNote.split('\n').filter(p => p.trim().length > 0);

    if (points.length > 0) {
        // First paragraph is the description
        document.getElementById('note-description').innerText = points[0];

        // Rest are bullet points or sub-sections
        points.slice(1).forEach(p => {
            // Clean up common bullet prefixes and just render the text
            const cleanPoint = p.replace(/^[-*•]\s+/, '').trim();
            if (cleanPoint) {
                const pEl = document.createElement('p');
                pEl.className = 'text-slate-300 font-light leading-relaxed flex gap-3 text-sm';
                pEl.innerHTML = `<span class="text-blue-500 mt-1 flex-shrink-0">•</span> <span>${cleanPoint}</span>`;
                notesContainer.appendChild(pEl);
            }
        });
    }
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
    const sectionSelect = document.getElementById('flash-section-select');

    topicSelect.innerHTML = '<option value="" disabled selected>Select Topic</option>';
    sectionSelect.innerHTML = '<option value="" disabled selected>Select topic first</option>';

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

function updateFlashSectionDropdown() {
    const subName = document.getElementById('flash-subject-select').value;
    const topicName = document.getElementById('flash-topic-select').value;
    const sectionSelect = document.getElementById('flash-section-select');

    sectionSelect.innerHTML = '<option value="" disabled selected>Select Section</option>';

    const subject = subjects.find(s => s.name === subName);
    const topic = subject.topics.find(t => t.title === topicName);

    if (topic && topic.flashcards) {
        topic.flashcards.forEach(section => {
            const opt = document.createElement('option');
            opt.value = section.title;
            opt.innerText = section.title;
            sectionSelect.add(opt);
        });
    }
}

async function generateFlashCardsAction() {
    const subName = document.getElementById('flash-subject-select').value;
    const topicName = document.getElementById('flash-topic-select').value;
    const sectionTitle = document.getElementById('flash-section-select').value;

    if (!subName || !topicName || !sectionTitle) {
        alert("Please select subject, topic, and section.");
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
        await new Promise(r => setTimeout(r, 400));
    }

    const subject = subjects.find(s => s.name === subName);
    const topic = subject.topics.find(t => t.title === topicName);
    const section = topic.flashcards.find(s => s.title === sectionTitle);

    activeSectionCards = section.cards || [];
    currentFlashCardIndex = 0;

    document.getElementById('flash-current-subject').innerText = subName;
    document.getElementById('flash-current-topic').innerText = topicName;
    document.getElementById('flash-section-title').innerText = sectionTitle;

    renderCurrentFlashCard();

    loading.classList.add('hidden');
    content.classList.remove('hidden');
}

function renderCurrentFlashCard(direction = 'next') {
    const container = document.getElementById('flashcard-main-container');
    const card = activeSectionCards[currentFlashCardIndex];

    if (!card) return;

    // Update Progress
    const progressPercent = ((currentFlashCardIndex + 1) / activeSectionCards.length) * 100;
    document.getElementById('flash-progress-bar').style.width = `${progressPercent}%`;
    document.getElementById('flash-card-progress').innerText = `Card ${currentFlashCardIndex + 1} / ${activeSectionCards.length}`;

    // Navigation Button States
    document.getElementById('prev-card-btn').style.opacity = currentFlashCardIndex === 0 ? '0.3' : '1';
    document.getElementById('prev-card-btn').disabled = currentFlashCardIndex === 0;
    document.getElementById('next-card-btn').style.opacity = currentFlashCardIndex === activeSectionCards.length - 1 ? '0.3' : '1';
    document.getElementById('next-card-btn').disabled = currentFlashCardIndex === activeSectionCards.length - 1;

    // Slide Animation Logic
    const slideClass = direction === 'next' ? 'translate-x-full opacity-0' : '-translate-x-full opacity-0';

    container.innerHTML = `
        <div id="active-flashcard" class="flashcard-container active w-full h-full transition-all duration-500 transform ${slideClass}" onclick="flipCurrentCard()">
            <div class="flashcard-inner">
                <div class="flashcard-front">
                    <div class="text-center space-y-6">
                        <span class="px-3 py-1 bg-white/5 rounded-full text-[10px] text-slate-500 font-bold tracking-widest uppercase">Question</span>
                        <p class="text-2xl font-semibold leading-relaxed px-4">${card.question}</p>
                        <div class="text-[10px] text-slate-500 uppercase tracking-widest animate-pulse"><i class="fas fa-sync-alt mr-2"></i> Click to Reveal Answer</div>
                    </div>
                </div>
                <div class="flashcard-back">
                    <div class="text-center space-y-6">
                        <span class="px-3 py-1 bg-black/20 rounded-full text-[10px] text-orange-200 font-bold tracking-widest uppercase">Answer</span>
                        <p class="text-xl font-bold leading-relaxed px-4">${card.answer}</p>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Trigger entry animation
    setTimeout(() => {
        const cardEl = document.getElementById('active-flashcard');
        if (cardEl) cardEl.classList.remove('translate-x-full', '-translate-x-full', 'opacity-0');
    }, 50);

    initSwipeEvents();
}

function nextFlashCard() {
    if (currentFlashCardIndex < activeSectionCards.length - 1) {
        currentFlashCardIndex++;
        renderCurrentFlashCard('next');
    }
}

function prevFlashCard() {
    if (currentFlashCardIndex > 0) {
        currentFlashCardIndex--;
        renderCurrentFlashCard('prev');
    }
}

function flipCurrentCard() {
    const cardEl = document.querySelector('#active-flashcard');
    if (cardEl) {
        cardEl.classList.toggle('flipped');
    }
}

function initFlashKeyboardControls() {
    window.removeEventListener('keydown', handleFlashKeydown);
    window.addEventListener('keydown', handleFlashKeydown);
}

function handleFlashKeydown(e) {
    if (document.getElementById('flashcards-view').classList.contains('hidden')) return;

    if (e.code === 'Space') {
        e.preventDefault();
        flipCurrentCard();
    } else if (e.code === 'ArrowRight') {
        nextFlashCard();
    } else if (e.code === 'ArrowLeft') {
        prevFlashCard();
    }
}

let touchStartX = 0;
let touchEndX = 0;

function initSwipeEvents() {
    const container = document.getElementById('flashcard-main-container');
    if (!container) return;

    container.ontouchstart = e => {
        touchStartX = e.changedTouches[0].screenX;
    };

    container.ontouchend = e => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    };
}

function handleSwipe() {
    const threshold = 50;
    if (touchEndX < touchStartX - threshold) {
        nextFlashCard();
    } else if (touchEndX > touchStartX + threshold) {
        prevFlashCard();
    }
}

function resetFlashSetup() {
    document.getElementById('flashcards-content').classList.add('hidden');
    document.getElementById('flashcards-loading').classList.add('hidden');
    document.getElementById('flashcards-setup').classList.remove('hidden');

    // Reset state
    activeSectionCards = [];
    currentFlashCardIndex = 0;

    // Reset dropdowns
    document.getElementById('flash-subject-select').value = "";
    document.getElementById('flash-topic-select').innerHTML = '<option value="" disabled selected>Select topic first</option>';
    document.getElementById('flash-section-select').innerHTML = '<option value="" disabled selected>Select topic first</option>';
}

// Authentication Logic
function toggleAuthMode() {
    authMode = authMode === 'login' ? 'register' : 'login';
    const title = document.getElementById('auth-title');
    const subtitle = document.getElementById('auth-subtitle');
    const btn = document.getElementById('auth-main-btn');
    const toggleLink = document.getElementById('auth-toggle-link');
    const nameField = document.getElementById('name-field-container');

    if (authMode === 'register') {
        title.innerText = 'Create Account';
        subtitle.innerText = 'Join the next generation of visual learning.';
        btn.querySelector('span').innerText = 'Create My Account';
        btn.querySelector('i').className = 'fas fa-user-plus';
        toggleLink.innerText = 'Sign In';
        if (nameField) nameField.classList.remove('hidden');
    } else {
        title.innerText = 'Welcome to CLH';
        subtitle.innerText = 'Your intelligent cognitive learning workspace.';
        btn.querySelector('span').innerText = 'Sign In';
        btn.querySelector('i').className = 'fas fa-sign-in-alt';
        toggleLink.innerText = 'Sign Up';
        if (nameField) nameField.classList.add('hidden');
    }
}

async function handleAuthSubmit() {
    const name = document.getElementById('auth-name') ? document.getElementById('auth-name').value : "";
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;

    if (!email || !password || (authMode === 'register' && !name)) {
        alert("Please fill in all fields.");
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
            body: JSON.stringify({ email, password, name: authMode === 'register' ? name : null })
        });

        const data = await response.json();

        if (response.ok) {
            if (authMode === 'register') {
                alert("Account created! Please sign in.");
                toggleAuthMode();
                loading.classList.add('hidden');
                forms.classList.remove('hidden');
            } else {
                localStorage.setItem('clh_user', JSON.stringify({ email: data.email, name: data.name }));
                currentUser = data;
                window.location.reload();
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
