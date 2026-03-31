const API_URL = '/api';

// State
let subjects = [];
let activeSubject = null;
let activeMindMapRoot = null;
let activeTopicNode = null;
let expandedNodes = new Set();
let searchQuery = "";

// Init
document.addEventListener('DOMContentLoaded', () => {
    initApp();
    initSearch();
    initDashboard();
    showView('dashboard-view');
});

async function initApp() {
    await fetchSubjects();
    populateSubjectDropdown();
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
            sidebarLink.classList.add('bg-blue-600/20', 'text-blue-400', 'border-blue-500/30');
            sidebarLink.classList.remove('hover:bg-white/5', 'text-slate-400');
        }

        if (viewId === 'mindmap-view' && !activeSubject) {
            resetSetup();
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
        let points = [];
        if (topic.note.includes('\n')) {
            points = topic.note.split('\n');
        } else {
            points = topic.note.split('.').filter(p => p.trim().length > 0).map(p => p.trim());
        }

        // Set top highlight note
        document.getElementById('note-description').innerText = points[0] || "";

        // Add additional points as bullet sections
        if (points.length > 1) {
            points.slice(1).forEach((p, index) => {
                let title = `Key Point ${index + 1}`;
                let content = p;
                if (p.includes(':')) {
                    const parts = p.split(':');
                    title = parts[0].trim();
                    content = parts.slice(1).join(':').trim();
                }
                notesContainer.appendChild(createNoteSection(title, content));
            });
        }
    } else {
        document.getElementById('note-description').innerText = "Detailed content is under development or being fetched by AI.";
    }

    document.getElementById('note-confidence-val').innerText = (topic.confidence * 0.96).toFixed(1);
    document.getElementById('note-confidence-bar').style.width = `${topic.confidence * 20}%`;
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
