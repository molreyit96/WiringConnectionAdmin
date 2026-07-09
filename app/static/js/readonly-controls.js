class ReadOnlyManager {
    constructor(options = {}) {
        this.options = {
            alwaysEnabledSelectors: [
                '.close-btn',
                '.close-button',
                '.btn-close',
                '[data-bs-dismiss="modal"]',
                '.cancel-btn',
                '.back-btn',
                '.print-btn',
                '.export-btn',
                '.search-btn',
                '.search-button',
                '[data-always-enabled="true"]',
                ...options.alwaysEnabledSelectors || []
            ],
            ...options
        };
        
        this.isInitialized = false;
        this.isRefreshing = false;
        
        // Check if emp exists and is read-only
        if (typeof emp !== 'undefined' && emp.is_read_only) {
            this.init();
        }
    }
    
    init() {
        if (this.isInitialized && !this.isRefreshing) {
            return;
        }
        
        if (this.isRefreshing) {
            return;
        }
        
        this.isRefreshing = true;
        
        console.log('Read-only mode activated for employee:', emp.name || emp.id);
        this.disableFormSubmissions();
        this.disableInteractiveElements();
        this.disableActionLinks();
        this.disableHtmxElements();
        this.disableInputFields();
        this.addReadOnlyIndicators();
        this.handleModalForms();
        this.addBodyClass();
        
        this.isInitialized = true;
        this.isRefreshing = false;
    }
    
    // Check if an element should be exempt from read-only restrictions
    isExemptElement(element) {
        if (!element) return false;
        
        // Check if element matches any always-enabled selector
        const exempt = this.options.alwaysEnabledSelectors.some(selector => {
            try {
                return element.matches(selector) || element.closest(selector);
            } catch (e) {
                return false;
            }
        });
        
        // Also check if element has data-always-enabled="true" attribute
        if (element.dataset && element.dataset.alwaysEnabled === 'true') {
            return true;
        }
        
        // Check closest parent for data-always-enabled="true"
        const closestParent = element.closest('[data-always-enabled="true"]');
        if (closestParent) {
            return true;
        }
        
        return exempt;
    }
    
    // Add read-only class to body for CSS styling
    addBodyClass() {
        if (typeof emp !== 'undefined' && emp.is_read_only) {
            document.body.classList.add('readonly-mode');
        }
    }
    
    disableFormSubmissions() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            if (form.dataset.readonlyProcessed === 'true') {
                return;
            }
            
            if (this.isExemptElement(form)) {
                form.dataset.readonlyProcessed = 'true';
                return;
            }
            
            form.addEventListener('submit', (e) => {
                const submitButton = document.activeElement;
                if (this.isExemptElement(submitButton) || this.isExemptElement(form)) {
                    return;
                }
                
                e.preventDefault();
                e.stopPropagation();
                this.showNotification('This action is disabled in read-only mode.', 'warning');
                return false;
            });
            
            form.dataset.readonlyProcessed = 'true';
        });
    }
    
    disableInteractiveElements() {
        const selectors = [
            'button:not([data-always-enabled="true"]):not([data-readonly-processed])',
            'input[type="submit"]:not([data-always-enabled="true"]):not([data-readonly-processed])',
            'input[type="reset"]:not([data-always-enabled="true"]):not([data-readonly-processed])',
            'input[type="button"]:not([data-always-enabled="true"]):not([data-readonly-processed])',
            'button[onclick]:not([data-always-enabled="true"]):not([data-readonly-processed])'
        ];
        
        const elements = document.querySelectorAll(selectors.join(','));
        elements.forEach(element => {
            if (this.isExemptElement(element)) {
                element.dataset.readonlyProcessed = 'true';
                return;
            }
            
            if (element._originalClick) {
                return;
            }
            
            element._originalClick = element.onclick;
            element.onclick = null;
            
            element.disabled = true;
            element.style.opacity = '0.6';
            element.style.cursor = 'not-allowed';
            element.title = 'Disabled in read-only mode';
            element.classList.add('readonly-disabled');
            
            element.addEventListener('click', (e) => {
                if (!this.isExemptElement(e.target)) {
                    e.preventDefault();
                    e.stopPropagation();
                    this.showNotification('This action is disabled in read-only mode.', 'info');
                }
            });
            
            element.dataset.readonlyProcessed = 'true';
        });
    }
    
    // NEW: Comprehensive disableActionLinks - catches ALL action links
    disableActionLinks() {
        // Select all links that look like action buttons
        const selectors = [
            '.action-link',
            '.delete-link', 
            '.edit-link',
            '[data-action]',
            'a.btn-primary',
            'a.btn-success', 
            'a.btn-danger',
            'a.btn-warning',
            'a[href*="create"]',
            'a[href*="edit"]', 
            'a[href*="delete"]',
            'a[href*="update"]',
            'a[href*="add"]',
            'a[href*="remove"]',
            'a[href*="new"]'
        ];
        
        const actionLinks = document.querySelectorAll(selectors.join(','));
        
        actionLinks.forEach(link => {
            // Skip if already processed
            if (link.dataset.readonlyProcessed === 'true') {
                return;
            }
            
            // Skip if explicitly marked as always enabled
            if (this.isExemptElement(link)) {
                link.dataset.readonlyProcessed = 'true';
                return;
            }
            
            // Skip if it's a close, cancel, back, or search button
            if (link.matches('.close-btn, .close-button, .btn-close, .cancel-btn, .back-btn, .search-btn, .search-button')) {
                link.dataset.readonlyProcessed = 'true';
                return;
            }
            
            // Check if it's a safe navigation link (home, dashboard, etc.)
            const href = link.getAttribute('href');
            if (href) {
                const safePaths = ['/', '/home', '/dashboard', '/index', '/logout', '/login'];
                if (safePaths.includes(href) || href === '' || href === '#') {
                    link.dataset.readonlyProcessed = 'true';
                    return;
                }
            }
            
            // Store original href
            link._originalHref = link.getAttribute('href');
            
            // Remove href to prevent navigation
            link.removeAttribute('href');
            link.style.cursor = 'not-allowed';
            link.style.opacity = '0.6';
            link.style.pointerEvents = 'none';
            link.title = 'Disabled in read-only mode';
            link.classList.add('readonly-disabled');
            
            // Add click handler to show notification
            link.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.showNotification('This action is disabled in read-only mode.', 'info');
                return false;
            });
            
            // Add lock icon for action links
            this.addLockIconToElement(link);
            
            link.dataset.readonlyProcessed = 'true';
        });
    }
    
    // Handle HTMX elements
    disableHtmxElements() {
        const htmxSelectors = [
            '[hx-get]',
            '[hx-post]',
            '[hx-put]',
            '[hx-delete]',
            '[hx-patch]'
        ];
        
        const htmxElements = document.querySelectorAll(htmxSelectors.join(','));
        
        htmxElements.forEach(element => {
            if (element.dataset.readonlyProcessed === 'true') {
                return;
            }
            
            if (this.isExemptElement(element)) {
                element.dataset.readonlyProcessed = 'true';
                return;
            }
            
            if (element.dataset.alwaysEnabled === 'false') {
                this.disableHtmxElement(element);
                return;
            }
            
            const parent = element.closest('[data-always-enabled="false"]');
            if (parent) {
                this.disableHtmxElement(element);
                return;
            }
            
            if (element.matches('.close-btn, .close-button, .btn-close, .cancel-btn, .back-btn, .print-btn, .export-btn, .search-btn, .search-button')) {
                element.dataset.readonlyProcessed = 'true';
                return;
            }
            
            this.disableHtmxElement(element);
        });
    }
    
    // Helper method to disable a single HTMX element
    disableHtmxElement(element) {
        const htmxAttrs = ['hx-get', 'hx-post', 'hx-put', 'hx-delete', 'hx-patch', 'hx-target', 'hx-swap'];
        const originalAttrs = {};
        
        htmxAttrs.forEach(attr => {
            if (element.hasAttribute(attr)) {
                originalAttrs[attr] = element.getAttribute(attr);
                element.removeAttribute(attr);
            }
        });
        
        element._originalHtmxAttrs = originalAttrs;
        
        element.style.cursor = 'not-allowed';
        element.style.opacity = '0.5';
        element.classList.add('readonly-disabled', 'htmx-disabled');
        element.title = 'Disabled in read-only mode';
        
        element.removeEventListener('click', this._htmxClickHandler);
        element.addEventListener('click', this._htmxClickHandler = (e) => {
            if (!this.isExemptElement(e.target)) {
                e.preventDefault();
                e.stopPropagation();
                this.showNotification('This action is disabled in read-only mode.', 'info');
                return false;
            }
        });
        
        // Add lock icon ONLY for buttons and action links, NOT for text inputs
        this.addLockIconToElement(element);
        
        if (element.tagName === 'BUTTON' || element.tagName === 'INPUT') {
            element.disabled = true;
        }
        
        element.dataset.readonlyProcessed = 'true';
        
        if (element.tagName === 'A') {
            element.href = 'javascript:void(0)';
            element.style.pointerEvents = 'none';
        }
    }
    
    // Restore HTMX elements
    restoreHtmxElement(element) {
        if (element._originalHtmxAttrs) {
            Object.keys(element._originalHtmxAttrs).forEach(attr => {
                element.setAttribute(attr, element._originalHtmxAttrs[attr]);
            });
        }
        
        element.style.cursor = '';
        element.style.opacity = '';
        element.classList.remove('readonly-disabled', 'htmx-disabled');
        element.title = '';
        
        // Remove lock icon if exists
        const lockIcon = element.querySelector('.readonly-icon');
        if (lockIcon) {
            lockIcon.remove();
        }
        
        if (element.tagName === 'A') {
            element.href = element._originalHref || '';
            element.style.pointerEvents = '';
        }
        
        if (element.tagName === 'BUTTON' || element.tagName === 'INPUT') {
            element.disabled = false;
        }
        
        element.dataset.readonlyProcessed = 'false';
    }
    
    // Add lock icon only to appropriate elements (buttons, links, actions)
    addLockIconToElement(element) {
        // Skip adding lock icon to text inputs, textareas, selects
        if (element.tagName === 'INPUT' || 
            element.tagName === 'TEXTAREA' || 
            element.tagName === 'SELECT') {
            return;
        }
        
        // Skip if it's a plain text input type
        if (element.tagName === 'INPUT' && 
            ['text', 'email', 'password', 'number', 'tel', 'url', 'search'].includes(element.type)) {
            return;
        }
        
        // Skip if element already has a lock icon
        if (element.querySelector('.readonly-icon')) {
            return;
        }
        
        // Only add lock icon to buttons, links, and interactive elements
        if (element.tagName === 'BUTTON' || 
            element.tagName === 'A' || 
            element.tagName === 'SPAN' || 
            element.tagName === 'DIV' ||
            element.matches('[hx-get], [hx-post], [hx-put], [hx-delete]')) {
            
            const indicator = document.createElement('span');
            indicator.className = 'readonly-icon ms-1';
            indicator.innerHTML = '🔒';
            indicator.style.fontSize = '0.7em';
            indicator.title = 'Read-only mode';
            element.appendChild(indicator);
        }
    }
    
    disableInputFields() {
        // Disable text inputs - NO lock icons
        const inputs = document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="reset"]):not([type="button"]):not([data-readonly-processed])');
        inputs.forEach(input => {
            if (this.isExemptElement(input)) {
                input.dataset.readonlyProcessed = 'true';
                return;
            }
            
            input.disabled = true;
            input.readOnly = true;
            input.style.backgroundColor = '#f8f9fa';
            input.style.cursor = 'not-allowed';
            input.classList.add('readonly-disabled');
            input.dataset.readonlyProcessed = 'true';
            // NO lock icon added here
        });
        
        // Disable textareas - NO lock icons
        const textareas = document.querySelectorAll('textarea:not([data-readonly-processed])');
        textareas.forEach(textarea => {
            if (this.isExemptElement(textarea)) {
                textarea.dataset.readonlyProcessed = 'true';
                return;
            }
            
            textarea.disabled = true;
            textarea.readOnly = true;
            textarea.style.backgroundColor = '#f8f9fa';
            textarea.style.cursor = 'not-allowed';
            textarea.classList.add('readonly-disabled');
            textarea.dataset.readonlyProcessed = 'true';
            // NO lock icon added here
        });
        
        // Disable select dropdowns - NO lock icons
        const selects = document.querySelectorAll('select:not([data-readonly-processed])');
        selects.forEach(select => {
            if (this.isExemptElement(select)) {
                select.dataset.readonlyProcessed = 'true';
                return;
            }
            
            select.disabled = true;
            select.style.backgroundColor = '#f8f9fa';
            select.style.cursor = 'not-allowed';
            select.classList.add('readonly-disabled');
            select.dataset.readonlyProcessed = 'true';
            // NO lock icon added here
        });
        
        // Disable checkbox and radio inputs - NO lock icons
        const checkable = document.querySelectorAll('input[type="checkbox"]:not([data-readonly-processed]), input[type="radio"]:not([data-readonly-processed])');
        checkable.forEach(input => {
            if (this.isExemptElement(input)) {
                input.dataset.readonlyProcessed = 'true';
                return;
            }
            
            input.disabled = true;
            input.style.cursor = 'not-allowed';
            input.classList.add('readonly-disabled');
            
            input.addEventListener('click', (e) => {
                e.preventDefault();
                this.showNotification('This action is disabled in read-only mode.', 'info');
            });
            
            input.dataset.readonlyProcessed = 'true';
            // NO lock icon added here
        });
    }
    
    addReadOnlyIndicators() {
        // Only add info bar once
        if (document.querySelector('.readonly-info-bar')) {
            return;
        }
        
        // Add lock icons to buttons and action links that don't have them yet
        const interactiveElements = document.querySelectorAll(
            'button.readonly-disabled:not([data-indicator-added]), ' +
            'a.readonly-disabled:not([data-indicator-added]), ' +
            '.action-link.readonly-disabled:not([data-indicator-added]), ' +
            '.delete-link.readonly-disabled:not([data-indicator-added]), ' +
            '.edit-link.readonly-disabled:not([data-indicator-added])'
        );
        
        interactiveElements.forEach(el => {
            this.addLockIconToElement(el);
            el.dataset.indicatorAdded = 'true';
        });
        
        // Show employee info in read-only mode
        if (typeof emp !== 'undefined' && emp.is_read_only) {
            const infoBar = document.createElement('div');
            infoBar.className = 'readonly-info-bar alert alert-info';
            infoBar.id = 'readonly-info-bar';
            infoBar.innerHTML = `
                <i class="fas fa-eye"></i> 
                <strong>Read-Only Mode</strong> - 
                ${emp.name || 'Employee'} is viewing in read-only mode
                <button type="button" class="btn-close float-end" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            infoBar.style.position = 'fixed';
            infoBar.style.bottom = '20px';
            infoBar.style.right = '20px';
            infoBar.style.zIndex = '9999';
            infoBar.style.maxWidth = '300px';
            infoBar.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
            infoBar.style.borderRadius = '8px';
            infoBar.style.fontSize = '0.9rem';
            document.body.appendChild(infoBar);
        }
    }
    
    handleModalForms() {
        document.addEventListener('show.bs.modal', (e) => {
            const modal = e.target;
            const forms = modal.querySelectorAll('form');
            
            forms.forEach(form => {
                if (this.isExemptElement(form) || form.dataset.readonlyProcessed === 'true') {
                    return;
                }
                
                const closeButtons = modal.querySelectorAll('.btn-close, .close, [data-bs-dismiss="modal"]');
                closeButtons.forEach(btn => {
                    btn.dataset.alwaysEnabled = 'true';
                    btn.disabled = false;
                    btn.style.opacity = '1';
                    btn.style.cursor = 'pointer';
                    btn.dataset.readonlyProcessed = 'true';
                });
            });
        });
    }
    
    showNotification(message, type = 'info') {
        if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
            document.querySelectorAll('.readonly-notification').forEach(el => el.remove());
            
            const alertHtml = `
                <div class="alert alert-${type} alert-dismissible fade show readonly-notification position-fixed top-0 start-50 translate-middle-x mt-3" 
                     style="z-index: 9999; min-width: 300px; max-width: 90%;" role="alert">
                    <i class="fas fa-${type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
            
            const container = document.createElement('div');
            container.innerHTML = alertHtml;
            document.body.appendChild(container.firstElementChild);
            
            setTimeout(() => {
                const alerts = document.querySelectorAll('.readonly-notification');
                if (alerts.length > 0) {
                    const lastAlert = alerts[alerts.length - 1];
                    if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                        const bsAlert = new bootstrap.Alert(lastAlert);
                        bsAlert.close();
                    } else {
                        lastAlert.remove();
                    }
                }
            }, 3000);
        } else {
            alert(message);
        }
    }
    
    addException(selector) {
        if (!this.options.alwaysEnabledSelectors.includes(selector)) {
            this.options.alwaysEnabledSelectors.push(selector);
        }
    }
    
    refresh() {
        document.querySelectorAll('[data-readonly-processed]').forEach(el => {
            if (!el.dataset.alwaysEnabled) {
                // Keep the flag for elements that are already processed
            }
        });
        
        this.init();
    }
    
    destroy() {
        this.isInitialized = false;
    }
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize only once
let readOnlyManagerInstance = null;

