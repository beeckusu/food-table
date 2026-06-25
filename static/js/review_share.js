// Compose-and-share page: segmented source/shared/platform text, lens preview, debounced autosave.
(function () {
    const dataEl = document.getElementById('share-page-data');
    if (!dataEl) return;

    const pageData = JSON.parse(dataEl.textContent);
    const draft = pageData.share_draft;
    const PLATFORMS = ['instagram', 'google', 'yelp'];
    const SEGMENT_TYPES = ['shared', 'instagram', 'google', 'yelp'];
    const SAVE_URL = '/api/reviews/' + pageData.review_id + '/share-draft/';
    const AUTOSAVE_DELAY = 1500;

    const segmentsContainer = document.getElementById('shareSegments');
    const platformLabelEl = document.getElementById('sharePlatformLabel');
    const previewEl = document.getElementById('sharePreview');
    const statusEl = document.getElementById('shareSaveStatus');
    const tabButtons = document.querySelectorAll('.share-platform-tabs [data-platform]');
    const photoThumbs = document.querySelectorAll('.share-photo-thumb');

    function defaultSegments() {
        return pageData.seed_text ? [{ type: 'shared', text: pageData.seed_text }] : [];
    }

    const state = {
        segments: (draft && draft.segments) || defaultSegments(),
        platforms: {},
        activePlatform: 'instagram',
    };
    PLATFORMS.forEach(function (platform) {
        const saved = draft && draft.platforms && draft.platforms[platform];
        state.platforms[platform] = { image_ids: (saved && saved.image_ids) || [] };
    });

    function segmentLabel(type) {
        return type === 'shared' ? 'Shared' : type.charAt(0).toUpperCase() + type.slice(1);
    }

    function updatePhotoHighlights() {
        const activeIds = state.platforms[state.activePlatform].image_ids;
        photoThumbs.forEach(function (img) {
            const id = parseInt(img.dataset.imageId, 10);
            img.classList.toggle('selected', activeIds.indexOf(id) !== -1);
        });
    }

    function composedTextForPlatform(platform) {
        return state.segments
            .filter(function (seg) { return seg.type === 'shared' || seg.type === platform; })
            .map(function (seg) { return seg.text.trim(); })
            .filter(Boolean)
            .join('\n');
    }

    function renderPreview() {
        previewEl.textContent = composedTextForPlatform(state.activePlatform) || 'Nothing written yet.';
    }

    function getCsrfToken() {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? match[1] : '';
    }

    let saveTimer = null;
    function scheduleAutosave() {
        if (statusEl) statusEl.textContent = 'Editing…';
        clearTimeout(saveTimer);
        saveTimer = setTimeout(saveDraft, AUTOSAVE_DELAY);
    }

    function saveDraft() {
        if (statusEl) statusEl.textContent = 'Saving…';
        fetch(SAVE_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
            body: JSON.stringify({ segments: state.segments, platforms: state.platforms }),
        })
            .then(function (response) { return response.json(); })
            .then(function (data) {
                if (statusEl) statusEl.textContent = data.success ? 'Saved' : 'Save failed';
            })
            .catch(function () {
                if (statusEl) statusEl.textContent = 'Save failed';
            });
    }

    function renderSegments() {
        segmentsContainer.innerHTML = '';

        state.segments.forEach(function (segment, index) {
            const row = document.createElement('div');
            row.className = 'share-segment-row share-segment-type-' + segment.type + ' border rounded p-2 mb-2';

            const header = document.createElement('div');
            header.className = 'd-flex justify-content-between align-items-center mb-1';

            const select = document.createElement('select');
            select.className = 'form-select form-select-sm';
            select.style.width = 'auto';
            SEGMENT_TYPES.forEach(function (type) {
                const option = document.createElement('option');
                option.value = type;
                option.textContent = segmentLabel(type);
                if (type === segment.type) option.selected = true;
                select.appendChild(option);
            });
            select.addEventListener('change', function () {
                state.segments[index].type = select.value;
                renderSegments();
                renderPreview();
                scheduleAutosave();
            });

            const controls = document.createElement('div');
            controls.className = 'btn-group btn-group-sm';

            const upBtn = document.createElement('button');
            upBtn.type = 'button';
            upBtn.className = 'btn btn-outline-secondary';
            upBtn.title = 'Move up';
            upBtn.innerHTML = '<i class="bi bi-arrow-up"></i>';
            upBtn.disabled = index === 0;
            upBtn.addEventListener('click', function () {
                if (index === 0) return;
                const tmp = state.segments[index - 1];
                state.segments[index - 1] = state.segments[index];
                state.segments[index] = tmp;
                renderSegments();
                renderPreview();
                scheduleAutosave();
            });

            const downBtn = document.createElement('button');
            downBtn.type = 'button';
            downBtn.className = 'btn btn-outline-secondary';
            downBtn.title = 'Move down';
            downBtn.innerHTML = '<i class="bi bi-arrow-down"></i>';
            downBtn.disabled = index === state.segments.length - 1;
            downBtn.addEventListener('click', function () {
                if (index === state.segments.length - 1) return;
                const tmp = state.segments[index + 1];
                state.segments[index + 1] = state.segments[index];
                state.segments[index] = tmp;
                renderSegments();
                renderPreview();
                scheduleAutosave();
            });

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'btn btn-outline-danger';
            removeBtn.title = 'Remove';
            removeBtn.innerHTML = '<i class="bi bi-trash"></i>';
            removeBtn.addEventListener('click', function () {
                state.segments.splice(index, 1);
                renderSegments();
                renderPreview();
                scheduleAutosave();
            });

            controls.appendChild(upBtn);
            controls.appendChild(downBtn);
            controls.appendChild(removeBtn);

            header.appendChild(select);
            header.appendChild(controls);

            const textarea = document.createElement('textarea');
            textarea.className = 'form-control form-control-sm';
            textarea.rows = 2;
            textarea.placeholder = segment.type === 'shared'
                ? 'Shared text — included in every platform.'
                : segmentLabel(segment.type) + '-only text — interleaved here for this platform.';
            textarea.value = segment.text;
            textarea.addEventListener('input', function () {
                state.segments[index].text = textarea.value;
                renderPreview();
                scheduleAutosave();
            });

            row.appendChild(header);
            row.appendChild(textarea);
            segmentsContainer.appendChild(row);
        });
    }

    document.querySelectorAll('.share-add-segment-btn').forEach(function (btn) {
        btn.addEventListener('click', function (event) {
            event.preventDefault();
            state.segments.push({ type: btn.dataset.type, text: '' });
            renderSegments();
            renderPreview();
            scheduleAutosave();
        });
    });

    photoThumbs.forEach(function (img) {
        img.addEventListener('click', function () {
            const id = parseInt(img.dataset.imageId, 10);
            const ids = state.platforms[state.activePlatform].image_ids;
            const idx = ids.indexOf(id);
            if (idx === -1) {
                ids.push(id);
            } else {
                ids.splice(idx, 1);
            }
            updatePhotoHighlights();
            scheduleAutosave();
        });
    });

    document.querySelectorAll('.share-source-item').forEach(function (item) {
        item.addEventListener('click', function () {
            const text = item.dataset.sourceText || '';
            if (!text) return;
            state.segments.push({ type: 'shared', text: text });
            renderSegments();
            renderPreview();
            scheduleAutosave();
        });
    });

    tabButtons.forEach(function (btn) {
        btn.addEventListener('click', function () {
            tabButtons.forEach(function (b) { b.classList.remove('active'); });
            btn.classList.add('active');
            state.activePlatform = btn.dataset.platform;
            platformLabelEl.textContent = btn.textContent;
            updatePhotoHighlights();
            renderPreview();
        });
    });

    renderSegments();
    updatePhotoHighlights();
    renderPreview();
}());
