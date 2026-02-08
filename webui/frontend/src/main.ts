// TypeScript entry converted from original static/app.js

type Channel = { sender_id: string; message_count: number }
type Model = { id: string; name: string }

interface State {
  selectedChannels: string[]
  selectedModel: string
  channels: Channel[]
  models: Model[]
  isLoading: boolean
}

const state: State = {
  selectedChannels: [],
  selectedModel: 'gemini-2.0-flash',
  channels: [],
  models: [],
  isLoading: false,
}

const elements = {
  chatMessages: document.getElementById('chatMessages')! as HTMLDivElement,
  messageInput: document.getElementById('messageInput')! as HTMLTextAreaElement,
  sendButton: document.getElementById('sendButton')! as HTMLButtonElement,
  channelSelector: document.getElementById('channelSelector')! as HTMLButtonElement,
  channelDropdown: document.getElementById('channelDropdown')! as HTMLDivElement,
  channelList: document.getElementById('channelList')! as HTMLDivElement,
  channelSelectorText: document.getElementById('channelSelectorText')! as HTMLSpanElement,
  clearChannels: document.getElementById('clearChannels')! as HTMLButtonElement,
  modelSelector: document.getElementById('modelSelector')! as HTMLButtonElement,
  modelDropdown: document.getElementById('modelDropdown')! as HTMLDivElement,
  modelList: document.getElementById('modelList')! as HTMLDivElement,
  modelSelectorText: document.getElementById('modelSelectorText')! as HTMLSpanElement,
}

document.addEventListener('DOMContentLoaded', () => {
  initializeApp()
})

async function initializeApp() {
  setupEventListeners()
  await Promise.all([loadChannels(), loadModels()])
}

function setupEventListeners() {
  elements.messageInput.addEventListener('input', handleInputChange)
  elements.messageInput.addEventListener('keydown', handleKeyDown)
  elements.sendButton.addEventListener('click', sendMessage)

  elements.channelSelector.addEventListener('click', (e) => {
    e.stopPropagation()
    toggleDropdown('channel')
  })
  elements.clearChannels.addEventListener('click', (e) => {
    e.stopPropagation()
    clearAllChannels()
  })

  elements.modelSelector.addEventListener('click', (e) => {
    e.stopPropagation()
    toggleDropdown('model')
  })

  document.addEventListener('click', closeAllDropdowns)

  elements.messageInput.addEventListener('input', autoResizeTextarea)
}

function handleInputChange() {
  elements.sendButton.disabled = !elements.messageInput.value.trim() || state.isLoading
}

function handleKeyDown(e: KeyboardEvent) {
  if ((e as KeyboardEvent).key === 'Enter' && !(e as KeyboardEvent).shiftKey) {
    e.preventDefault()
    if (!elements.sendButton.disabled) sendMessage()
  }
}

function autoResizeTextarea() {
  const textarea = elements.messageInput
  textarea.style.height = 'auto'
  textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px'
}

function toggleDropdown(type: 'channel' | 'model') {
  const wrapper =
    type === 'channel' ? elements.channelSelector.parentElement : elements.modelSelector.parentElement

  const isOpen = wrapper?.classList.contains('open')
  closeAllDropdowns()

  if (!isOpen && wrapper) wrapper.classList.add('open')
}

function closeAllDropdowns() {
  document.querySelectorAll('.selector-wrapper').forEach((w) => w.classList.remove('open'))
}

async function loadChannels() {
  try {
    const response = await fetch('/api/senders')
    if (!response.ok) throw new Error('Failed to load channels')
    state.channels = (await response.json()) as Channel[]
    renderChannelList()
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error('Error loading channels:', error)
    elements.channelList.innerHTML = '<div class="loading">Failed to load channels</div>'
  }
}

function renderChannelList() {
  if (state.channels.length === 0) {
    elements.channelList.innerHTML = '<div class="loading">No channels found</div>'
    return
  }

  elements.channelList.innerHTML = state.channels
    .map(
      (channel) => `
        <div class="dropdown-item ${state.selectedChannels.includes(channel.sender_id) ? 'selected' : ''}" 
             data-id="${channel.sender_id}">
            <input type="checkbox" 
                   ${state.selectedChannels.includes(channel.sender_id) ? 'checked' : ''}>
            <div class="item-info">
                <div class="item-name">${escapeHtml(channel.sender_id)}</div>
                <div class="item-meta">${channel.message_count} messages</div>
            </div>
        </div>
    `,
    )
    .join('')

  elements.channelList.querySelectorAll('.dropdown-item').forEach((item) => {
    item.addEventListener('click', (e) => {
      e.stopPropagation()
      const id = item.getAttribute('data-id')
      if (id) toggleChannel(id)
    })
  })
}

