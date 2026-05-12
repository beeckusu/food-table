from django.forms import Widget
from django.utils.html import format_html


class QuillWidget(Widget):
    """Rich text editor widget for Django admin using Quill.js."""

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        widget_id = attrs.get('id', 'id_' + name)
        container_id = widget_id + '_quill'
        value = value or ''

        return format_html(
            '<div id="{0}" style="min-height: 150px;"></div>'
            '<input type="hidden" name="{1}" id="{2}" value="{3}">'
            '<script>'
            '(function(){{'
            'function init(){{'
            'if(typeof initQuillEditor==="undefined"){{setTimeout(init,50);return;}}'
            'initQuillEditor(document.getElementById("{0}"),document.getElementById("{2}"));'
            '}}'
            'init();'
            '}})();'
            '</script>',
            container_id, name, widget_id, value,
        )

    class Media:
        css = {
            'all': ('https://cdn.quilljs.com/1.3.7/quill.snow.css',)
        }
        js = (
            'https://cdn.quilljs.com/1.3.7/quill.min.js',
            'js/quill-editor.js',
        )
