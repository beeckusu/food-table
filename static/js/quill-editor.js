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
