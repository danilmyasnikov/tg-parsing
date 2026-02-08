import { PRESETS, Preset } from './presets'

type Channel = { sender_id: string; message_count: number }
type Model = { id: string; name: string }
type DbStatus = {
  message_count: number
  sender_count: number
  latest_message_at: string | null
}

type Result = {
  id: string
  prompt: string
  response: string
  createdAt: string
  contextCount: number
  senderIds: string[]
  modelId: string
}

type LogEntry = {
  id: string
  message: string
  time: string
  type: 'info' | 'success' | 'error'
}

const RESULTS_STORAGE_KEY = 'tgParsingResults'
const ACTIVE_RESULT_KEY = 'tgParsingActiveResult'

const state = {
  selectedChannels: [] as string[],
  selectedModel: 'gemini-2.0-flash',
  channels: [] as Channel[],
  models: [] as Model[],
  isLoading: false,
  channelFilter: '',
  results: [] as Result[],
  activeResultId: null as string | null,
  runLog: [] as LogEntry[],
  opsLog: [] as LogEntry[],
  dbStatus: null as DbStatus | null,
}

const elements = {
  tabButtons: Array.from(document.querySelectorAll<HTMLButtonElement>('.tab-button')),
  panels: Array.from(document.querySelectorAll<HTMLDivElement>('.sidebar-panel')),
  channelSearch: document.getElementById('channelSearch') as HTMLInputElement,
  channelList: document.getElementById('channelList') as HTMLDivElement,
  channelSummary: document.getElementById('channelSummary') as HTMLDivElement,
  recentChannels: document.getElementById('recentChannels') as HTMLDivElement,
  clearChannels: document.getElementById('clearChannels') as HTMLButtonElement,
  sessionList: document.getElementById('sessionList') as HTMLDivElement,
  newSession: document.getElementById('newSession') as HTMLButtonElement,
  presetBar: document.getElementById('presetBar') as HTMLDivElement,
  promptInput: document.getElementById('promptInput') as HTMLTextAreaElement,
  generateButton: document.getElementById('generateButton') as HTMLButtonElement,
  messageLimit: document.getElementById('messageLimit') as HTMLInputElement,
  contextSummary: document.getElementById('contextSummary') as HTMLDivElement,
  resultsList: document.getElementById('resultsList') as HTMLDivElement,
  resultsMeta: document.getElementById('resultsMeta') as HTMLParagraphElement,
  viewAllResults: document.getElementById('viewAllResults') as HTMLButtonElement,
  runLog: document.getElementById('runLog') as HTMLDivElement,
  opsLog: document.getElementById('opsLog') as HTMLDivElement,
  dbStatus: document.getElementById('dbStatus') as HTMLDivElement,
  activeModel: document.getElementById('activeModel') as HTMLDivElement,
  toggleSidebar: document.getElementById('toggleSidebar') as HTMLButtonElement,
  refreshDb: document.getElementById('refreshDb') as HTMLButtonElement,
  refreshDbSecondary: document.getElementById('refreshDbSecondary') as HTMLButtonElement,
  clearDb: document.getElementById('clearDb') as HTMLButtonElement,
  collectorTargets: document.getElementById('collectorTargets') as HTMLTextAreaElement,
  collectorLimit: document.getElementById('collectorLimit') as HTMLInputElement,
  collectorRun: document.getElementById('collectorRun') as HTMLButtonElement,
  analyzerJob: document.getElementById('analyzerJob') as HTMLSelectElement,
  analyzerDays: document.getElementById('analyzerDays') as HTMLInputElement,
  analyzerLimit: document.getElementById('analyzerLimit') as HTMLInputElement,
  analyzerUseSelected: document.getElementById('analyzerUseSelected') as HTMLInputElement,
  analyzerRun: document.getElementById('analyzerRun') as HTMLButtonElement,
  modelSelector: document.getElementById('modelSelector') as HTMLButtonElement,
  modelDropdown: document.getElementById('modelDropdown') as HTMLDivElement,
  modelList: document.getElementById('modelList') as HTMLDivElement,
  modelSelectorText: document.getElementById('modelSelectorText') as HTMLSpanElement,
}

