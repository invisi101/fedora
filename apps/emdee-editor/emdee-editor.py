#!/usr/bin/env python3
"""EmDee Editor — A lightweight markdown editor and viewer."""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
gi.require_version('GtkSource', '4')

import json
import os
import re
import sys
from gi.repository import Gtk, WebKit2, Gio, GLib, Gdk, GtkSource

import markdown
from pygments.formatters import HtmlFormatter

RECENT_FILE = os.path.expanduser('~/.config/emdee-editor/recent.json')
THEME_CSS_FILE = os.path.expanduser('~/.config/omarchy/current/theme/emdee-viewer.css')

DARK_CSS = """
body {
    background: #1c1c22;
    color: #d4d4d8;
    font-family: system-ui, -apple-system, sans-serif;
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    line-height: 1.7;
}
h1, h2, h3, h4, h5, h6 { color: #e4e4e7; margin-top: 1.5em; }
h1 { border-bottom: 1px solid #3f3f46; padding-bottom: 0.3em; }
a { color: #60a5fa; }
code {
    background: #27272a;
    padding: 0.2em 0.4em;
    border-radius: 4px;
    font-size: 0.9em;
}
pre {
    background: #18181b;
    padding: 1rem;
    border-radius: 8px;
    overflow-x: auto;
    border: 1px solid #3f3f46;
}
pre code { background: none; padding: 0; font-size: 1rem; }
blockquote {
    border-left: 3px solid #60a5fa;
    margin-left: 0;
    padding-left: 1rem;
    color: #a1a1aa;
}
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #3f3f46; padding: 0.5rem; }
th { background: #27272a; }
hr { border: none; border-top: 1px solid #3f3f46; }
img { max-width: 100%; }
"""


def _load_css():
    try:
        with open(THEME_CSS_FILE, 'r') as f:
            return f.read()
    except (FileNotFoundError, PermissionError, OSError):
        return DARK_CSS


class EmDeeEditor(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id='com.neil.emdee-editor',
            flags=Gio.ApplicationFlags.HANDLES_OPEN
        )

    def do_startup(self):
        Gtk.Application.do_startup(self)
        settings = Gtk.Settings.get_default()
        if settings:
            settings.set_property('gtk-application-prefer-dark-theme', True)

    def do_activate(self):
        win = self.get_active_window()
        if not win:
            win = EmDeeWindow(application=self)
        win.present()

    def do_open(self, files, n_files, hint):
        win = self.get_active_window()
        if not win:
            win = EmDeeWindow(application=self)
        win.load_file(files[0].get_path())
        win.present()


class EmDeeWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(
            title='EmDee Editor',
            default_width=1200,
            default_height=700,
            **kwargs
        )

        self.css = _load_css()
        self.current_file = None
        self.file_monitor = None
        self.modified = False
        self.font_size = 1.0
        self._preview_timeout = None
        self._reload_timeout = None
        self._inhibit_external_reload = False

        self._build_header()
        self._build_ui()
        self._setup_shortcuts()
        self._show_welcome()
        self.show_all()
        self.toc_scroll.hide()
        self.editor_box.hide()

    # ── Header ──────────────────────────────────────────────────────

    def _build_header(self):
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.set_title('EmDee Editor')
        self.set_titlebar(header)
        self.header = header

        # Left buttons
        new_btn = Gtk.Button(label='New')
        new_btn.connect('clicked', lambda b: self._new_file())
        header.pack_start(new_btn)

        open_btn = Gtk.Button(label='Open')
        open_btn.connect('clicked', self._on_open_clicked)
        header.pack_start(open_btn)

        save_btn = Gtk.Button(label='Save')
        save_btn.connect('clicked', lambda b: self._save_file())
        header.pack_start(save_btn)

        recent_btn = Gtk.MenuButton(label='Recent')
        self.recent_popover = Gtk.Popover()
        recent_btn.set_popover(self.recent_popover)
        header.pack_start(recent_btn)
        self.recent_btn = recent_btn
        self._update_recent_menu()

        # Right buttons
        self.toc_btn = Gtk.ToggleButton(label='TOC')
        self.toc_btn.set_active(False)
        self.toc_btn.connect('toggled', self._on_toc_toggled)
        header.pack_end(self.toc_btn)

        zoom_out_btn = Gtk.Button(label='A\u2212')
        zoom_out_btn.connect('clicked', self._on_zoom_out)
        header.pack_end(zoom_out_btn)

        zoom_in_btn = Gtk.Button(label='A+')
        zoom_in_btn.connect('clicked', self._on_zoom_in)
        header.pack_end(zoom_in_btn)

        # View mode toggle
        view_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        view_box.get_style_context().add_class('linked')
        self.btn_split = Gtk.ToggleButton(label='Split')
        self.btn_edit = Gtk.ToggleButton(label='Edit')
        self.btn_preview = Gtk.ToggleButton(label='View')
        self.btn_preview.set_active(True)
        self._view_mode = 'preview'
        self.btn_split.connect('toggled', self._on_view_toggle, 'split')
        self.btn_edit.connect('toggled', self._on_view_toggle, 'edit')
        self.btn_preview.connect('toggled', self._on_view_toggle, 'preview')
        view_box.pack_start(self.btn_edit, False, False, 0)
        view_box.pack_start(self.btn_split, False, False, 0)
        view_box.pack_start(self.btn_preview, False, False, 0)
        header.pack_end(view_box)

    # ── Main UI ─────────────────────────────────────────────────────

    def _build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        # TOC sidebar
        self.toc_store = Gtk.TreeStore(str, str)
        self.toc_view = Gtk.TreeView(model=self.toc_store)
        self.toc_view.set_headers_visible(False)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('', renderer, text=0)
        self.toc_view.append_column(column)
        self.toc_view.connect('row-activated', self._on_toc_clicked)

        toc_scroll = Gtk.ScrolledWindow()
        toc_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        toc_scroll.set_size_request(200, -1)
        toc_scroll.add(self.toc_view)
        self.toc_scroll = toc_scroll
        main_box.pack_start(toc_scroll, False, False, 0)

        # Editor + Preview paned
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)

        # Editor pane
        editor_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._build_toolbar(editor_box)

        self.source_buffer = GtkSource.Buffer()
        lang_manager = GtkSource.LanguageManager.get_default()
        md_lang = lang_manager.get_language('markdown')
        if md_lang:
            self.source_buffer.set_language(md_lang)
        self.source_buffer.set_highlight_syntax(True)

        style_manager = GtkSource.StyleSchemeManager.get_default()
        scheme = style_manager.get_scheme('oblivion')
        if scheme:
            self.source_buffer.set_style_scheme(scheme)

        self.source_view = GtkSource.View(buffer=self.source_buffer)
        self.source_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.source_view.set_show_line_numbers(True)
        self.source_view.set_auto_indent(True)
        self.source_view.set_tab_width(4)
        self.source_view.set_insert_spaces_instead_of_tabs(True)
        self.source_view.set_monospace(True)

        editor_scroll = Gtk.ScrolledWindow()
        editor_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        editor_scroll.add(self.source_view)
        editor_box.pack_start(editor_scroll, True, True, 0)
        self.editor_box = editor_box

        # Preview pane
        self.webview = WebKit2.WebView()
        bg_hex = self._parse_bg_color(self.css)
        self.webview.set_background_color(bg_hex)

        self.paned.pack1(editor_box, resize=True, shrink=False)
        self.paned.pack2(self.webview, resize=True, shrink=False)

        main_box.pack_start(self.paned, True, True, 0)
        self.add(main_box)

        self._apply_gtk_theme(self.css)

        # Connect buffer change signal for live preview
        self.source_buffer.connect('changed', self._on_buffer_changed)

    def _build_toolbar(self, parent):
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        toolbar.set_margin_top(2)
        toolbar.set_margin_bottom(2)
        toolbar.set_margin_start(4)
        toolbar.set_margin_end(4)

        buttons = [
            ('B',   'Bold (Ctrl+B)',      self._fmt_bold),
            ('I',   'Italic (Ctrl+I)',    self._fmt_italic),
            ('H1',  'Heading 1',          lambda b: self._fmt_heading(1)),
            ('H2',  'Heading 2',          lambda b: self._fmt_heading(2)),
            ('H3',  'Heading 3',          lambda b: self._fmt_heading(3)),
            ('``',  'Inline code',        self._fmt_code),
            ('```', 'Code block',         self._fmt_code_block),
            ('[]',  'Link (Ctrl+K)',      self._fmt_link),
            ('\u2022',  'Bullet list',    self._fmt_bullet),
            ('1.',  'Numbered list',      self._fmt_numbered),
            ('>',   'Blockquote',         self._fmt_quote),
            ('---', 'Horizontal rule',    self._fmt_hr),
        ]

        for label, tooltip, callback in buttons:
            btn = Gtk.Button(label=label)
            btn.set_tooltip_text(tooltip)
            btn.connect('clicked', callback)
            toolbar.pack_start(btn, False, False, 0)

        parent.pack_start(toolbar, False, False, 0)
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        parent.pack_start(sep, False, False, 0)

    # ── Keyboard shortcuts ──────────────────────────────────────────

    def _setup_shortcuts(self):
        accel = Gtk.AccelGroup()
        self.add_accel_group(accel)

        shortcuts = [
            ('<Control>s', lambda *a: self._save_file()),
            ('<Control><Shift>s', lambda *a: self._save_file_as()),
            ('<Control>o', lambda *a: self._on_open_clicked(None)),
            ('<Control>n', lambda *a: self._new_file()),
            ('<Control>b', lambda *a: self._fmt_bold(None)),
            ('<Control>i', lambda *a: self._fmt_italic(None)),
            ('<Control>k', lambda *a: self._fmt_link(None)),
        ]
        for accel_str, callback in shortcuts:
            key, mods = Gtk.accelerator_parse(accel_str)
            accel.connect(key, mods, Gtk.AccelFlags.VISIBLE, callback)

    # ── View mode ───────────────────────────────────────────────────

    def _on_view_toggle(self, button, mode):
        if not button.get_active():
            return
        self._view_mode = mode
        for btn, m in [(self.btn_split, 'split'), (self.btn_edit, 'edit'), (self.btn_preview, 'preview')]:
            if m != mode:
                btn.handler_block_by_func(self._on_view_toggle)
                btn.set_active(False)
                btn.handler_unblock_by_func(self._on_view_toggle)

        if mode == 'split':
            self.editor_box.show()
            self.webview.show()
            w = self.paned.get_allocated_width()
            self.paned.set_position(w // 2)
        elif mode == 'edit':
            self.editor_box.show()
            self.webview.hide()
        elif mode == 'preview':
            self.editor_box.hide()
            self.webview.show()

    def _on_toc_toggled(self, button):
        if button.get_active():
            self.toc_scroll.show()
        else:
            self.toc_scroll.hide()

    # ── File operations ─────────────────────────────────────────────

    def _new_file(self):
        if self.modified and not self._confirm_discard():
            return
        self.current_file = None
        self.source_buffer.begin_not_undoable_action()
        self.source_buffer.set_text('')
        self.source_buffer.end_not_undoable_action()
        self.modified = False
        self._update_title()
        self._update_preview()

    def _on_open_clicked(self, button):
        if self.modified and not self._confirm_discard():
            return
        dialog = Gtk.FileChooserDialog(
            title='Open Markdown File',
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
        )
        md_filter = Gtk.FileFilter()
        md_filter.set_name('Markdown files')
        md_filter.add_pattern('*.md')
        dialog.add_filter(md_filter)
        all_filter = Gtk.FileFilter()
        all_filter.set_name('All files')
        all_filter.add_pattern('*')
        dialog.add_filter(all_filter)

        if dialog.run() == Gtk.ResponseType.OK:
            self.load_file(dialog.get_filename())
        dialog.destroy()

    def load_file(self, filepath):
        try:
            with open(filepath, 'r') as f:
                text = f.read()
        except (FileNotFoundError, PermissionError, OSError):
            return

        self.source_buffer.handler_block_by_func(self._on_buffer_changed)
        self.source_buffer.begin_not_undoable_action()
        self.source_buffer.set_text(text)
        self.source_buffer.end_not_undoable_action()
        self.source_buffer.handler_unblock_by_func(self._on_buffer_changed)

        self.current_file = filepath
        self.modified = False
        self._update_title()
        self._update_preview()
        self._save_recent(filepath)
        self._refresh_recent_popover()
        self._setup_file_monitor(filepath)

    def _save_file(self):
        if self.current_file:
            self._write_file(self.current_file)
        else:
            self._save_file_as()

    def _save_file_as(self):
        dialog = Gtk.FileChooserDialog(
            title='Save Markdown File',
            parent=self,
            action=Gtk.FileChooserAction.SAVE,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK,
        )
        dialog.set_do_overwrite_confirmation(True)
        md_filter = Gtk.FileFilter()
        md_filter.set_name('Markdown files')
        md_filter.add_pattern('*.md')
        dialog.add_filter(md_filter)
        all_filter = Gtk.FileFilter()
        all_filter.set_name('All files')
        all_filter.add_pattern('*')
        dialog.add_filter(all_filter)
        if self.current_file:
            dialog.set_filename(self.current_file)
        else:
            dialog.set_current_name('untitled.md')

        if dialog.run() == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            self._write_file(filepath)
            self.current_file = filepath
            self._update_title()
            self._save_recent(filepath)
            self._refresh_recent_popover()
            self._setup_file_monitor(filepath)
        dialog.destroy()

    def _write_file(self, filepath):
        start = self.source_buffer.get_start_iter()
        end = self.source_buffer.get_end_iter()
        text = self.source_buffer.get_text(start, end, True)
        self._inhibit_external_reload = True
        try:
            with open(filepath, 'w') as f:
                f.write(text)
        except (PermissionError, OSError) as e:
            self._inhibit_external_reload = False
            dialog = Gtk.MessageDialog(
                parent=self, flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=f'Could not save file:\n{e}'
            )
            dialog.run()
            dialog.destroy()
            return
        self.modified = False
        self._update_title()
        GLib.timeout_add(500, self._clear_inhibit)

    def _clear_inhibit(self):
        self._inhibit_external_reload = False
        return False

    def _confirm_discard(self):
        dialog = Gtk.MessageDialog(
            parent=self, flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE,
            text='You have unsaved changes. Discard them?'
        )
        dialog.add_buttons(
            'Cancel', Gtk.ResponseType.CANCEL,
            'Discard', Gtk.ResponseType.OK,
        )
        result = dialog.run()
        dialog.destroy()
        return result == Gtk.ResponseType.OK

    # ── Title management ────────────────────────────────────────────

    def _update_title(self):
        if self.current_file:
            name = GLib.path_get_basename(self.current_file)
        else:
            name = 'Untitled'
        if self.modified:
            name = '\u2022 ' + name
        self.header.set_subtitle(name)

    # ── Live preview ────────────────────────────────────────────────

    def _on_buffer_changed(self, buf):
        if not self.modified:
            self.modified = True
            self._update_title()
        if self._preview_timeout:
            GLib.source_remove(self._preview_timeout)
        self._preview_timeout = GLib.timeout_add(300, self._do_preview_update)

    def _do_preview_update(self):
        self._preview_timeout = None
        self._update_preview()
        return False

    def _update_preview(self):
        start = self.source_buffer.get_start_iter()
        end = self.source_buffer.get_end_iter()
        md_text = self.source_buffer.get_text(start, end, True)

        if not md_text.strip():
            self._show_welcome()
            self.toc_store.clear()
            return

        pygments_css = HtmlFormatter(style='monokai').get_style_defs('.codehilite')
        md = markdown.Markdown(extensions=[
            'fenced_code', 'codehilite', 'tables', 'toc',
        ], extension_configs={
            'codehilite': {'css_class': 'codehilite', 'guess_lang': True},
            'toc': {'permalink': False},
        })
        html_body = md.convert(md_text)

        scroll_js = """
        <script>
        (function() {
            var scrollPos = sessionStorage.getItem('scrollPos');
            window.addEventListener('load', function() {
                if (scrollPos) window.scrollTo(0, parseInt(scrollPos));
            });
            window.addEventListener('beforeunload', function() {
                sessionStorage.setItem('scrollPos', window.scrollY);
            });
        })();
        </script>
        """

        html = f"""<!DOCTYPE html>
<html><head>
<style>{self.css}\n{pygments_css}</style>
{scroll_js}
</head><body>{html_body}</body></html>"""

        base_uri = 'file:///'
        if self.current_file:
            base_uri = GLib.filename_to_uri(os.path.dirname(self.current_file), None) + '/'

        self.webview.load_html(html, base_uri)
        self.webview.connect('load-changed', self._on_load_finished)

        self.toc_store.clear()
        self._populate_toc(md.toc_tokens, None)
        self.toc_view.expand_all()

    def _on_load_finished(self, webview, event):
        if event == WebKit2.LoadEvent.FINISHED:
            self._apply_font_size()
            webview.disconnect_by_func(self._on_load_finished)

    def _show_welcome(self):
        welcome = f"""<!DOCTYPE html><html><head><style>
{self.css}
body {{ display: flex; align-items: center; justify-content: center; height: 90vh; }}
.msg {{ text-align: center; }}
h1 {{ font-size: 1.5rem; }}
p {{ font-size: 1rem; }}
</style></head><body><div class="msg">
<h1>EmDee Editor</h1>
<p>Click <b>New</b> or <b>Open</b> to get started</p>
</div></body></html>"""
        self.webview.load_html(welcome, 'file:///')

    # ── Formatting commands ─────────────────────────────────────────

    def _wrap_selection(self, prefix, suffix=None):
        if suffix is None:
            suffix = prefix
        buf = self.source_buffer
        if buf.get_has_selection():
            start, end = buf.get_selection_bounds()
            text = buf.get_text(start, end, True)
            buf.begin_user_action()
            buf.delete(start, end)
            buf.insert_at_cursor(f'{prefix}{text}{suffix}')
            buf.end_user_action()
        else:
            buf.begin_user_action()
            buf.insert_at_cursor(f'{prefix}{suffix}')
            buf.end_user_action()
            cursor = buf.get_iter_at_mark(buf.get_insert())
            cursor.backward_chars(len(suffix))
            buf.place_cursor(cursor)

    def _prefix_line(self, prefix):
        buf = self.source_buffer
        if buf.get_has_selection():
            start, end = buf.get_selection_bounds()
        else:
            start = buf.get_iter_at_mark(buf.get_insert())
            end = start.copy()
        start.set_line_offset(0)
        if not end.ends_line():
            end.forward_to_line_end()
        text = buf.get_text(start, end, True)
        lines = text.split('\n')
        new_lines = [prefix + line for line in lines]
        buf.begin_user_action()
        buf.delete(start, end)
        buf.insert(start, '\n'.join(new_lines))
        buf.end_user_action()

    def _fmt_bold(self, button):
        self._wrap_selection('**')

    def _fmt_italic(self, button):
        self._wrap_selection('*')

    def _fmt_heading(self, level):
        prefix = '#' * level + ' '
        buf = self.source_buffer
        cursor = buf.get_iter_at_mark(buf.get_insert())
        cursor.set_line_offset(0)
        line_end = cursor.copy()
        if not line_end.ends_line():
            line_end.forward_to_line_end()
        line_text = buf.get_text(cursor, line_end, True)
        stripped = re.sub(r'^#+\s*', '', line_text)
        buf.begin_user_action()
        buf.delete(cursor, line_end)
        buf.insert(cursor, prefix + stripped)
        buf.end_user_action()

    def _fmt_code(self, button):
        self._wrap_selection('`')

    def _fmt_code_block(self, button):
        self._wrap_selection('```\n', '\n```')

    def _fmt_link(self, button):
        buf = self.source_buffer
        if buf.get_has_selection():
            start, end = buf.get_selection_bounds()
            text = buf.get_text(start, end, True)
            buf.begin_user_action()
            buf.delete(start, end)
            buf.insert_at_cursor(f'[{text}](url)')
            buf.end_user_action()
        else:
            buf.begin_user_action()
            buf.insert_at_cursor('[text](url)')
            buf.end_user_action()

    def _fmt_bullet(self, button):
        self._prefix_line('- ')

    def _fmt_numbered(self, button):
        buf = self.source_buffer
        if buf.get_has_selection():
            start, end = buf.get_selection_bounds()
        else:
            start = buf.get_iter_at_mark(buf.get_insert())
            end = start.copy()
        start.set_line_offset(0)
        if not end.ends_line():
            end.forward_to_line_end()
        text = buf.get_text(start, end, True)
        lines = text.split('\n')
        new_lines = [f'{i+1}. {line}' for i, line in enumerate(lines)]
        buf.begin_user_action()
        buf.delete(start, end)
        buf.insert(start, '\n'.join(new_lines))
        buf.end_user_action()

    def _fmt_quote(self, button):
        self._prefix_line('> ')

    def _fmt_hr(self, button):
        buf = self.source_buffer
        buf.begin_user_action()
        buf.insert_at_cursor('\n---\n')
        buf.end_user_action()

    # ── Font size ───────────────────────────────────────────────────

    def _apply_font_size(self):
        js = f"document.body.style.fontSize='{self.font_size:.1f}rem';"
        self.webview.run_javascript(js, None, None, None)

    def _on_zoom_in(self, button):
        self.font_size = min(self.font_size + 0.1, 3.0)
        self._apply_font_size()

    def _on_zoom_out(self, button):
        self.font_size = max(self.font_size - 0.1, 0.5)
        self._apply_font_size()

    # ── TOC ─────────────────────────────────────────────────────────

    def _populate_toc(self, tokens, parent):
        for token in tokens:
            row = self.toc_store.append(parent, [token['name'], token['id']])
            if token.get('children'):
                self._populate_toc(token['children'], row)

    def _on_toc_clicked(self, treeview, path, column):
        model = treeview.get_model()
        iter_ = model.get_iter(path)
        anchor = model.get_value(iter_, 1)
        js = f"document.getElementById('{anchor}').scrollIntoView({{behavior:'smooth'}});"
        self.webview.run_javascript(js, None, None, None)

    # ── File monitor ────────────────────────────────────────────────

    def _setup_file_monitor(self, filepath):
        if self.file_monitor:
            self.file_monitor.cancel()
        gfile = Gio.File.new_for_path(filepath)
        self.file_monitor = gfile.monitor_file(Gio.FileMonitorFlags.NONE, None)
        self.file_monitor.connect('changed', self._on_file_changed)

    def _on_file_changed(self, monitor, file, other_file, event):
        if self._inhibit_external_reload:
            return
        if event == Gio.FileMonitorEvent.CHANGES_DONE_HINT:
            if self._reload_timeout:
                GLib.source_remove(self._reload_timeout)
            self._reload_timeout = GLib.timeout_add(300, self._do_external_reload)

    def _do_external_reload(self):
        self._reload_timeout = None
        if not self.current_file:
            return False
        try:
            with open(self.current_file, 'r') as f:
                text = f.read()
        except (FileNotFoundError, PermissionError, OSError):
            return False
        start = self.source_buffer.get_start_iter()
        end = self.source_buffer.get_end_iter()
        current = self.source_buffer.get_text(start, end, True)
        if text != current:
            self.source_buffer.handler_block_by_func(self._on_buffer_changed)
            self.source_buffer.begin_not_undoable_action()
            self.source_buffer.set_text(text)
            self.source_buffer.end_not_undoable_action()
            self.source_buffer.handler_unblock_by_func(self._on_buffer_changed)
            self.modified = False
            self._update_title()
            self._update_preview()
        return False

    # ── Recent files ────────────────────────────────────────────────

    def _load_recent(self):
        try:
            with open(RECENT_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_recent(self, filepath):
        os.makedirs(os.path.dirname(RECENT_FILE), exist_ok=True)
        recent = self._load_recent()
        if filepath in recent:
            recent.remove(filepath)
        recent.insert(0, filepath)
        recent = recent[:10]
        with open(RECENT_FILE, 'w') as f:
            json.dump(recent, f)

    def _refresh_recent_popover(self):
        child = self.recent_popover.get_child()
        if child:
            self.recent_popover.remove(child)
        self._update_recent_menu()

    def _update_recent_menu(self):
        recent = self._load_recent()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(8)
        box.set_margin_end(8)

        if not recent:
            label = Gtk.Label(label='No recent files')
            box.pack_start(label, False, False, 0)
        else:
            for filepath in recent:
                btn = Gtk.ModelButton(label=GLib.path_get_basename(filepath))
                btn.connect('clicked', lambda b, p=filepath: self._open_recent(p))
                box.pack_start(btn, False, False, 0)

        box.show_all()
        self.recent_popover.add(box)

    def _open_recent(self, filepath):
        self.recent_popover.popdown()
        if os.path.exists(filepath):
            if self.modified and not self._confirm_discard():
                return
            self.load_file(filepath)

    # ── Theme helpers ───────────────────────────────────────────────

    @staticmethod
    def _parse_bg_color(css):
        match = re.search(r'background:\s*(#[0-9a-fA-F]{6})', css)
        if match:
            h = match.group(1)
            r, g, b = int(h[1:3], 16) / 255, int(h[3:5], 16) / 255, int(h[5:7], 16) / 255
            return Gdk.RGBA(r, g, b, 1.0)
        return Gdk.RGBA(0.11, 0.11, 0.14, 1.0)

    def _apply_gtk_theme(self, css):
        bg = re.search(r'background:\s*(#[0-9a-fA-F]{6})', css)
        fg = re.search(r'color:\s*(#[0-9a-fA-F]{6})', css)
        accent = re.search(r'a \{ color:\s*(#[0-9a-fA-F]{6})', css)
        bg_color = bg.group(1) if bg else '#1c1c22'
        fg_color = fg.group(1) if fg else '#d4d4d8'
        accent_color = accent.group(1) if accent else '#60a5fa'
        gtk_css = f"""
            treeview {{
                background-color: {bg_color};
                color: {fg_color};
            }}
            treeview:selected {{
                background-color: {accent_color};
                color: {bg_color};
            }}
            scrolledwindow {{
                background-color: {bg_color};
            }}
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(gtk_css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    # ── Window close ────────────────────────────────────────────────

    def do_delete_event(self, event):
        if self.modified:
            return not self._confirm_discard()
        return False


app = EmDeeEditor()
app.run(sys.argv)
