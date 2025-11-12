// Review Draft Manager
// Handles autosaving, restoring, and deleting review drafts

class ReviewDraftManager {
    constructor() {
        this.draftId = null;
        this.autosaveInterval = null;
        this.autosaveDelay = 30000; // 30 seconds
        this.hasUnsavedChanges = false;
        this.lastSaveTime = null;
    }

    /**
     * Initialize the draft manager
     * Check for existing drafts and offer restoration
     */
    async init() {
        try {
            const draft = await this.retrieveDraft();
            if (draft) {
                return this.offerDraftRestoration(draft);
            }
            return null;
        } catch (error) {
            console.error('Error initializing draft manager:', error);
            return null;
        }
    }

    /**
     * Retrieve the latest draft from the server
     */
    async retrieveDraft() {
        try {
            const response = await fetch('/api/reviews/draft/retrieve/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();

            if (data.success && data.draft) {
                this.draftId = data.draft.id;
                return data.draft;
            }

            return null;
        } catch (error) {
            console.error('Error retrieving draft:', error);
            return null;
        }
    }

    /**
     * Show a modal/dialog to ask user if they want to restore the draft
     */
    offerDraftRestoration(draft) {
        return new Promise((resolve) => {
            const message = `You have an unsaved draft from ${draft.age_display}. Would you like to resume it?`;

            // Create a simple confirmation dialog
            // In a real implementation, you might use a Bootstrap modal
            const shouldRestore = confirm(message);

            if (shouldRestore) {
                resolve(draft);
            } else {
                // User chose to discard, delete the draft
                this.deleteDraft(draft.id);
                resolve(null);
            }
        });
    }

    /**
     * Save draft to server
     * @param {string} step - Current step ID
     * @param {object} data - Form data to save
     */
    async saveDraft(step, data) {
        try {
            const response = await fetch('/api/reviews/draft/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    draft_id: this.draftId,
                    step: step,
                    data: data
                })
            });

            const result = await response.json();

            if (result.success) {
                this.draftId = result.draft_id;
                this.lastSaveTime = new Date();
                this.hasUnsavedChanges = false;
                console.log('Draft saved successfully at', this.lastSaveTime.toLocaleTimeString());
                return true;
            } else {
                console.error('Error saving draft:', result.error);
                return false;
            }
        } catch (error) {
            console.error('Error saving draft:', error);
            return false;
        }
    }

    /**
     * Delete draft from server
     * @param {string} draftId - Draft ID to delete (optional, uses current if not provided)
     */
    async deleteDraft(draftId = null) {
        const idToDelete = draftId || this.draftId;

        if (!idToDelete) {
            return true; // No draft to delete
        }

        try {
            const response = await fetch(`/api/reviews/draft/${idToDelete}/delete/`, {
                method: 'POST', // Using POST for compatibility
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            const result = await response.json();

            if (result.success) {
                this.draftId = null;
                this.hasUnsavedChanges = false;
                console.log('Draft deleted successfully');
                return true;
            } else {
                console.error('Error deleting draft:', result.error);
                return false;
            }
        } catch (error) {
            console.error('Error deleting draft:', error);
            return false;
        }
    }

    /**
     * Start autosave interval
     * Saves draft every 30 seconds if there are unsaved changes
     */
    startAutosave(getCurrentStep, getFormData) {
        // Clear any existing interval
        this.stopAutosave();

        this.autosaveInterval = setInterval(() => {
            if (this.hasUnsavedChanges) {
                const step = getCurrentStep();
                const data = getFormData();
                this.saveDraft(step, data);
            }
        }, this.autosaveDelay);

        console.log('Autosave started (every 30 seconds)');
    }

    /**
     * Stop autosave interval
     */
    stopAutosave() {
        if (this.autosaveInterval) {
            clearInterval(this.autosaveInterval);
            this.autosaveInterval = null;
            console.log('Autosave stopped');
        }
    }

    /**
     * Mark that there are unsaved changes
     */
    markUnsaved() {
        this.hasUnsavedChanges = true;
    }

    /**
     * Save draft immediately (called on step navigation, modal close, etc.)
     */
    async saveNow(step, data) {
        return await this.saveDraft(step, data);
    }

    /**
     * Get CSRF token from cookie
     */
    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Get the current draft ID
     */
    getDraftId() {
        return this.draftId;
    }

    /**
     * Check if there are unsaved changes
     */
    hasUnsaved() {
        return this.hasUnsavedChanges;
    }

    /**
     * Reset the draft manager (call after successful submission)
     */
    reset() {
        this.stopAutosave();
        this.draftId = null;
        this.hasUnsavedChanges = false;
        this.lastSaveTime = null;
    }
}