document.addEventListener('DOMContentLoaded', () => {
  initializeApp()
})

async function initializeApp() {
  loadStoredResults()
  setupEventListeners()
  renderPresets()
  renderResults()
  renderSessions()
  updateChannelSummary()
  updateContextSummary()
  autoResizeTextarea(elements.promptInput)

  await Promise.all([loadChannels(), loadModels(), fetchDbStatus()])
  startDbPolling()
}

function setupEventListeners() {
  elements.tabButtons.forEach((button) => {
    button.addEventListener('click', () => {
      setActiveTab(button.dataset.tab || 'channels')
    })
  })

  elements.channelSearch.addEventListener('input', () => {
    state.channelFilter = elements.channelSearch.value.trim().toLowerCase()
    renderChannelList()
  })

  elements.clearChannels.addEventListener('click', () => {
    clearAllChannels()
  })

  elements.newSession.addEventListener('click', () => {
    state.activeResultId = null
    saveActiveResult()
    elements.promptInput.value = ''
    updateGenerateButton()
    renderResults()
  })

  elements.promptInput.addEventListener('input', () => {
    updateGenerateButton()
    autoResizeTextarea(elements.promptInput)
  })

  elements.generateButton.addEventListener('click', () => {
    generatePost()
  })

  elements.viewAllResults.addEventListener('click', () => {
    state.activeResultId = null
    saveActiveResult()
    renderResults()
  })

  elements.toggleSidebar.addEventListener('click', () => {
    document.body.classList.toggle('sidebar-collapsed')
  })

  elements.refreshDb.addEventListener('click', () => fetchDbStatus(true))
  elements.refreshDbSecondary.addEventListener('click', () => fetchDbStatus(true))
  elements.clearDb.addEventListener('click', () => clearDatabase())
  elements.collectorRun.addEventListener('click', () => runCollector())
  elements.analyzerRun.addEventListener('click', () => runAnalyzer())

  elements.modelSelector.addEventListener('click', (event) => {
    event.stopPropagation()
    toggleModelDropdown()
  })

  document.addEventListener('click', () => closeModelDropdown())
}

function setActiveTab(tab: string) {
  elements.tabButtons.forEach((button) => {
    button.classList.toggle('active', button.dataset.tab === tab)
  })
  elements.panels.forEach((panel) => {
    panel.classList.toggle('active', panel.dataset.panel === tab)
  })
}

