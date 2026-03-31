const API_URL = '/api';

// State
let subjects = [];
let activeSubject = null;
let activeTopicNode = null;
let expandedNodes = new Set();
let searchQuery = "";

// Init
document.addEventListener('DOMContentLoaded', () => {
    loadSubjects();
    initSearch();
});

// Navigation & View Management
function showView(viewId) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    const target = document.getElementById(viewId);
    if (target) {
        target.classList.add('active');
    }
}

// Data Fetching
async function loadSubjects() {
    try {
        const res = await fetch(`${API_URL}/subjects/`);
        subjects = await res.json();

        // Auto-select PHOTONICS if available
        activeSubject = subjects.find(s => s.name.toUpperCase() === "PHOTONICS") || subjects[0];

        if (activeSubject) {
            document.getElementById('current-subject-title').innerText = activeSubject.name;
            renderTree();
        }
    } catch (err) {
        console.error('Error loading subjects:', err);
    }
}

// Tree Rendering
function renderTree() {
    const treeRoot = document.getElementById('tree-root');
    if (!activeSubject || !activeSubject.topics) return;

    treeRoot.innerHTML = '';

    // Sort topics if needed or filter by search
    const filteredTopics = filterTopics(activeSubject.topics, searchQuery);

    filteredTopics.forEach((topic, index) => {
        treeRoot.appendChild(createTreeNode(topic, 0, `root-${index}`));
    });

    const totalVisible = countAllNodes(filteredTopics);
    document.getElementById('topic-count-stats').innerText = `${totalVisible} Topics Found`;
}

function countAllNodes(nodes) {
    let count = 0;
    nodes.forEach(node => {
        count++;
        if (node.children && (expandedNodes.has(node.id) || searchQuery)) {
            count += countAllNodes(node.children);
        }
    });
    return count;
}

