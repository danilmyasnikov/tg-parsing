// State
const state = {
    selectedChannels: [],
    selectedModel: 'gemini-2.0-flash',
    channels: [],
    models: [],
    isLoading: false,
};

// DOM Elements
const elements = {
    chatMessages: document.getElementById('chatMessages'),
    messageInput: document.getElementById('messageInput'),
    sendButton: document.getElementById('sendButton'),
    channelSelector: document.getElementById('channelSelector'),
    channelDropdown: document.getElementById('channelDropdown'),
    channelList: document.getElementById('channelList'),
    channelSelectorText: document.getElementById('channelSelectorText'),
    clearChannels: document.getElementById('clearChannels'),
    modelSelector: document.getElementById('modelSelector'),
    modelDropdown: document.getElementById('modelDropdown'),
    modelList: document.getElementById('modelList'),
    modelSelectorText: document.getElementById('modelSelectorText'),
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    setupEventListeners();
    await Promise.all([
        loadChannels(),
        loadModels(),
    ]);
}

function setupEventListeners() {
    // Message input
    elements.messageInput.addEventListener('input', handleInputChange);
    elements.messageInput.addEventListener('keydown', handleKeyDown);
    elements.sendButton.addEventListener('click', sendMessage);

    // Channel selector
    elements.channelSelector.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDropdown('channel');
    });
    elements.clearChannels.addEventListener('click', (e) => {
        e.stopPropagation();
        clearAllChannels();
    });

    // Model selector
    elements.modelSelector.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDropdown('model');
    });

    // Close dropdowns when clicking outside
    document.addEventListener('click', closeAllDropdowns);

    // Auto-resize textarea
    elements.messageInput.addEventListener('input', autoResizeTextarea);
}

function handleInputChange() {
    elements.sendButton.disabled = !elements.messageInput.value.trim() || state.isLoading;
}

function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!elements.sendButton.disabled) {
            sendMessage();
        }
    }
}

function autoResizeTextarea() {
    const textarea = elements.messageInput;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
}

// Dropdown handling
function toggleDropdown(type) {
    const wrapper = type === 'channel' 
        ? elements.channelSelector.parentElement 
        : elements.modelSelector.parentElement;
    
    const isOpen = wrapper.classList.contains('open');
    closeAllDropdowns();
    
    if (!isOpen) {
        wrapper.classList.add('open');
    }
}

function closeAllDropdowns() {
    document.querySelectorAll('.selector-wrapper').forEach(w => w.classList.remove('open'));
}

// Load channels from API
async function loadChannels() {
    try {
        const response = await fetch('/api/senders');
        if (!response.ok) throw new Error('Failed to load channels');
        
        state.channels = await response.json();
        renderChannelList();
    } catch (error) {
        console.error('Error loading channels:', error);
        elements.channelList.innerHTML = '<div class="loading">Failed to load channels</div>';
    }
}

function renderChannelList() {
    if (state.channels.length === 0) {
        elements.channelList.innerHTML = '<div class="loading">No channels found</div>';
        return;
    }

    elements.channelList.innerHTML = state.channels.map(channel => `
        <div class="dropdown-item ${state.selectedChannels.includes(channel.sender_id) ? 'selected' : ''}" 
             data-id="${channel.sender_id}">
            <input type="checkbox" 
                   ${state.selectedChannels.includes(channel.sender_id) ? 'checked' : ''}>
            <div class="item-info">
                <div class="item-name">${escapeHtml(channel.sender_id)}</div>
                <div class="item-meta">${channel.message_count} messages</div>
            </div>
        </div>
    `).join('');

    // Add click handlers
    elements.channelList.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleChannel(item.dataset.id);
        });
    });
}

function toggleChannel(channelId) {
    const index = state.selectedChannels.indexOf(channelId);
    if (index === -1) {
        state.selectedChannels.push(channelId);
    } else {
        state.selectedChannels.splice(index, 1);
    }
    updateChannelSelectorText();
    renderChannelList();
    syncSelectedIds();
}