function renderPresets() {
  elements.presetBar.innerHTML = PRESETS.map((preset) => {
    const hint = escapeHtml(preset.hint).replace(/"/g, '&quot;')
    return `
      <button type="button" class="preset-chip" data-preset="${preset.id}" data-hint="${hint}">
        ${escapeHtml(preset.label)}
      </button>
    `
  }).join('')

  elements.presetBar.querySelectorAll<HTMLButtonElement>('.preset-chip').forEach((button) => {
    button.addEventListener('click', () => {
      const preset = PRESETS.find((item) => item.id === button.dataset.preset)
      if (preset) applyPreset(preset)
    })
  })
}

function applyPreset(preset: Preset) {
  const current = elements.promptInput.value.trim()
  if (!current) {
    elements.promptInput.value = preset.template
  } else {
    elements.promptInput.value = `${elements.promptInput.value.trim()}\n\n${preset.template}`
  }
  autoResizeTextarea(elements.promptInput)
  updateGenerateButton()
}

async function loadChannels() {
  try {
    const response = await fetch('/api/senders')
    if (!response.ok) throw new Error('Failed to load channels')
    state.channels = (await response.json()) as Channel[]
    renderChannelList()
    renderRecentChannels()
    updateChannelSummary()
    updateContextSummary()
  } catch (error) {
    elements.channelList.innerHTML = '<div class="loading">Failed to load channels</div>'
  }
}

function renderChannelList() {
  const filtered = state.channelFilter
    ? state.channels.filter((channel) => channel.sender_id.toLowerCase().includes(state.channelFilter))
    : state.channels

  if (filtered.length === 0) {
    elements.channelList.innerHTML = '<div class="loading">No channels found</div>'
    return
  }

  elements.channelList.innerHTML = filtered
    .map((channel) => {
      const selected = state.selectedChannels.includes(channel.sender_id)
      return `
        <div class="channel-item ${selected ? 'selected' : ''}" data-id="${channel.sender_id}">
          <div>
            <div>${escapeHtml(channel.sender_id)}</div>
            <div class="channel-meta">${channel.message_count} messages</div>
          </div>
          <input type="checkbox" ${selected ? 'checked' : ''} />
        </div>
      `
    })
    .join('')

  elements.channelList.querySelectorAll<HTMLDivElement>('.channel-item').forEach((item) => {
    item.addEventListener('click', () => {
      const id = item.dataset.id
      if (id) toggleChannel(id)
    })
  })
}

function renderRecentChannels() {
  if (state.channels.length === 0) {
    elements.recentChannels.innerHTML = '<div class="loading">No activity yet.</div>'
    return
  }
  const recent = [...state.channels].sort((a, b) => b.message_count - a.message_count).slice(0, 4)
  elements.recentChannels.innerHTML = recent
    .map((channel) => {
      return `
        <div class="recent-item">
          <span>${escapeHtml(channel.sender_id)}</span>
          <span>${channel.message_count}</span>
        </div>
      `
    })
    .join('')
}

function toggleChannel(channelId: string) {
  const index = state.selectedChannels.indexOf(channelId)
  if (index === -1) state.selectedChannels.push(channelId)
  else state.selectedChannels.splice(index, 1)
  updateChannelSummary()
  updateContextSummary()
  renderChannelList()
  syncSelectedIds()
}

function clearAllChannels() {
  state.selectedChannels = []
  updateChannelSummary()
  updateContextSummary()
  renderChannelList()
  syncSelectedIds()
}

async function syncSelectedIds() {
  try {
    await fetch('/api/selected-ids', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sender_ids: state.selectedChannels }),
    })
  } catch (err) {
    appendRunLog('Failed to sync selected channels', 'error')
  }
}

function updateChannelSummary() {
  const count = state.selectedChannels.length
  if (count === 0) {
    elements.channelSummary.textContent = `All channels (${state.channels.length})`
  } else if (count === 1) {
    elements.channelSummary.textContent = `Selected: ${state.selectedChannels[0]}`
  } else {
    elements.channelSummary.textContent = `Selected: ${count} channels`
  }
}

function updateContextSummary() {
  const count = state.selectedChannels.length
  if (count === 0) {
    elements.contextSummary.textContent = 'All channels'
  } else if (count === 1) {
    elements.contextSummary.textContent = state.selectedChannels[0]
  } else {
    elements.contextSummary.textContent = `${count} channels selected`
  }
}

async function loadModels() {
  try {
    const response = await fetch('/api/models')
    if (!response.ok) throw new Error('Failed to load models')
    state.models = (await response.json()) as Model[]
    if (!state.models.find((model) => model.id === state.selectedModel) && state.models.length > 0) {
      state.selectedModel = state.models[0].id
    }
    renderModelList()
    updateModelText()
  } catch (error) {
    elements.modelList.innerHTML = '<div class="loading">Failed to load models</div>'
  }
}

function renderModelList() {
  if (state.models.length === 0) {
    elements.modelList.innerHTML = '<div class="loading">No models available</div>'
    return
  }

  elements.modelList.innerHTML = state.models
    .map((model) => {
      const selected = state.selectedModel === model.id
      return `
        <div class="dropdown-item ${selected ? 'selected' : ''}" data-id="${model.id}">
          ${escapeHtml(model.name)}
        </div>
      `
    })
    .join('')

  elements.modelList.querySelectorAll<HTMLDivElement>('.dropdown-item').forEach((item) => {
    item.addEventListener('click', (event) => {
      event.stopPropagation()
      const id = item.dataset.id
      if (id) selectModel(id)
    })
  })
}