document.addEventListener('DOMContentLoaded', function() {
    if (typeof emp !== 'undefined' && emp.is_read_only && !readOnlyManagerInstance) {
        readOnlyManagerInstance = new ReadOnlyManager({
            alwaysEnabledSelectors: [
                '.close-btn',
                '.close-button',
                '.btn-close',
                '[data-bs-dismiss="modal"]',
                '.cancel-btn',
                '.back-btn',
                '.print-btn',
                '.export-btn',
                '.search-btn',
                '.search-button',
                '[data-always-enabled="true"]'
            ]
        });
        console.log('Read-only manager initialized successfully');
    } else if (typeof emp !== 'undefined' && emp.is_read_only && readOnlyManagerInstance) {
        console.log('Read-only manager already initialized');
    }
});

// Debounced refresh for dynamic content
const debouncedRefresh = debounce(function() {
    if (readOnlyManagerInstance) {
        readOnlyManagerInstance.refresh();
    }
}, 250);

// Handle HTMX events
document.addEventListener('htmx:afterSwap', function() {
    debouncedRefresh();
});

document.addEventListener('htmx:afterSettle', function() {
    debouncedRefresh();
});

document.addEventListener('htmx:afterOnLoad', function() {
    debouncedRefresh();
});

// Handle Turbo
document.addEventListener('turbo:render', function() {
    debouncedRefresh();
});

// MutationObserver with debouncing
if (window.MutationObserver && typeof emp !== 'undefined' && emp.is_read_only) {
    let observerTimeout = null;
    
    const observer = new MutationObserver(function(mutations) {
        let hasAddedNodes = false;
        for (const mutation of mutations) {
            if (mutation.addedNodes.length > 0) {
                hasAddedNodes = true;
                break;
            }
        }
        
        if (hasAddedNodes && readOnlyManagerInstance) {
            if (observerTimeout) {
                clearTimeout(observerTimeout);
            }
            
            observerTimeout = setTimeout(function() {
                if (readOnlyManagerInstance && !readOnlyManagerInstance.isRefreshing) {
                    readOnlyManagerInstance.refresh();
                }
                observerTimeout = null;
            }, 300);
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: false,
        characterData: false
    });
    
    window.__readonlyObserver = observer;
}