function createTreeNode(topic, depth, id) {
    const container = document.createElement('div');
    container.className = 'tree-node flex flex-col';

    const hasChildren = topic.children && topic.children.length > 0;
    const isExpanded = expandedNodes.has(id) || (searchQuery.length > 0 && hasChildren);
    const isMatched = searchQuery.length > 0 && topic.title.toLowerCase().includes(searchQuery.toLowerCase());

    // Confidence Color
    let statusClass = "status-green";
    if (topic.confidence <= 1) statusClass = "status-red";
    else if (topic.confidence <= 3) statusClass = "status-yellow";

    const nodeContent = document.createElement('div');
    nodeContent.className = `tree-node-content flex items-center gap-2 py-2 px-3 rounded-lg cursor-pointer transition-all duration-200 group ${depth > 0 ? 'ml-' + (depth * 4) : ''} ${isMatched ? 'search-highlight' : ''}`;
    nodeContent.style.marginLeft = `${depth * 1.5}rem`;

    const arrowIcon = hasChildren
        ? `<i class="fas fa-caret-right text-slate-500 transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}"></i>`
        : `<i class="fas fa-circle text-[6px] text-slate-700 ml-1 mr-1"></i>`;

    nodeContent.innerHTML = `
        <div class="flex items-center gap-2 flex-1">
            <span class="w-4 flex justify-center">${arrowIcon}</span>
            <span class="${statusClass} status-dot"></span>
            <span class="text-sm font-medium ${hasChildren ? 'text-slate-200' : 'text-slate-400'} group-hover:text-white transition-colors">
                ${highlightText(topic.title, searchQuery)}
            </span>
        </div>
        ${!hasChildren ? '<i class="fas fa-file-alt text-[10px] text-slate-600 opacity-0 group-hover:opacity-100 transition-opacity"></i>' : ''}
    `;

    nodeContent.onclick = (e) => {
        e.stopPropagation();
        if (hasChildren && e.target.closest('.fa-caret-right')) {
            toggleNode(id);
        } else {
            selectTopic(topic);
            if (hasChildren && !isExpanded) toggleNode(id);
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

// Search Logic
function initSearch() {
    const searchInput = document.getElementById('global-search');
    searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value.trim();
        renderTree();
    });
}

function filterTopics(topics, query) {
    if (!query) return topics;

    return topics.filter(topic => {
        const matchesTopic = topic.title.toLowerCase().includes(query.toLowerCase());
        const hasMatchingChild = topic.children && filterTopics(topic.children, query).length > 0;
        return matchesTopic || hasMatchingChild;
    });
}

function highlightText(text, query) {
    if (!query) return text;
    const regex = new RegExp(`(${query})`, 'gi');
    return text.replace(regex, '<span class="text-blue-400 font-bold">$1</span>');
}

// State Management
function toggleNode(id) {
    if (expandedNodes.has(id)) {
        expandedNodes.delete(id);
    } else {
        expandedNodes.add(id);
    }
    renderTree();
}

function expandAll() {
    if (!activeSubject || !activeSubject.topics) return;

    function recurse(nodes, parentId) {
        nodes.forEach((node, idx) => {
            const id = parentId ? `${parentId}-${idx}` : `root-${idx}`;
            if (node.children && node.children.length > 0) {
                expandedNodes.add(id);
                recurse(node.children, id);
            }
        });
    }

    expandedNodes.clear();
    recurse(activeSubject.topics);
    renderTree();
}

function collapseAll() {
    expandedNodes.clear();
    searchQuery = "";
    const searchInput = document.getElementById('global-search');
    if (searchInput) searchInput.value = "";
    renderTree();
}

function selectTopic(topic) {
    activeTopicNode = topic;

    // Hide empty state
    document.getElementById('notes-empty-state').classList.add('hidden');

    // Show active note view
    const view = document.getElementById('active-note-view');
    view.classList.remove('hidden');

    // Update Title & Badge
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

    // Update Description (Notes)
    const notesContainer = document.getElementById('note-sections-container');
    notesContainer.innerHTML = '';

    if (topic.note) {
        // Parse note into sections if it follows the Example structure
        // Structure: p-region, intrinsic region... Working: Intrinsic layer...
        const lines = topic.note.split('\n');

        // Show the first line as a description summary if multiple lines exist
        document.getElementById('note-description').innerText = lines[0] || "No detailed AI description available for this node yet.";

        // If there are specific structured lines (like "Structure:", "Working:"), parse them
        if (lines.length > 1) {
            lines.slice(1).forEach(line => {
                if (line.includes(':')) {
                    const [head, ...rest] = line.split(':');
                    notesContainer.appendChild(createNoteSection(head, rest.join(':')));
                }
            });
        } else if (topic.note.includes('Structure:') || topic.note.includes('Working:') || topic.note.includes('Advantages:')) {
            // Fallback for single line with keys
            const keys = ['Structure:', 'Working:', 'Advantages:', 'Applications:', 'Pros and Cons:'];
            let currentText = topic.note;
            keys.forEach((key, idx) => {
                if (currentText.includes(key)) {
                    let sectionContent = "";
                    const nextKey = keys.find((k, i) => i > idx && currentText.includes(k));
                    if (nextKey) {
                        sectionContent = currentText.split(key)[1].split(nextKey)[0];
                    } else {
                        sectionContent = currentText.split(key)[1];
                    }
                    notesContainer.appendChild(createNoteSection(key.replace(':', ''), sectionContent.trim()));
                }
            });
        }
    } else {
        document.getElementById('note-description').innerText = "Select a specific sub-topic or final node to view detailed clinical and research notes.";
    }

    // Update Metrics
    document.getElementById('note-confidence-val').innerText = (topic.confidence * 0.96).toFixed(1); // Mock variation
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

function countVisibleNodes(topics) {
    return countAllNodes(topics);
}

// UI Modals
function closeModal() {
    document.getElementById('modal-overlay').classList.add('hidden');
}

function showModal(title, msg) {
    document.getElementById('modal-title').innerText = title;
    document.getElementById('modal-message').innerText = msg;
    document.getElementById('modal-overlay').classList.remove('hidden');
}