function selectModel(modelId: string) {
  state.selectedModel = modelId
  updateModelText()
  renderModelList()
  closeModelDropdown()
}

function updateModelText() {
  const model = state.models.find((item) => item.id === state.selectedModel)
  if (model) {
    elements.modelSelectorText.textContent = model.name
    elements.activeModel.textContent = `Model: ${model.name}`
  }
}

function toggleModelDropdown() {
  elements.modelDropdown.parentElement?.classList.toggle('open')
}

function closeModelDropdown() {
  elements.modelDropdown.parentElement?.classList.remove('open')
}

function updateGenerateButton() {
  elements.generateButton.disabled = !elements.promptInput.value.trim() || state.isLoading
}

function autoResizeTextarea(textarea: HTMLTextAreaElement) {
  textarea.style.height = 'auto'
  const styles = window.getComputedStyle(textarea)
  const lineHeight = Number.parseFloat(styles.lineHeight || '24') || 24
  const paddingTop = Number.parseFloat(styles.paddingTop || '0') || 0
  const paddingBottom = Number.parseFloat(styles.paddingBottom || '0') || 0
  const maxHeight = lineHeight * 8 + paddingTop + paddingBottom
  const nextHeight = Math.min(textarea.scrollHeight, maxHeight)
  textarea.style.height = `${nextHeight}px`
  textarea.style.overflowY = textarea.scrollHeight > maxHeight ? 'auto' : 'hidden'
}

async function generatePost() {
  const prompt = elements.promptInput.value.trim()
  if (!prompt || state.isLoading) return

  const messageLimit = Math.max(1, Number(elements.messageLimit.value || 120))

  state.isLoading = true
  updateGenerateButton()
  appendRunLog('Generating post...', 'info')

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: prompt,
        sender_ids: state.selectedChannels,
        model_id: state.selectedModel,
        message_limit: messageLimit,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to generate')
    }

    const data = await response.json()
    const result: Result = {
      id: crypto.randomUUID(),
      prompt,
      response: data.response,
      createdAt: new Date().toISOString(),
      contextCount: data.context_message_count,
      senderIds: [...state.selectedChannels],
      modelId: state.selectedModel,
    }

    state.results.unshift(result)
    state.activeResultId = result.id
    saveResults()
    saveActiveResult()
    renderResults()
    renderSessions()
    appendRunLog(`Generated using ${data.context_message_count} messages`, 'success')
  } catch (error: any) {
    appendRunLog(error.message || 'Generation failed', 'error')
  } finally {
    state.isLoading = false
    updateGenerateButton()
  }
}

