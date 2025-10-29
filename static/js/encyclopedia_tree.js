/**
 * Encyclopedia Tree Navigator
 * Handles sidebar navigation, tree expansion/collapse, and state persistence
 */

(function() {
    'use strict';

    // Configuration
    const STORAGE_KEYS = {
        SIDEBAR_OPEN: 'encyclopedia_sidebar_open',
        EXPANDED_ENTRIES: 'encyclopedia_expanded_entries'
    };

    const MOBILE_BREAKPOINT = 768;

    // State management
    class TreeState {
        constructor() {
            this.expandedEntries = this.loadExpandedEntries();
            this.sidebarOpen = this.loadSidebarState();
        }

        loadExpandedEntries() {
            try {
                const stored = localStorage.getItem(STORAGE_KEYS.EXPANDED_ENTRIES);
                return stored ? new Set(JSON.parse(stored)) : new Set();
            } catch (e) {
                console.error('Failed to load expanded entries:', e);
                return new Set();
            }
        }

        saveExpandedEntries() {
            try {
                localStorage.setItem(
                    STORAGE_KEYS.EXPANDED_ENTRIES,
                    JSON.stringify([...this.expandedEntries])
                );
            } catch (e) {
                console.error('Failed to save expanded entries:', e);
            }
        }

        loadSidebarState() {
            try {
                const stored = localStorage.getItem(STORAGE_KEYS.SIDEBAR_OPEN);
                // Default to closed on mobile, open on desktop
                if (stored === null) {
                    return window.innerWidth >= MOBILE_BREAKPOINT;
                }
                return stored === 'true';
            } catch (e) {
                console.error('Failed to load sidebar state:', e);
                return window.innerWidth >= MOBILE_BREAKPOINT;
            }
        }

        saveSidebarState(isOpen) {
            this.sidebarOpen = isOpen;
            try {
                localStorage.setItem(STORAGE_KEYS.SIDEBAR_OPEN, isOpen.toString());
            } catch (e) {
                console.error('Failed to save sidebar state:', e);
            }
        }

        toggleEntry(entryId) {
            if (this.expandedEntries.has(entryId)) {
                this.expandedEntries.delete(entryId);
            } else {
                this.expandedEntries.add(entryId);
            }
            this.saveExpandedEntries();
        }

        isExpanded(entryId) {
            return this.expandedEntries.has(entryId);
        }

        expandEntry(entryId) {
            this.expandedEntries.add(entryId);
            this.saveExpandedEntries();
        }

        collapseEntry(entryId) {
            this.expandedEntries.delete(entryId);
            this.saveExpandedEntries();
        }

        expandAll(entryIds) {
            entryIds.forEach(id => this.expandedEntries.add(id));
            this.saveExpandedEntries();
        }

        collapseAll() {
            this.expandedEntries.clear();
            this.saveExpandedEntries();
        }
    }

    // Tree synchronization
    class TreeSync {
        constructor(state) {
            this.state = state;
        }

        // Toggle entry in both main tree and sidebar
        toggleEntry(entryId) {
            this.state.toggleEntry(entryId);
            const isExpanded = this.state.isExpanded(entryId);

            // Update main tree
            this.updateTreeNode(entryId, isExpanded, false);
            // Update sidebar tree
            this.updateTreeNode(entryId, isExpanded, true);
        }

        // Update a single tree node (main or sidebar)
        updateTreeNode(entryId, isExpanded, isSidebar) {
            const prefix = isSidebar ? 'sidebar-' : '';
            const childrenId = isSidebar ? `sidebar-children-${entryId}` : `children-${entryId}`;

            // Find the tree entry
            const selector = isSidebar
                ? `.sidebar-tree-entry[data-entry-id="${entryId}"]`
                : `.tree-entry[data-entry-id="${entryId}"]`;

            const treeEntry = document.querySelector(selector);
            if (!treeEntry) return;

            // Update aria-expanded
            treeEntry.setAttribute('aria-expanded', isExpanded.toString());

            // Update toggle button
            const toggleBtn = treeEntry.querySelector(
                isSidebar ? '.sidebar-tree-toggle' : '.tree-toggle'
            );
            if (toggleBtn) {
                const icon = toggleBtn.querySelector('i');
                if (icon) {
                    if (isExpanded) {
                        icon.classList.remove('bi-chevron-right');
                        icon.classList.add('bi-chevron-down');
                    } else {
                        icon.classList.remove('bi-chevron-down');
                        icon.classList.add('bi-chevron-right');
                    }
                }
                toggleBtn.setAttribute('aria-label',
                    isExpanded ? `Collapse ${treeEntry.textContent.trim()}` : `Expand ${treeEntry.textContent.trim()}`
                );
            }

            // Update children container
            const childrenContainer = document.getElementById(childrenId);
            if (childrenContainer) {
                if (isExpanded) {
                    childrenContainer.classList.remove('collapsed');
                } else {
                    childrenContainer.classList.add('collapsed');
                }
            }
        }

        // Restore state from localStorage
        restoreState() {
            this.state.expandedEntries.forEach(entryId => {
                this.updateTreeNode(entryId, true, false);
                this.updateTreeNode(entryId, true, true);
            });
        }

        // Expand all entries
        expandAll() {
            const allEntryIds = [];

            // Collect all entry IDs from main tree
            document.querySelectorAll('.tree-entry[data-entry-id]').forEach(entry => {
                const entryId = entry.getAttribute('data-entry-id');
                if (entryId) allEntryIds.push(entryId);
            });

            this.state.expandAll(allEntryIds);

            // Update both trees
            allEntryIds.forEach(entryId => {
                this.updateTreeNode(entryId, true, false);
                this.updateTreeNode(entryId, true, true);
            });
        }

        // Collapse all entries
        collapseAll() {
            this.state.collapseAll();

            // Update main tree
            document.querySelectorAll('.tree-entry[data-entry-id]').forEach(entry => {
                const entryId = entry.getAttribute('data-entry-id');
                if (entryId) {
                    this.updateTreeNode(entryId, false, false);
                }
            });

            // Update sidebar tree
            document.querySelectorAll('.sidebar-tree-entry[data-entry-id]').forEach(entry => {
                const entryId = entry.getAttribute('data-entry-id');
                if (entryId) {
                    this.updateTreeNode(entryId, false, true);
                }
            });
        }
    }

    // Sidebar management
    class SidebarManager {
        constructor(state) {
            this.state = state;
            this.sidebar = document.getElementById('encyclopedia-sidebar');
            this.toggleBtn = document.getElementById('sidebar-toggle-btn');
            this.closeBtn = document.getElementById('sidebar-close-btn');
            this.backdrop = document.getElementById('sidebar-backdrop');
            this.mainWrapper = document.querySelector('.encyclopedia-main-wrapper');
        }

        init() {
            if (!this.sidebar || !this.toggleBtn) return;

            // Set initial state
            this.setSidebarState(this.state.sidebarOpen, false);

            // Event listeners
            this.toggleBtn.addEventListener('click', () => this.toggle());

            if (this.closeBtn) {
                this.closeBtn.addEventListener('click', () => this.close());
            }

            if (this.backdrop) {
                this.backdrop.addEventListener('click', () => this.close());
            }

            // Handle window resize
            window.addEventListener('resize', () => this.handleResize());

            // Handle escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.isMobile() && this.state.sidebarOpen) {
                    this.close();
                }
            });
        }

        isMobile() {
            return window.innerWidth < MOBILE_BREAKPOINT;
        }

        toggle() {
            this.setSidebarState(!this.state.sidebarOpen, true);
        }

        open() {
            this.setSidebarState(true, true);
        }

        close() {
            this.setSidebarState(false, true);
        }

        setSidebarState(isOpen, animate = true) {
            if (!this.sidebar) return;

            this.state.saveSidebarState(isOpen);

            if (isOpen) {
                this.sidebar.classList.add('open');
                if (this.mainWrapper) {
                    this.mainWrapper.classList.add('sidebar-open');
                }
                if (this.backdrop && this.isMobile()) {
                    this.backdrop.classList.add('active');
                }
                this.toggleBtn.setAttribute('aria-expanded', 'true');

                // Focus trap for mobile
                if (this.isMobile()) {
                    this.sidebar.focus();
                }
            } else {
                this.sidebar.classList.remove('open');
                if (this.mainWrapper) {
                    this.mainWrapper.classList.remove('sidebar-open');
                }
                if (this.backdrop) {
                    this.backdrop.classList.remove('active');
                }
                this.toggleBtn.setAttribute('aria-expanded', 'false');
            }
        }

        handleResize() {
            // Auto-open sidebar on desktop if it was previously open
            if (!this.isMobile() && this.state.sidebarOpen) {
                this.setSidebarState(true, false);
            }
            // Auto-close sidebar on mobile
            else if (this.isMobile() && this.state.sidebarOpen) {
                this.setSidebarState(false, false);
            }
        }
    }

    // Current entry highlighting
    class CurrentEntryHighlighter {
        constructor() {
            this.currentSlug = this.getCurrentSlug();
        }

        getCurrentSlug() {
            // Try to get slug from URL path
            const path = window.location.pathname;
            const match = path.match(/\/encyclopedia\/([^\/]+)\/?$/);
            return match ? match[1] : null;
        }

        highlight() {
            if (!this.currentSlug) return;

            // Find and highlight current entry in sidebar
            const sidebarLinks = document.querySelectorAll('.sidebar-entry-link');
            sidebarLinks.forEach(link => {
                if (link.href.includes(`/encyclopedia/${this.currentSlug}`)) {
                    link.classList.add('current-entry');
                    link.setAttribute('aria-current', 'page');

                    // Expand parent entries to show current entry
                    this.expandParents(link);
                }
            });

            // Also highlight in main tree
            const mainLinks = document.querySelectorAll('.tree-entry-link');
            mainLinks.forEach(link => {
                if (link.href.includes(`/encyclopedia/${this.currentSlug}`)) {
                    link.classList.add('current-entry');
                    link.setAttribute('aria-current', 'page');
                }
            });
        }

        expandParents(link) {
            let currentElement = link.closest('.sidebar-tree-entry');

            while (currentElement) {
                const parent = currentElement.parentElement.closest('.sidebar-tree-entry');
                if (parent) {
                    const entryId = parent.getAttribute('data-entry-id');
                    if (entryId && window.treeSync) {
                        window.treeSync.state.expandEntry(entryId);
                        window.treeSync.updateTreeNode(entryId, true, true);
                        window.treeSync.updateTreeNode(entryId, true, false);
                    }
                }
                currentElement = parent;
            }
        }
    }

    // Initialize on DOM ready
    function init() {
        const state = new TreeState();
        const treeSync = new TreeSync(state);
        const sidebarManager = new SidebarManager(state);
        const highlighter = new CurrentEntryHighlighter();

        // Expose treeSync globally for current entry highlighting
        window.treeSync = treeSync;

        // Initialize sidebar
        sidebarManager.init();

        // Restore expanded state
        treeSync.restoreState();

        // Highlight current entry
        highlighter.highlight();

        // Event listeners for tree toggles in main tree
        document.querySelectorAll('.tree-toggle').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                const entryId = toggle.getAttribute('data-entry-id');
                if (entryId) {
                    treeSync.toggleEntry(entryId);
                }
            });
        });

        // Event listeners for tree toggles in sidebar
        document.querySelectorAll('.sidebar-tree-toggle').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                const entryId = toggle.getAttribute('data-entry-id');
                if (entryId) {
                    treeSync.toggleEntry(entryId);
                }
            });
        });

        // Expand all button
        const expandAllBtn = document.getElementById('expand-all-btn');
        if (expandAllBtn) {
            expandAllBtn.addEventListener('click', () => {
                treeSync.expandAll();
            });
        }

        // Collapse all button
        const collapseAllBtn = document.getElementById('collapse-all-btn');
        if (collapseAllBtn) {
            collapseAllBtn.addEventListener('click', () => {
                treeSync.collapseAll();
            });
        }

        // Close sidebar when clicking entry links on mobile
        document.querySelectorAll('.sidebar-entry-link').forEach(link => {
            link.addEventListener('click', () => {
                if (sidebarManager.isMobile()) {
                    sidebarManager.close();
                }
            });
        });
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