function toggleChannel(channelId: string) {
  const index = state.selectedChannels.indexOf(channelId)
  if (index === -1) state.selectedChannels.push(channelId)
  else state.selectedChannels.splice(index, 1)

  updateChannelSelectorText()
  renderChannelList()
  syncSelectedIds()
}

function clearAllChannels() {
  state.selectedChannels = []
  updateChannelSelectorText()
  renderChannelList()
  syncSelectedIds()
}

async function syncSelectedIds() {
  // eslint-disable-next-line no-console
  console.log('[webui] selected_ids updated:', state.selectedChannels)
  try {
    await fetch('/api/selected-ids', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sender_ids: state.selectedChannels }),
    })
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error('Failed to sync selected_ids to backend:', err)
  }
}

function updateChannelSelectorText() {
  const count = state.selectedChannels.length
  if (count === 0) elements.channelSelectorText.textContent = 'All channels'
  else if (count === 1) elements.channelSelectorText.textContent = state.selectedChannels[0]
  else elements.channelSelectorText.textContent = `${count} channels`
}

async function loadModels() {
  try {
    const response = await fetch('/api/models')
    if (!response.ok) throw new Error('Failed to load models')
    state.models = (await response.json()) as Model[]
    renderModelList()
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error('Error loading models:', error)
    elements.modelList.innerHTML = '<div class="loading">Failed to load models</div>'
  }
}

function renderModelList() {
  if (state.models.length === 0) {
    elements.modelList.innerHTML = '<div class="loading">No models available</div>'
    return
  }

  elements.modelList.innerHTML = state.models
    .map(
      (model) => `
        <div class="dropdown-item model-item ${state.selectedModel === model.id ? 'selected' : ''}" 
             data-id="${model.id}">
            <div class="item-info">
                <div class="item-name">${escapeHtml(model.name)}</div>
            </div>
        </div>
    `,
    )
    .join('')

  elements.modelList.querySelectorAll('.dropdown-item').forEach((item) => {
    item.addEventListener('click', (e) => {
      e.stopPropagation()
      const id = item.getAttribute('data-id')
      if (id) selectModel(id)
    })
  })
}

function selectModel(modelId: string) {
  state.selectedModel = modelId
  const model = state.models.find((m) => m.id === modelId)
  if (model) elements.modelSelectorText.textContent = model.name
  renderModelList()
  closeAllDropdowns()
}

async function sendMessage() {
  const message = elements.messageInput.value.trim()
  if (!message || state.isLoading) return

  elements.messageInput.value = ''
  elements.messageInput.style.height = 'auto'
  handleInputChange()

  const welcome = elements.chatMessages.querySelector('.welcome-message')
  if (welcome) welcome.remove()

  addMessage(message, 'user')

  const loadingEl = addLoadingMessage()

  state.isLoading = true
  elements.sendButton.disabled = true

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: message,
        sender_ids: state.selectedChannels,
        model_id: state.selectedModel,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to get response')
    }

    const data = await response.json()
    loadingEl.remove()
    addMessage(data.response, 'assistant', data.context_message_count)
  } catch (error: any) {
    // eslint-disable-next-line no-console
    console.error('Error:', error)
    loadingEl.remove()
    addMessage(`Error: ${error.message}`, 'assistant')
  } finally {
    state.isLoading = false
    handleInputChange()
  }
}

function addMessage(text: string, role: 'user' | 'assistant' | 'loading', contextCount: number | null = null) {
  const messageEl = document.createElement('div')
  messageEl.className = `message ${role}`

  let content = escapeHtml(text).replace(/\n/g, '<br>')

  if (role === 'assistant' && contextCount !== null) {
    content += `<div class="context-info">Based on ${contextCount} messages from selected channels</div>`
  }

  messageEl.innerHTML = content
  elements.chatMessages.appendChild(messageEl)
  scrollToBottom()
  return messageEl
}

function addLoadingMessage() {
  const messageEl = document.createElement('div')
  messageEl.className = 'message loading'
  messageEl.innerHTML = `
        <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `
  elements.chatMessages.appendChild(messageEl)
  scrollToBottom()
  return messageEl
}

function scrollToBottom() {
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight
}

function escapeHtml(text: string) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}