function clearAllChannels() {
    state.selectedChannels = [];
    updateChannelSelectorText();
    renderChannelList();
    syncSelectedIds();
}

/** Push the current selected channel IDs to the backend and log to console. */
async function syncSelectedIds() {
    console.log('[webui] selected_ids updated:', state.selectedChannels);
    try {
        await fetch('/api/selected-ids', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sender_ids: state.selectedChannels }),
        });
    } catch (err) {
        console.error('Failed to sync selected_ids to backend:', err);
    }
}

function updateChannelSelectorText() {
    const count = state.selectedChannels.length;
    if (count === 0) {
        elements.channelSelectorText.textContent = 'All channels';
    } else if (count === 1) {
        elements.channelSelectorText.textContent = state.selectedChannels[0];
    } else {
        elements.channelSelectorText.textContent = `${count} channels`;
    }
}

// Load models from API
async function loadModels() {
    try {
        const response = await fetch('/api/models');
        if (!response.ok) throw new Error('Failed to load models');
        
        state.models = await response.json();
        renderModelList();
    } catch (error) {
        console.error('Error loading models:', error);
        elements.modelList.innerHTML = '<div class="loading">Failed to load models</div>';
    }
}

function renderModelList() {
    if (state.models.length === 0) {
        elements.modelList.innerHTML = '<div class="loading">No models available</div>';
        return;
    }

    elements.modelList.innerHTML = state.models.map(model => `
        <div class="dropdown-item model-item ${state.selectedModel === model.id ? 'selected' : ''}" 
             data-id="${model.id}">
            <div class="item-info">
                <div class="item-name">${escapeHtml(model.name)}</div>
            </div>
        </div>
    `).join('');

    // Add click handlers
    elements.modelList.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            selectModel(item.dataset.id);
        });
    });
}

function selectModel(modelId) {
    state.selectedModel = modelId;
    const model = state.models.find(m => m.id === modelId);
    if (model) {
        elements.modelSelectorText.textContent = model.name;
    }
    renderModelList();
    closeAllDropdowns();
}

// Chat functionality
async function sendMessage() {
    const message = elements.messageInput.value.trim();
    if (!message || state.isLoading) return;

    // Clear input
    elements.messageInput.value = '';
    elements.messageInput.style.height = 'auto';
    handleInputChange();

    // Remove welcome message if present
    const welcome = elements.chatMessages.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    // Add user message
    addMessage(message, 'user');

    // Add loading indicator
    const loadingEl = addLoadingMessage();

    state.isLoading = true;
    elements.sendButton.disabled = true;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                sender_ids: state.selectedChannels,
                model_id: state.selectedModel,
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get response');
        }

        const data = await response.json();
        
        // Remove loading indicator
        loadingEl.remove();

        // Add assistant message
        addMessage(data.response, 'assistant', data.context_message_count);
    } catch (error) {
        console.error('Error:', error);
        loadingEl.remove();
        addMessage(`Error: ${error.message}`, 'assistant');
    } finally {
        state.isLoading = false;
        handleInputChange();
    }
}

function addMessage(text, role, contextCount = null) {
    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}`;
    
    let content = escapeHtml(text).replace(/\n/g, '<br>');
    
    if (role === 'assistant' && contextCount !== null) {
        content += `<div class="context-info">Based on ${contextCount} messages from selected channels</div>`;
    }
    
    messageEl.innerHTML = content;
    elements.chatMessages.appendChild(messageEl);
    scrollToBottom();
    return messageEl;
}

function addLoadingMessage() {
    const messageEl = document.createElement('div');
    messageEl.className = 'message loading';
    messageEl.innerHTML = `
        <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    elements.chatMessages.appendChild(messageEl);
    scrollToBottom();
    return messageEl;
}

function scrollToBottom() {
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
