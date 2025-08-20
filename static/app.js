// Server Provisioning System - Custom JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Form validation feedback
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Dynamic form field updates
    const serverTypeSelect = document.getElementById('server_type');
    if (serverTypeSelect) {
        serverTypeSelect.addEventListener('change', function() {
            updateHardwareRecommendations(this.value);
        });
    }

    // Search functionality for admin dashboard
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        // Add live search with debounce
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(function() {
                // Auto-submit form after 500ms of no typing
                if (searchInput.value.length > 2 || searchInput.value.length === 0) {
                    searchInput.form.submit();
                }
            }, 500);
        });
    }

    // Progress bar animations
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(function(bar) {
        const width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(function() {
            bar.style.width = width;
        }, 100);
    });

    // Notification mark as read functionality
    const notificationLinks = document.querySelectorAll('.notification-mark-read');
    notificationLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const notificationId = this.dataset.notificationId;
            markNotificationAsRead(notificationId);
        });
    });

    // Copy request ID functionality
    const copyButtons = document.querySelectorAll('.copy-request-id');
    copyButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const requestId = this.dataset.requestId;
            copyToClipboard(requestId);
            showToast('Request ID copied to clipboard!');
        });
    });

    // Status refresh for pending requests
    if (window.location.pathname.includes('/request/') && 
        document.querySelector('.badge.bg-warning')) {
        // Auto-refresh every 30 seconds for pending requests
        setInterval(function() {
            location.reload();
        }, 30000);
    }
});

// Helper function to update hardware recommendations
function updateHardwareRecommendations(serverType) {
    const recommendations = {
        'web': { cpu: 2, memory: 4, storage: 50 },
        'database': { cpu: 4, memory: 16, storage: 250 },
        'application': { cpu: 4, memory: 8, storage: 100 },
        'cache': { cpu: 2, memory: 8, storage: 20 },
        'file': { cpu: 2, memory: 4, storage: 1000 },
        'backup': { cpu: 1, memory: 2, storage: 2000 },
        'development': { cpu: 2, memory: 4, storage: 50 },
        'testing': { cpu: 1, memory: 2, storage: 50 }
    };

    const rec = recommendations[serverType];
    if (rec) {
        const cpuSelect = document.getElementById('cpu_cores');
        const memorySelect = document.getElementById('memory_gb');
        const storageSelect = document.getElementById('storage_gb');

        if (cpuSelect && cpuSelect.value === '') {
            cpuSelect.value = rec.cpu;
        }
        if (memorySelect && memorySelect.value === '') {
            memorySelect.value = rec.memory;
        }
        if (storageSelect && storageSelect.value === '') {
            storageSelect.value = rec.storage;
        }
    }
}

// Helper function to mark notification as read
function markNotificationAsRead(notificationId) {
    fetch(`/notifications/mark-read/${notificationId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (response.ok) {
            const notificationElement = document.querySelector(`[data-notification-id="${notificationId}"]`);
            if (notificationElement) {
                notificationElement.style.opacity = '0.5';
            }
        }
    })
    .catch(error => {
        console.error('Error marking notification as read:', error);
    });
}

// Helper function to copy text to clipboard
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            document.execCommand('copy');
        } catch (err) {
            console.error('Failed to copy text: ', err);
        }
        document.body.removeChild(textArea);
    }
}

// Helper function to show toast notifications
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Helper function to create toast container
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'position-fixed bottom-0 end-0 p-3';
    container.style.zIndex = '1050';
    document.body.appendChild(container);
    return container;
}

// Utility function for debouncing
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

// Format numbers for better display
function formatNumber(num) {
    return new Intl.NumberFormat().format(num);
}

// Format dates for better display
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

// Auto-save form data to localStorage
function enableAutoSave(formId) {
    const form = document.getElementById(formId);
    if (!form) return;

    const saveKey = `autosave_${formId}`;
    
    // Load saved data
    const savedData = localStorage.getItem(saveKey);
    if (savedData) {
        const data = JSON.parse(savedData);
        Object.keys(data).forEach(key => {
            const field = form.querySelector(`[name="${key}"]`);
            if (field) {
                field.value = data[key];
            }
        });
    }
    
    // Save data on input
    form.addEventListener('input', debounce(function() {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);
        localStorage.setItem(saveKey, JSON.stringify(data));
    }, 1000));
    
    // Clear saved data on successful submit
    form.addEventListener('submit', function() {
        localStorage.removeItem(saveKey);
    });
}

// Initialize auto-save for server request form
if (document.getElementById('server-request-form')) {
    enableAutoSave('server-request-form');
}
