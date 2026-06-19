// Shared Quill rich text editor initializer.
// Called by review_modal.js (frontend forms) and by QuillWidget (admin inline scripts).
function initQuillEditor(container, hiddenInput, options) {
    options = options || {};

    var toolbarOptions = [
        ['bold', 'italic', 'underline'],
        ['blockquote'],
        [{ list: 'ordered' }, { list: 'bullet' }],
        ['link'],
        ['clean']
    ];

    var quill = new Quill(container, {
        theme: 'snow',
        modules: { toolbar: toolbarOptions },
        placeholder: options.placeholder || ''
    });

    if (hiddenInput.value) {
        quill.clipboard.dangerouslyPasteHTML(hiddenInput.value);
    }

    quill.on('text-change', function () {
        var text = quill.getText().trim();
        hiddenInput.value = text ? quill.root.innerHTML : '';
        if (options.onChange) {
            options.onChange();
        }
    });

    return quill;
}

// Populate a Quill editor from a raw stored field value that may be Quill-authored HTML
// or legacy plain text (mirrors the rtf() template filter's detection logic in
// content/templatetags/rtf_tags.py, so both stay in lockstep).
var RTF_HTML_RE = /<[a-zA-Z]/;

function setQuillContentFromRtf(quill, rawValue) {
    if (!rawValue) {
        quill.setContents([]);
        return;
    }
    if (RTF_HTML_RE.test(rawValue)) {
        quill.clipboard.dangerouslyPasteHTML(rawValue);
        return;
    }
    var html = rawValue.split('\n\n').map(function (para) {
        var escaped = para.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>');
        return '<p>' + escaped + '</p>';
    }).join('');
    quill.clipboard.dangerouslyPasteHTML(html);
}