function renderResults() {
  const visible = state.activeResultId
    ? state.results.filter((result) => result.id === state.activeResultId)
    : state.results

  if (visible.length === 0) {
    elements.resultsList.innerHTML = '<div class="empty-state">Run your first generation to see results.</div>'
    elements.resultsMeta.textContent = 'No generations yet.'
    return
  }

  const metaText = state.activeResultId
    ? 'Showing 1 session'
    : `Showing ${visible.length} sessions`
  elements.resultsMeta.textContent = metaText

  elements.resultsList.innerHTML = visible
    .map((result) => {
      const created = new Date(result.createdAt).toLocaleString()
      const promptSnippet = result.prompt.length > 140 ? `${result.prompt.slice(0, 140)}...` : result.prompt
      return `
        <div class="result-card" data-id="${result.id}">
          <div class="result-meta">
            <span>${created}</span>
            <span>${result.senderIds.length || 'All'} channels · ${result.contextCount} msgs</span>
          </div>
          <div class="result-prompt">${escapeHtml(promptSnippet)}</div>
          <div class="result-body">${escapeHtml(result.response)}</div>
          <div class="result-actions">
            <button class="ghost-button" data-action="copy">Copy</button>
            <button class="ghost-button" data-action="edit">Edit</button>
          </div>
        </div>
      `
    })
    .join('')

  elements.resultsList.querySelectorAll<HTMLButtonElement>('button[data-action="copy"]').forEach((button) => {
    button.addEventListener('click', (event) => {
      const card = (event.target as HTMLElement).closest('.result-card') as HTMLDivElement | null
      if (!card) return
      const id = card.dataset.id
      const result = state.results.find((item) => item.id === id)
      if (result) copyToClipboard(result.response)
    })
  })

  elements.resultsList.querySelectorAll<HTMLButtonElement>('button[data-action="edit"]').forEach((button) => {
    button.addEventListener('click', (event) => {
      const card = (event.target as HTMLElement).closest('.result-card') as HTMLDivElement | null
      if (!card) return
      const id = card.dataset.id
      const result = state.results.find((item) => item.id === id)
      if (result) {
        elements.promptInput.value = result.response
        autoResizeTextarea(elements.promptInput)
        updateGenerateButton()
      }
    })
  })
}

function renderSessions() {
  if (state.results.length === 0) {
    elements.sessionList.innerHTML = '<div class="loading">No sessions yet.</div>'
    return
  }

  elements.sessionList.innerHTML = state.results
    .map((result) => {
      const created = new Date(result.createdAt).toLocaleDateString()
      const label = result.prompt.length > 32 ? `${result.prompt.slice(0, 32)}...` : result.prompt
      const active = state.activeResultId === result.id ? 'selected' : ''
      return `
        <div class="session-item ${active}" data-id="${result.id}">
          <div>
            <div>${escapeHtml(label || 'Untitled')}</div>
            <div class="session-meta">${created}</div>
          </div>
          <span>${result.contextCount}</span>
        </div>
      `
    })
    .join('')

  elements.sessionList.querySelectorAll<HTMLDivElement>('.session-item').forEach((item) => {
    item.addEventListener('click', () => {
      const id = item.dataset.id
      if (id) {
        state.activeResultId = id
        saveActiveResult()
        renderResults()
      }
    })
  })
}

function appendRunLog(message: string, type: LogEntry['type']) {
  const entry: LogEntry = {
    id: crypto.randomUUID(),
    message,
    time: new Date().toLocaleTimeString(),
    type,
  }
  state.runLog.unshift(entry)
  if (state.runLog.length > 6) state.runLog.pop()
  renderLog(entriesToHtml(state.runLog), elements.runLog)
}

function appendOpsLog(message: string, type: LogEntry['type']) {
  const entry: LogEntry = {
    id: crypto.randomUUID(),
    message,
    time: new Date().toLocaleTimeString(),
    type,
  }
  state.opsLog.unshift(entry)
  if (state.opsLog.length > 8) state.opsLog.pop()
  renderLog(entriesToHtml(state.opsLog), elements.opsLog)
}

function entriesToHtml(entries: LogEntry[]) {
  return entries
    .map(
      (entry) => `
      <div class="log-entry ${entry.type}">
        <span>${escapeHtml(entry.message)}</span>
        <span>${entry.time}</span>
      </div>
    `,
    )
    .join('')
}

function renderLog(html: string, target: HTMLDivElement) {
  target.innerHTML = html || '<div class="loading">No activity yet.</div>'
}

async function fetchDbStatus(showLog = false) {
  try {
    const response = await fetch('/api/db/status')
    if (!response.ok) throw new Error('Failed to fetch DB status')
    state.dbStatus = (await response.json()) as DbStatus
    updateDbStatus()
    if (showLog) appendOpsLog('Database status refreshed', 'success')
  } catch (error: any) {
    if (showLog) appendOpsLog(error.message || 'Failed to refresh DB status', 'error')
  }
}

