// Dish Image Upload JavaScript
// Handles uploading images to review dishes

document.addEventListener('DOMContentLoaded', function() {
    const modalElement = document.getElementById('dishImageUploadModal');
    if (!modalElement) return; // Modal not present (user not authenticated)

    const modal = new bootstrap.Modal(modalElement);
    const uploadForm = document.getElementById('dishImageUploadForm');
    const fileInput = document.getElementById('dishImageFile');
    const captionInput = document.getElementById('dishImageCaption');
    const altTextInput = document.getElementById('dishImageAltText');
    const imagePreviewContainer = document.getElementById('imagePreviewContainer');
    const imagePreview = document.getElementById('imagePreview');
    const uploadBtn = document.getElementById('uploadImageBtn');
    const uploadBtnText = document.getElementById('uploadBtnText');
    const uploadBtnSpinner = document.getElementById('uploadBtnSpinner');
    const uploadBtnLoading = document.getElementById('uploadBtnLoading');
    const uploadError = document.getElementById('uploadError');
    const uploadSuccess = document.getElementById('uploadSuccess');

    let currentDishId = null;

    // Open modal when "Upload Photo" button is clicked
    function attachUploadHandlers() {
        document.querySelectorAll('.upload-dish-image-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                currentDishId = this.dataset.dishId;
                resetForm();
                modal.show();
            });
        });
    }
    attachUploadHandlers();

    // File input change handler - show preview
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) {
            imagePreviewContainer.style.display = 'none';
            return;
        }

        // Validate file type
        const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            uploadError.textContent = 'Invalid file type. Please select a JPEG, PNG, GIF, or WebP image.';
            uploadError.style.display = 'block';
            fileInput.value = '';
            imagePreviewContainer.style.display = 'none';
            return;
        }

        // Validate file size (10MB max)
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            uploadError.textContent = 'File is too large. Maximum size is 10MB.';
            uploadError.style.display = 'block';
            fileInput.value = '';
            imagePreviewContainer.style.display = 'none';
            return;
        }

        // Clear any errors
        uploadError.style.display = 'none';

        // Show preview
        const reader = new FileReader();
        reader.onload = function(e) {
            imagePreview.src = e.target.result;
            imagePreviewContainer.style.display = 'block';
        };
        reader.readAsDataURL(file);
    });

    // Upload button click handler
    uploadBtn.addEventListener('click', function() {
        uploadImage();
    });

    // Reset form when modal is closed
    modalElement.addEventListener('hidden.bs.modal', function() {
        resetForm();
        currentDishId = null;
    });

    function resetForm() {
        uploadForm.reset();
        imagePreviewContainer.style.display = 'none';
        uploadError.style.display = 'none';
        uploadSuccess.style.display = 'none';
        imagePreview.src = '';
        uploadBtn.disabled = false;
        uploadBtnText.style.display = 'inline';
        uploadBtnSpinner.style.display = 'none';
        uploadBtnLoading.style.display = 'none';
    }

    function uploadImage() {
        // Validate file is selected
        const file = fileInput.files[0];
        if (!file) {
            uploadError.textContent = 'Please select an image file.';
            uploadError.style.display = 'block';
            return;
        }

        // Hide any previous messages
        uploadError.style.display = 'none';
        uploadSuccess.style.display = 'none';

        // Show loading state
        uploadBtn.disabled = true;
        uploadBtnText.style.display = 'none';
        uploadBtnSpinner.style.display = 'inline-block';
        uploadBtnLoading.style.display = 'inline';

        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                         getCookie('csrftoken');

        // Prepare form data
        const formData = new FormData();
        formData.append('image', file);
        formData.append('caption', captionInput.value.trim());
        formData.append('alt_text', altTextInput.value.trim());
        formData.append('order', 0); // Default order

        // Upload the image
        fetch(`/api/dishes/${currentDishId}/upload-image/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Reset button state
            uploadBtn.disabled = false;
            uploadBtnText.style.display = 'inline';
            uploadBtnSpinner.style.display = 'none';
            uploadBtnLoading.style.display = 'none';

            if (data.success) {
                // Show success message
                uploadSuccess.style.display = 'block';

                // Update the page to show the new image
                updateDishImages(currentDishId, data.image);

                // Show toast notification
                showToast('Success', 'Image uploaded successfully!', 'success');

                // Close modal after a short delay
                setTimeout(() => {
                    modal.hide();
                }, 1500);
            } else {
                uploadError.textContent = data.error || 'Failed to upload image.';
                uploadError.style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
            uploadBtn.disabled = false;
            uploadBtnText.style.display = 'inline';
            uploadBtnSpinner.style.display = 'none';
            uploadBtnLoading.style.display = 'none';
            uploadError.textContent = 'Failed to upload image. Please try again.';
            uploadError.style.display = 'block';
        });
    }

    function updateDishImages(dishId, imageData) {
        // Find the dish's image container
        const uploadBtn = document.querySelector(`.upload-dish-image-btn[data-dish-id="${dishId}"]`);
        if (!uploadBtn) return;

        // Find the dish's list item
        const listItem = uploadBtn.closest('.list-group-item');
        if (!listItem) return;

        // Find or create the images section
        let imagesSection = listItem.querySelector('.dish-images');
        if (!imagesSection) {
            // Create images section if it doesn't exist
            const h5 = listItem.querySelector('h5');
            if (!h5) return;

            imagesSection = document.createElement('div');
            imagesSection.className = 'dish-images mt-2';
            h5.insertAdjacentElement('afterend', imagesSection);
        }

        // Add the new image
        const imageDiv = document.createElement('div');
        imageDiv.className = 'd-inline-block me-2 mb-2';
        imageDiv.innerHTML = `
            <img src="${imageData.url}" alt="${imageData.alt_text || ''}"
                 class="img-thumbnail" style="max-width: 150px; max-height: 150px;">
            ${imageData.caption ? `<div class="small text-muted">${imageData.caption}</div>` : ''}
        `;
        imagesSection.appendChild(imageDiv);
    }

    function getCookie(name) {
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

    function showToast(title, message, type) {
        // Simple toast notification
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
        alertDiv.style.zIndex = '9999';
        alertDiv.innerHTML = `
            <strong>${title}:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);
        setTimeout(() => alertDiv.remove(), 5000);
    }
});
