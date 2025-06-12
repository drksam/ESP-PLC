/**
 * JavaScript for AutomationDirect CLICK PLC Monitor
 * Handles real-time data updates and user interactions
 */

class PLCMonitor {
    constructor() {
        this.refreshInterval = null;
        this.refreshRate = 2000; // 2 seconds
        this.lastData = null;
        this.isConnected = false;
        
        // Initialize the application
        this.init();
    }
    
    init() {
        console.log('Initializing PLC Monitor...');
        
        // Start automatic refresh
        this.startAutoRefresh();
        
        // Initial data load
        this.refreshData();
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Manual refresh button
        document.addEventListener('DOMContentLoaded', () => {
            const refreshBtn = document.querySelector('[onclick="refreshData()"]');
            if (refreshBtn) {
                refreshBtn.addEventListener('click', () => this.refreshData());
            }
        });
        
        // Tab change events
        const tabElements = document.querySelectorAll('[data-bs-toggle="tab"]');
        tabElements.forEach(tab => {
            tab.addEventListener('shown.bs.tab', () => {
                this.updateActiveTabData();
            });
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'F5' || (e.ctrlKey && e.key === 'r')) {
                e.preventDefault();
                this.refreshData();
            }
        });
    }
    
    async refreshData() {
        try {
            console.log('Refreshing PLC data...');
            
            const response = await fetch('/api/status');
            const result = await response.json();
            
            if (result.success) {
                this.lastData = result.data;
                this.isConnected = result.data.connected;
                this.updateUI(result.data);
                this.hideError();
            } else {
                this.showError(`API Error: ${result.error}`);
                this.isConnected = false;
                this.updateConnectionStatus(false);
            }
        } catch (error) {
            console.error('Error refreshing data:', error);
            this.showError(`Connection Error: ${error.message}`);
            this.isConnected = false;
            this.updateConnectionStatus(false);
        }
    }
    
    updateUI(data) {
        // Update system information
        this.updateSystemInfo(data.system_info);
        
        // Update connection status
        this.updateConnectionStatus(data.connected);
        
        // Update status cards
        this.updateStatusCards(data);
        
        // Update PLC data displays
        this.updateDigitalInputs(data.input_status || {});
        this.updateDigitalOutputs(data.coil_status || {});
        this.updateDataRegisters(data.data_registers || {});
        
        console.log('UI updated successfully');
    }
    
    updateSystemInfo(systemInfo) {
        if (!systemInfo) return;
        
        const elements = {
            'plc-model': systemInfo.plc_model || 'Unknown',
            'comm-type': `${systemInfo.communication_type || 'Unknown'} @ ${systemInfo.baud_rate || 'Unknown'} baud`,
            'device-addr': systemInfo.device_address || 'Unknown',
            'last-update': this.formatTimestamp(this.lastData?.last_update)
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }
    
    updateConnectionStatus(connected) {
        const statusBadge = document.getElementById('connection-status');
        const connectionIndicator = document.getElementById('connection-indicator');
        
        if (connected) {
            statusBadge.className = 'badge bg-success me-3';
            statusBadge.innerHTML = '<i class="fas fa-check-circle me-1"></i>Connected';
            
            connectionIndicator.textContent = 'Connected';
            connectionIndicator.className = 'status-connected';
        } else {
            statusBadge.className = 'badge bg-danger me-3';
            statusBadge.innerHTML = '<i class="fas fa-exclamation-circle me-1"></i>Disconnected';
            
            connectionIndicator.textContent = 'Disconnected';
            connectionIndicator.className = 'status-disconnected';
        }
    }
    
    updateStatusCards(data) {
        // Communication errors
        const errorCount = document.getElementById('error-count');
        if (errorCount) {
            errorCount.textContent = data.communication_errors || 0;
        }
        
        // Data age
        const dataAge = document.getElementById('data-age');
        if (dataAge && data.data_age_seconds !== undefined) {
            dataAge.textContent = `${data.data_age_seconds}s`;
            
            // Color code based on age
            if (data.data_age_seconds > 10) {
                dataAge.className = 'text-danger';
            } else if (data.data_age_seconds > 5) {
                dataAge.className = 'text-warning';
            } else {
                dataAge.className = 'text-success';
            }
        }
    }
    
    updateDigitalInputs(inputs) {
        const container = document.getElementById('digital-inputs');
        if (!container) return;
        
        container.innerHTML = '';
        
        // Create input displays for X000-X015
        for (let i = 0; i < 16; i++) {
            const address = `X${i.toString().padStart(3, '0')}`;
            const value = inputs[address] || false;
            
            const inputElement = this.createDigitalIOElement(address, value, false);
            container.appendChild(inputElement);
        }
    }
    
    updateDigitalOutputs(outputs) {
        const container = document.getElementById('digital-outputs');
        if (!container) return;
        
        container.innerHTML = '';
        
        // Create output displays for Y000-Y015
        for (let i = 0; i < 16; i++) {
            const address = `Y${i.toString().padStart(3, '0')}`;
            const value = outputs[address] || false;
            
            const outputElement = this.createDigitalIOElement(address, value, true);
            container.appendChild(outputElement);
        }
    }
    
    createDigitalIOElement(address, value, isOutput) {
        const element = document.createElement('div');
        element.className = `digital-io-item ${value ? 'active' : 'inactive'}`;
        
        element.innerHTML = `
            <div class="digital-io-label">${address}</div>
            <div class="digital-io-status">
                <i class="fas ${value ? 'fa-circle' : 'fa-circle-o'}"></i>
            </div>
            <div class="digital-io-value">${value ? 'ON' : 'OFF'}</div>
        `;
        
        // Add click handler for outputs (if we want to support writing)
        if (isOutput && this.isConnected) {
            element.style.cursor = 'pointer';
            element.title = 'Click to toggle (if write access enabled)';
            
            element.addEventListener('click', () => {
                this.toggleOutput(address, !value);
            });
        }
        
        return element;
    }
    
    updateDataRegisters(registers) {
        const container = document.getElementById('data-registers');
        if (!container) return;
        
        container.innerHTML = '';
        
        // Create register displays for DS001-DS010
        for (let i = 1; i <= 10; i++) {
            const address = `DS${i.toString().padStart(3, '0')}`;
            const value = registers[address] || 0;
            
            const registerElement = this.createDataRegisterElement(address, value);
            container.appendChild(registerElement);
        }
    }
    
    createDataRegisterElement(address, value) {
        const colDiv = document.createElement('div');
        colDiv.className = 'col-md-6 col-lg-4 register-item';
        
        const hexValue = '0x' + value.toString(16).toUpperCase().padStart(4, '0');
        
        colDiv.innerHTML = `
            <div class="register-card">
                <div class="register-label">${address}</div>
                <div class="register-value">${value}</div>
                <div class="register-hex">${hexValue}</div>
            </div>
        `;
        
        return colDiv;
    }
    
    async toggleOutput(address, newValue) {
        if (!this.isConnected) {
            this.showError('Cannot write to PLC - not connected');
            return;
        }
        
        try {
            // Extract numeric address from string (Y001 -> 1)
            const numericAddress = parseInt(address.substring(1));
            
            const response = await fetch(`/api/coil/${numericAddress}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ value: newValue })
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log(`Successfully toggled ${address} to ${newValue}`);
                // Refresh data to show updated state
                setTimeout(() => this.refreshData(), 500);
            } else {
                this.showError(`Failed to toggle ${address}: ${result.message}`);
            }
        } catch (error) {
            console.error('Error toggling output:', error);
            this.showError(`Error toggling ${address}: ${error.message}`);
        }
    }
    
    startAutoRefresh() {
        this.stopAutoRefresh();
        this.refreshInterval = setInterval(() => {
            this.refreshData();
        }, this.refreshRate);
        
        console.log(`Auto-refresh started (${this.refreshRate}ms interval)`);
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    updateActiveTabData() {
        // Re-render data for the currently active tab
        if (this.lastData) {
            this.updateUI(this.lastData);
        }
    }
    
    showError(message) {
        const errorAlert = document.getElementById('error-alert');
        const errorMessage = document.getElementById('error-message');
        
        if (errorAlert && errorMessage) {
            errorMessage.textContent = message;
            errorAlert.style.display = 'block';
            
            // Auto-hide error after 10 seconds
            setTimeout(() => {
                this.hideError();
            }, 10000);
        }
        
        console.error('PLC Monitor Error:', message);
    }
    
    hideError() {
        const errorAlert = document.getElementById('error-alert');
        if (errorAlert) {
            errorAlert.style.display = 'none';
        }
    }
    
    formatTimestamp(timestamp) {
        if (!timestamp) return 'Never';
        
        try {
            const date = new Date(timestamp);
            return date.toLocaleString();
        } catch (error) {
            return 'Invalid';
        }
    }
}

// Global function for backward compatibility
function refreshData() {
    if (window.plcMonitor) {
        window.plcMonitor.refreshData();
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.plcMonitor = new PLCMonitor();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (window.plcMonitor) {
        if (document.hidden) {
            window.plcMonitor.stopAutoRefresh();
        } else {
            window.plcMonitor.startAutoRefresh();
            window.plcMonitor.refreshData();
        }
    }
});