function updateDbStatus() {
  if (!state.dbStatus) return
  const latest = state.dbStatus.latest_message_at
    ? new Date(state.dbStatus.latest_message_at).toLocaleString()
    : 'No data'
  elements.dbStatus.textContent = `DB: ${state.dbStatus.message_count} msgs · ${state.dbStatus.sender_count} channels`
  elements.dbStatus.title = `Latest message: ${latest}`
}

function startDbPolling() {
  setInterval(() => {
    fetchDbStatus()
  }, 20000)
}

async function clearDatabase() {
  const confirmClear = window.confirm('This will delete all messages. Continue?')
  if (!confirmClear) return
  appendOpsLog('Clearing messages table...', 'info')
  try {
    const response = await fetch('/api/db/clear', { method: 'POST' })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to clear database')
    }
    appendOpsLog('Messages table reset', 'success')
    await fetchDbStatus()
    await loadChannels()
  } catch (error: any) {
    appendOpsLog(error.message || 'Failed to clear database', 'error')
  }
}

async function runCollector() {
  const targets = elements.collectorTargets.value
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean)

  if (targets.length === 0) {
    appendOpsLog('Provide at least one target', 'error')
    return
  }

  const limit = Math.max(1, Number(elements.collectorLimit.value || 100))
  appendOpsLog('Running collector...', 'info')

  try {
    const response = await fetch('/api/collector/fetch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ targets, limit }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Collector failed')
    }

    const data = await response.json()
    appendOpsLog(`Collector processed ${data.processed} messages`, 'success')
    await fetchDbStatus()
    await loadChannels()
  } catch (error: any) {
    appendOpsLog(error.message || 'Collector failed', 'error')
  }
}

async function runAnalyzer() {
  const job = elements.analyzerJob.value
  const daysBack = Math.max(1, Number(elements.analyzerDays.value || 30))
  const limit = Math.max(1, Number(elements.analyzerLimit.value || 500))
  const useSelected = elements.analyzerUseSelected.checked
  const senderIds = useSelected ? state.selectedChannels : []

  appendOpsLog(`Running ${job} analysis...`, 'info')
  try {
    const response = await fetch('/api/analyzer/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job,
        days_back: daysBack,
        limit,
        sender_ids: senderIds,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Analyzer failed')
    }

    const data = await response.json()
    appendOpsLog('Analyzer completed', 'success')
    appendRunLog(`Analyzer output ready (${job})`, 'success')
    addResultFromAnalysis(job, data.output)
  } catch (error: any) {
    appendOpsLog(error.message || 'Analyzer failed', 'error')
  }
}

function addResultFromAnalysis(job: string, output: string) {
  const result: Result = {
    id: crypto.randomUUID(),
    prompt: `Analyzer job: ${job}`,
    response: output,
    createdAt: new Date().toISOString(),
    contextCount: 0,
    senderIds: [...state.selectedChannels],
    modelId: state.selectedModel,
  }
  state.results.unshift(result)
  state.activeResultId = result.id
  saveResults()
  saveActiveResult()
  renderResults()
  renderSessions()
}

function loadStoredResults() {
  try {
    const stored = localStorage.getItem(RESULTS_STORAGE_KEY)
    state.results = stored ? (JSON.parse(stored) as Result[]) : []
  } catch {
    state.results = []
  }

  const active = localStorage.getItem(ACTIVE_RESULT_KEY)
  state.activeResultId = active || null
}

function saveResults() {
  localStorage.setItem(RESULTS_STORAGE_KEY, JSON.stringify(state.results))
}

function saveActiveResult() {
  if (state.activeResultId) localStorage.setItem(ACTIVE_RESULT_KEY, state.activeResultId)
  else localStorage.removeItem(ACTIVE_RESULT_KEY)
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text).then(
    () => appendRunLog('Copied to clipboard', 'success'),
    () => appendRunLog('Failed to copy', 'error'),
  )
}

function escapeHtml(text: string) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}
