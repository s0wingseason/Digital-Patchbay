/**
 * MB-76 Digital Patchbay Controller - Frontend Application
 * Interactive routing matrix and preset management
 */

// =============================================================================
// Configuration & State
// =============================================================================

const API_BASE = '';  // Same origin

const state = {
    config: null,
    presets: [],
    currentPreset: null,
    currentBank: null,
    routingMatrix: {},  // { inputId: [outputIds] }
    midiConnected: false,
    midiDevice: null,
    midiChannel: 1,
    inputs: [],
    outputs: []
};

// =============================================================================
// API Functions
// =============================================================================

async function api(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'API request failed');
        }

        return data;
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        showToast(error.message, 'error');
        throw error;
    }
}

// Config API
const configApi = {
    get: () => api('/api/config'),
    update: (data) => api('/api/config', { method: 'POST', body: JSON.stringify(data) })
};

// MIDI API
const midiApi = {
    getDevices: () => api('/api/midi/devices'),
    connect: (device) => api('/api/midi/connect', {
        method: 'POST',
        body: JSON.stringify({ device })
    }),
    disconnect: () => api('/api/midi/disconnect', { method: 'POST' })
};

// Bank API
const bankApi = {
    recall: (bank) => api(`/api/bank/${bank}`, { method: 'POST' })
};

// Preset API
const presetApi = {
    getAll: () => api('/api/presets'),
    get: (id) => api(`/api/presets/${id}`),
    create: (data) => api('/api/presets', { method: 'POST', body: JSON.stringify(data) }),
    update: (id, data) => api(`/api/presets/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id) => api(`/api/presets/${id}`, { method: 'DELETE' }),
    recall: (id) => api(`/api/presets/${id}/recall`, { method: 'POST' })
};

// =============================================================================
// UI Initialization
// =============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    await initializeApp();
    setupEventListeners();
});

async function initializeApp() {
    try {
        // Load configuration
        const configData = await configApi.get();
        state.config = configData.config;
        state.midiConnected = configData.midi_status.connected;
        state.midiDevice = configData.midi_status.device;
        state.midiChannel = configData.midi_status.channel;

        // Set I/O configuration
        state.inputs = state.config.mb76?.inputs || generateDefaultInputs();
        state.outputs = state.config.mb76?.outputs || generateDefaultOutputs();

        // Build UI
        buildRoutingMatrix();
        buildBankGrid();
        buildSettingsForm();

        // Load presets
        await loadPresets();

        // Update connection status
        updateConnectionStatus();
        updateStatusBar();

    } catch (error) {
        console.error('Failed to initialize app:', error);
        showToast('Failed to connect to server. Is the backend running?', 'error');
    }
}

function generateDefaultInputs() {
    return Array.from({ length: 7 }, (_, i) => ({
        id: i + 1,
        name: `Input ${i + 1}`,
        description: ''
    }));
}

function generateDefaultOutputs() {
    return Array.from({ length: 6 }, (_, i) => ({
        id: i + 1,
        name: `Output ${i + 1}`,
        description: ''
    }));
}

// =============================================================================
// Routing Matrix
// =============================================================================

function buildRoutingMatrix() {
    const outputsContainer = document.getElementById('matrixOutputs');
    const inputsContainer = document.getElementById('matrixInputs');
    const gridContainer = document.getElementById('matrixGrid');

    // Clear existing
    outputsContainer.innerHTML = '';
    inputsContainer.innerHTML = '';
    gridContainer.innerHTML = '';

    // Build output headers
    state.outputs.forEach(output => {
        const header = document.createElement('div');
        header.className = 'output-header';
        header.innerHTML = `
            <span class="output-num">OUT ${output.id}</span>
            <span class="output-name" title="${output.name}">${output.name}</span>
        `;
        outputsContainer.appendChild(header);
    });

    // Build input rows and crosspoints
    state.inputs.forEach(input => {
        // Input label
        const inputRow = document.createElement('div');
        inputRow.className = 'input-row';
        inputRow.innerHTML = `
            <span class="input-num">IN ${input.id}</span>
            <span class="input-name" title="${input.name}">${input.name}</span>
        `;
        inputsContainer.appendChild(inputRow);

        // Crosspoints row
        const crosspointRow = document.createElement('div');
        crosspointRow.className = 'crosspoint-row';

        state.outputs.forEach(output => {
            const crosspoint = document.createElement('div');
            crosspoint.className = 'crosspoint';
            crosspoint.dataset.input = input.id;
            crosspoint.dataset.output = output.id;
            crosspoint.title = `${input.name} → ${output.name}`;

            // Check if active
            if (isRouted(input.id, output.id)) {
                crosspoint.classList.add('active');
            }

            crosspoint.addEventListener('click', () => toggleCrosspoint(input.id, output.id));
            crosspointRow.appendChild(crosspoint);
        });

        gridContainer.appendChild(crosspointRow);
    });
}

function isRouted(inputId, outputId) {
    const outputs = state.routingMatrix[inputId] || [];
    return outputs.includes(outputId);
}

function toggleCrosspoint(inputId, outputId) {
    if (!state.routingMatrix[inputId]) {
        state.routingMatrix[inputId] = [];
    }

    const outputs = state.routingMatrix[inputId];
    const index = outputs.indexOf(outputId);

    if (index === -1) {
        // Add routing
        outputs.push(outputId);
    } else {
        // Remove routing
        outputs.splice(index, 1);
    }

    // Update UI
    updateCrosspointUI(inputId, outputId);
    updateStatusBar();
}

function updateCrosspointUI(inputId, outputId) {
    const crosspoint = document.querySelector(
        `.crosspoint[data-input="${inputId}"][data-output="${outputId}"]`
    );

    if (crosspoint) {
        if (isRouted(inputId, outputId)) {
            crosspoint.classList.add('active');
        } else {
            crosspoint.classList.remove('active');
        }
    }
}

function clearMatrix() {
    state.routingMatrix = {};

    // Update all crosspoints
    document.querySelectorAll('.crosspoint').forEach(cp => {
        cp.classList.remove('active');
    });

    updateStatusBar();
    showToast('Routing matrix cleared', 'info');
}

function loadMatrixFromPreset(preset) {
    state.routingMatrix = { ...preset.routing_matrix };

    // Convert string keys to numbers if needed
    const newMatrix = {};
    Object.entries(state.routingMatrix).forEach(([key, value]) => {
        newMatrix[parseInt(key)] = value.map(v => parseInt(v));
    });
    state.routingMatrix = newMatrix;

    // Update UI
    document.querySelectorAll('.crosspoint').forEach(cp => {
        const inputId = parseInt(cp.dataset.input);
        const outputId = parseInt(cp.dataset.output);

        if (isRouted(inputId, outputId)) {
            cp.classList.add('active');
        } else {
            cp.classList.remove('active');
        }
    });
}

// =============================================================================
// Bank Grid (Quick Recall)
// =============================================================================

function buildBankGrid() {
    const grid = document.getElementById('bankGrid');
    grid.innerHTML = '';

    for (let bank = 1; bank <= 32; bank++) {
        const btn = document.createElement('button');
        btn.className = 'bank-btn';
        btn.textContent = bank;
        btn.dataset.bank = bank;
        btn.addEventListener('click', () => recallBank(bank));
        grid.appendChild(btn);
    }
}

async function recallBank(bank) {
    try {
        const result = await bankApi.recall(bank);

        if (result.success) {
            state.currentBank = bank;
            updateBankActiveState(bank);
            updateStatusBar();
            showToast(`Bank ${bank} recalled`, 'success');
        }
    } catch (error) {
        showToast(`Failed to recall bank ${bank}`, 'error');
    }
}

function updateBankActiveState(activeBank) {
    document.querySelectorAll('.bank-btn').forEach(btn => {
        if (parseInt(btn.dataset.bank) === activeBank) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

// =============================================================================
// Presets
// =============================================================================

async function loadPresets() {
    try {
        const data = await presetApi.getAll();
        state.presets = data.presets || [];
        renderPresetList();
    } catch (error) {
        console.error('Failed to load presets:', error);
    }
}

function renderPresetList() {
    const list = document.getElementById('presetList');
    list.innerHTML = '';

    if (state.presets.length === 0) {
        list.innerHTML = `
            <div class="preset-empty">
                <p>No presets saved yet.</p>
                <p>Create one using the "New" button above.</p>
            </div>
        `;
        return;
    }

    state.presets.forEach(preset => {
        const item = document.createElement('div');
        item.className = 'preset-item';
        if (state.currentPreset?.id === preset.id) {
            item.classList.add('active');
        }

        item.innerHTML = `
            <div class="preset-bank">${preset.bank_number}</div>
            <div class="preset-info">
                <div class="preset-name">${escapeHtml(preset.name)}</div>
                <div class="preset-desc">${preset.route_count} routes</div>
            </div>
            <div class="preset-actions">
                <button class="btn btn-sm btn-icon" title="Recall" data-action="recall">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="5 3 19 12 5 21 5 3"/>
                    </svg>
                </button>
                <button class="btn btn-sm btn-icon" title="Delete" data-action="delete">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                </button>
            </div>
        `;

        // Click to load into matrix
        item.addEventListener('click', (e) => {
            if (e.target.closest('[data-action]')) return;
            selectPreset(preset);
        });

        // Recall button
        item.querySelector('[data-action="recall"]').addEventListener('click', (e) => {
            e.stopPropagation();
            recallPreset(preset);
        });

        // Delete button
        item.querySelector('[data-action="delete"]').addEventListener('click', (e) => {
            e.stopPropagation();
            deletePreset(preset);
        });

        list.appendChild(item);
    });
}

async function selectPreset(preset) {
    try {
        const data = await presetApi.get(preset.id);
        state.currentPreset = data.preset;
        loadMatrixFromPreset(data.preset);
        renderPresetList();
        updateStatusBar();
        showToast(`Loaded "${preset.name}"`, 'info');
    } catch (error) {
        showToast('Failed to load preset', 'error');
    }
}

async function recallPreset(preset) {
    try {
        const result = await presetApi.recall(preset.id);

        if (result.success) {
            state.currentBank = preset.bank_number;
            state.currentPreset = result.preset;
            loadMatrixFromPreset(result.preset);
            updateBankActiveState(preset.bank_number);
            renderPresetList();
            updateStatusBar();
            showToast(`Recalled "${preset.name}" (Bank ${preset.bank_number})`, 'success');
        }
    } catch (error) {
        showToast('Failed to recall preset', 'error');
    }
}

async function deletePreset(preset) {
    if (!confirm(`Delete preset "${preset.name}"?`)) return;

    try {
        await presetApi.delete(preset.id);
        await loadPresets();

        if (state.currentPreset?.id === preset.id) {
            state.currentPreset = null;
        }

        showToast('Preset deleted', 'info');
    } catch (error) {
        showToast('Failed to delete preset', 'error');
    }
}

// =============================================================================
// Settings
// =============================================================================

function buildSettingsForm() {
    // MIDI Channel dropdown
    const channelSelect = document.getElementById('midiChannel');
    channelSelect.innerHTML = '';
    for (let ch = 1; ch <= 16; ch++) {
        const option = document.createElement('option');
        option.value = ch;
        option.textContent = `Channel ${ch}`;
        option.selected = ch === state.midiChannel;
        channelSelect.appendChild(option);
    }

    // Bank dropdown for preset modal
    const bankSelect = document.getElementById('presetBank');
    bankSelect.innerHTML = '';
    for (let bank = 1; bank <= 32; bank++) {
        const option = document.createElement('option');
        option.value = bank;
        option.textContent = `Bank ${bank}`;
        bankSelect.appendChild(option);
    }

    // I/O Labels
    buildIOLabels('inputLabels', state.inputs, 'IN');
    buildIOLabels('outputLabels', state.outputs, 'OUT');
}

function buildIOLabels(containerId, items, prefix) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    items.forEach(item => {
        const row = document.createElement('div');
        row.className = 'io-label-item';
        row.innerHTML = `
            <span>${prefix} ${item.id}</span>
            <input type="text" class="form-control" 
                   value="${escapeHtml(item.name)}" 
                   data-id="${item.id}"
                   placeholder="${prefix} ${item.id}">
        `;
        container.appendChild(row);
    });
}

async function refreshMidiDevices() {
    try {
        const data = await midiApi.getDevices();
        const select = document.getElementById('midiDevice');
        select.innerHTML = '<option value="">Select a device...</option>';

        data.devices.forEach(device => {
            const option = document.createElement('option');
            option.value = device;
            option.textContent = device;
            option.selected = device === data.current_device;
            select.appendChild(option);
        });

        if (data.devices.length === 0) {
            showToast('No MIDI devices found', 'warning');
        }
    } catch (error) {
        showToast('Failed to refresh MIDI devices', 'error');
    }
}

async function saveSettings() {
    try {
        // Gather I/O labels
        const inputs = [];
        document.querySelectorAll('#inputLabels input').forEach(input => {
            inputs.push({
                id: parseInt(input.dataset.id),
                name: input.value || `Input ${input.dataset.id}`,
                description: ''
            });
        });

        const outputs = [];
        document.querySelectorAll('#outputLabels input').forEach(input => {
            outputs.push({
                id: parseInt(input.dataset.id),
                name: input.value || `Output ${input.dataset.id}`,
                description: ''
            });
        });

        // Get MIDI settings
        const midiDevice = document.getElementById('midiDevice').value;
        const midiChannel = parseInt(document.getElementById('midiChannel').value);

        // Save config
        await configApi.update({
            midi_device: midiDevice,
            midi_channel: midiChannel,
            inputs: inputs,
            outputs: outputs
        });

        // Update local state
        state.inputs = inputs;
        state.outputs = outputs;
        state.midiChannel = midiChannel;

        // Reconnect MIDI if device changed
        if (midiDevice && midiDevice !== state.midiDevice) {
            await midiApi.connect(midiDevice);
            state.midiDevice = midiDevice;
            state.midiConnected = true;
        }

        // Rebuild matrix with new labels
        buildRoutingMatrix();
        updateConnectionStatus();
        updateStatusBar();

        closeModal('settingsModal');
        showToast('Settings saved', 'success');

    } catch (error) {
        showToast('Failed to save settings', 'error');
    }
}

async function testConnection() {
    try {
        const result = await api('/api/test', { method: 'POST' });

        if (result.success) {
            showToast('Connection test successful! Bank 1 sent.', 'success');
            state.currentBank = 1;
            updateBankActiveState(1);
            updateStatusBar();
        } else {
            showToast(result.error || 'Connection test failed', 'error');
        }
    } catch (error) {
        showToast('Connection test failed', 'error');
    }
}

// =============================================================================
// Event Listeners
// =============================================================================

function setupEventListeners() {
    // Settings modal
    document.getElementById('settingsBtn').addEventListener('click', () => {
        refreshMidiDevices();
        openModal('settingsModal');
    });

    document.getElementById('closeSettingsBtn').addEventListener('click', () => {
        closeModal('settingsModal');
    });

    document.getElementById('cancelSettingsBtn').addEventListener('click', () => {
        closeModal('settingsModal');
    });

    document.getElementById('saveSettingsBtn').addEventListener('click', saveSettings);
    document.getElementById('refreshDevicesBtn').addEventListener('click', refreshMidiDevices);
    document.getElementById('testConnectionBtn').addEventListener('click', testConnection);

    // Preset modal
    document.getElementById('newPresetBtn').addEventListener('click', () => {
        document.getElementById('presetModalTitle').textContent = 'New Preset';
        document.getElementById('presetName').value = '';
        document.getElementById('presetBank').value = '1';
        document.getElementById('presetDescription').value = '';
        openModal('presetModal');
    });

    document.getElementById('savePresetBtn').addEventListener('click', () => {
        document.getElementById('presetModalTitle').textContent = 'Save Preset';
        document.getElementById('presetName').value = state.currentPreset?.name || '';
        document.getElementById('presetBank').value = state.currentPreset?.bank_number || '1';
        document.getElementById('presetDescription').value = state.currentPreset?.description || '';
        openModal('presetModal');
    });

    document.getElementById('closePresetBtn').addEventListener('click', () => {
        closeModal('presetModal');
    });

    document.getElementById('cancelPresetBtn').addEventListener('click', () => {
        closeModal('presetModal');
    });

    document.getElementById('confirmPresetBtn').addEventListener('click', savePreset);

    // Matrix controls
    document.getElementById('clearMatrixBtn').addEventListener('click', () => {
        if (confirm('Clear all routing assignments?')) {
            clearMatrix();
        }
    });

    // Modal overlays
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', () => {
            closeModal(overlay.closest('.modal').id);
        });
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.active').forEach(modal => {
                closeModal(modal.id);
            });
        }
    });
}

async function savePreset() {
    const name = document.getElementById('presetName').value.trim();
    const bank = parseInt(document.getElementById('presetBank').value);
    const description = document.getElementById('presetDescription').value.trim();

    if (!name) {
        showToast('Please enter a preset name', 'error');
        return;
    }

    try {
        const presetData = {
            name: name,
            bank_number: bank,
            description: description,
            routing_matrix: state.routingMatrix
        };

        let result;
        if (state.currentPreset && document.getElementById('presetModalTitle').textContent === 'Save Preset') {
            // Update existing
            result = await presetApi.update(state.currentPreset.id, presetData);
        } else {
            // Create new
            result = await presetApi.create(presetData);
        }

        if (result.success) {
            state.currentPreset = result.preset;
            await loadPresets();
            closeModal('presetModal');
            showToast(`Preset "${name}" saved`, 'success');
        }
    } catch (error) {
        showToast('Failed to save preset', 'error');
    }
}

// =============================================================================
// UI Helpers
// =============================================================================

function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

function updateConnectionStatus() {
    const statusContainer = document.getElementById('connectionStatus');
    const dot = statusContainer.querySelector('.status-dot');
    const text = statusContainer.querySelector('.status-text');

    if (state.midiConnected && state.midiDevice) {
        dot.className = 'status-dot connected';
        text.textContent = 'Connected';
    } else {
        dot.className = 'status-dot disconnected';
        text.textContent = 'Disconnected';
    }
}

function updateStatusBar() {
    document.getElementById('midiDeviceStatus').textContent =
        state.midiDevice || 'Not Connected';

    document.getElementById('midiChannelStatus').textContent =
        state.midiChannel;

    document.getElementById('currentBankStatus').textContent =
        state.currentBank || '-';

    // Count active routes
    let routeCount = 0;
    Object.values(state.routingMatrix).forEach(outputs => {
        routeCount += outputs.length;
    });

    document.getElementById('lastActionStatus').textContent =
        `${routeCount} active routes`;
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span>${escapeHtml(message)}</span>
    `;

    container.appendChild(toast);

    // Auto-remove after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// =============================================================================
// Utility: Add empty preset styling
// =============================================================================

const style = document.createElement('style');
style.textContent = `
    .preset-empty {
        padding: var(--spacing-lg);
        text-align: center;
        color: var(--text-muted);
        font-size: 0.875rem;
    }
    .preset-empty p {
        margin-bottom: var(--spacing-xs);
    }
`;
document.head.appendChild(style);
