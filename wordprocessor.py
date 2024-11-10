try:
    import PySide6
except:
    PySide6 = None

if PySide6:
    from PySide6.QtGui import (
        QFont,
        QIcon,
        QImage,
        QKeySequence,
        QAction,
        QActionGroup,
        QTextDocument,
        QPixmap,
    )
    from PySide6.QtWidgets import (
        QPushButton,
        QToolTip,
        QTableWidgetItem,
        QTableWidget,
        QLabel,
        QTextEdit,
        QMainWindow,
        QVBoxLayout,
        QHBoxLayout,
        QWidget,
        QStatusBar,
        QToolBar,
        QFileDialog,
        QMessageBox,
        QFontComboBox,
        QComboBox,
        QApplication,
    )
    from PySide6.QtCore import QSize, Qt, QUrl, QTimer
    from PySide6.QtPrintSupport import QPrintDialog
else:
    from PyQt6.QtGui import (
        QFont,
        QIcon,
        QImage,
        QKeySequence,
        QAction,
        QActionGroup,
        QTextDocument,
        QPixmap,
    )
    from PyQt6.QtWidgets import (
        QPushButton,
        QToolTip,
        QTableWidgetItem,
        QTableWidget,
        QLabel,
        QTextEdit,
        QMainWindow,
        QVBoxLayout,
        QHBoxLayout,
        QWidget,
        QStatusBar,
        QToolBar,
        QFileDialog,
        QMessageBox,
        QFontComboBox,
        QComboBox,
        QApplication,
    )
    from PyQt6.QtCore import QSize, Qt, QUrl, QTimer
    from PyQt6.QtPrintSupport import QPrintDialog

import os, sys, uuid, xml.dom.minidom, subprocess

FONT_SIZES = [7, 8, 9, 10, 11, 12, 13, 14, 18, 24, 36, 48, 64, 72, 96, 144, 288]
IMAGE_EXTENSIONS = [".jpg", ".png", ".bmp"]
HTML_EXTENSIONS = [".htm", ".html"]
ADD_SEPARATOR = "addSeparator"

def hex_uuid():
    return uuid.uuid4().hex


def splitext(p):
    return os.path.splitext(p)[1].lower()


class TextEdit(QTextEdit):
    def mouseMoveEvent(self, event):
        text_cursor = self.cursorForPosition(event.pos())
        text_position = text_cursor.position()
        self.mouse_over_anchor=self.mouse_over_symbol=None
        if text_position:
            self.mouse_over_anchor = self.anchorAt(event.pos())
            txt = self.toPlainText()
            if text_position < len(txt):
                self.mouse_over_symbol = self.toPlainText()[text_position]
                if self.mouse_over_anchor and hasattr(self, 'on_mouse_over_anchor'):
                    self.on_mouse_over_anchor(event, self.mouse_over_anchor, self.mouse_over_symbol)
        super(TextEdit,self).mouseMoveEvent(event)

    def mousePressEvent(self, e):
        self.anchor = self.anchorAt(e.pos())
        super(TextEdit,self).mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        if self.anchor:
            if hasattr(self, 'on_link_clicked'):
                self.on_link_clicked(self.anchor)
            else:
                print('clicked anchor href:', self.anchor)
                webbrowser.open(self.anchor)
            self.anchor = None
        super(TextEdit,self).mouseReleaseEvent(e)

    def canInsertFromMimeData(self, source):
        if source.hasImage():
            return True
        else:
            return super(TextEdit, self).canInsertFromMimeData(source)

    def insertFromMimeData(self, source):
        cursor = self.textCursor()
        document = self.document()
        if source.hasHtml():
            html = source.html()
            print(html.encode('utf-8'))
            if html.endswith('\x00'):
                html = html[:-1]
                source.setHtml(html)
            if self.allow_inline_tables:
                cursor.insertHtml(html)
            else:
                doc = xml.dom.minidom.parseString(html)
                tables = doc.getElementsByTagName('table')
                if len(tables):
                    for tab in tables:
                        cursor.insertHtml('<a href="%s" style="color:blue">▦</a>' % len(self.tables))
                        if hasattr(self, 'on_new_table'):
                            self.tables.append(self.on_new_table(tab))
                        else:
                            self.tables.append(tab)

                else:
                    cursor.insertHtml(html)

            return

        elif source.hasUrls():
            for u in source.urls():
                file_ext = splitext(str(u.toLocalFile()))
                if u.isLocalFile() and file_ext in IMAGE_EXTENSIONS:
                    image = QImage(u.toLocalFile())
                    document.addResource(QTextDocument.ResourceType.ImageResource, u, image)
                    cursor.insertImage(u.toLocalFile())
                elif hasattr(self, 'extra_mime_types') and file_ext in self.extra_mime_types:
                    self.extra_mime_types[file_ext]( u.toLocalFile(), document, cursor )
                    return
                else:
                    # If we hit a non-image or non-local URL break the loop and fall out
                    # to the super call & let Qt handle it
                    break

            else:
                # If all were valid images, finish here.
                return

        elif source.hasImage():
            image = source.imageData()
            uu_id = hex_uuid()
            document.addResource(
                QTextDocument.ResourceType.ImageResource, QUrl(uu_id), image
            )
            cursor.insertImage(uu_id)
            return

        super(TextEdit, self).insertFromMimeData(source)


class MegasolidEditor(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MegasolidEditor, self).__init__(*args, **kwargs)
        self.left_widget = None
        self.right_widget = None
        self.alt_widget = None

    def reset(self, x=100, y=100, width=840, height=600, use_icons=True, use_menu=True, use_monospace=True, allow_inline_tables=True):
        self.setGeometry(x, y, width, height)
        layout = QHBoxLayout()
        self.editor = TextEdit()
        self.editor.allow_inline_tables=allow_inline_tables
        # Set up the QTextEdit editor configuration
        self.editor.setAutoFormatting(QTextEdit.AutoFormattingFlag.AutoAll)
        self.editor.selectionChanged.connect(self.update_format)
        # Initialize default font size.
        if use_monospace:
            font = QFont("Monospace", 12)
            self.editor.setFont(font)
        else:
            font = QFont("Times New Roman", 12)
            self.editor.setFont(font)

        # We need to repeat the size to init the current format.
        self.editor.setFontPointSize(12)
        # self.path holds the path of the currently open file.
        # If none, we haven't got a file open yet (or creating new).
        self.path = None
        if self.left_widget:
            layout.addWidget(self.left_widget)
        layout.addWidget(self.editor, stretch=1)
        if self.right_widget:
            layout.addWidget(self.right_widget)
        if self.alt_widget:
            layout.addWidget(self.alt_widget)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # Uncomment to disable native menubar on Mac
        # self.menuBar().setNativeMenuBar(False)

        menu_actions = [
            {
                "name": "File",
                "menu": "&File",
                "actions": [
                    {
                        "status tip": "Open File",
                        "menu name": "Open file...",
                        "icon": "blue-folder-open-document.png",
                        "symbol":"🗁",
                        "trigger": self.file_open,
                    },
                    {
                        "status tip": "Save File",
                        "menu name": "Save",
                        "icon": "disk.png",
                        "symbol":"🖪",
                        "trigger": self.file_save,
                    },
                    {
                        "status tip": "Save current page to specified file",
                        "menu name": "Save As...",
                        "icon": "disk--pencil.png",
                        "symbol":"🖫",
                        "trigger": self.file_save_as,
                    },
                    {
                        "status tip": "Print current page",
                        "menu name": "Print...",
                        "icon": "printer.png",
                        "symbol":"🖶",
                        "trigger": self.file_print,
                    },
                ],
            },
            {
                "name": "Edit",
                "menu": "&Edit",
                "actions": [
                    {
                        "status tip": "Undo last change",
                        "menu name": "Undo",
                        "icon": "arrow-curve-180-left.png",
                        "symbol":"⤺",
                        "trigger": self.editor.undo,
                    },
                    {
                        "status tip": "Redo last change",
                        "menu name": "Redo",
                        "icon": "arrow-curve.png",
                        "symbol":"⤻",
                        "trigger": self.editor.redo,
                    },
                    ADD_SEPARATOR,
                    {
                        "status tip": "Cut selected text",
                        "menu name": "Cut",
                        "icon": "scissors.png",
                        "symbol":"✂",
                        "trigger": self.editor.cut,
                        "shortcut": QKeySequence.StandardKey.Cut,
                    },
                    {
                        "status tip": "Copy selected text",
                        "menu name": "Copy",
                        "icon": "document-copy.png",
                        "symbol":"🗈",
                        "trigger": self.editor.copy,
                        "shortcut": QKeySequence.StandardKey.Copy,
                    },
                    {
                        "status tip": "Paste from clipboard",
                        "menu name": "Paste",
                        "icon": "clipboard-paste-document-text.png",
                        "symbol":"🗉",
                        "trigger": self.editor.paste,
                        "shortcut": QKeySequence.StandardKey.Paste,
                    },
                    {
                        "status tip": "Select all text",
                        "menu name": "Select all",
                        "icon": "selection-input.png",
                        "symbol":"🗏",
                        "trigger": self.editor.selectAll,
                        "shortcut": QKeySequence.StandardKey.SelectAll,
                    },
                    ADD_SEPARATOR,
                    {
                        "status tip": "Toggle wrap text to window",
                        "menu name": "Wrap text to window",
                        "icon": "arrow-continue.png",
                        "symbol":"🗞",
                        "trigger": self.edit_toggle_wrap,
                    },
                ],
            },
        ]
        for menu_action in menu_actions:
            toolbar = QToolBar(menu_action["name"])
            toolbar.setIconSize(QSize(16, 16))
            self.addToolBar(toolbar)
            if use_menu:
                menu = self.menuBar().addMenu(menu_action["menu"])

            for action in menu_action["actions"]:
                if ADD_SEPARATOR == action:
                    if use_menu:
                        menu.addSeparator()
                    continue

                if use_icons:
                    this_action = QAction(
                        QIcon(os.path.join("icons", action["icon"])),
                        action["menu name"],
                        self,
                    )
                else:
                    if 'symbol' in action:
                        this_action = QAction(action["symbol"],self)
                    else:
                        this_action = QAction(action["menu name"],self)
                    this_action.setToolTip(action["status tip"])

                this_action.setStatusTip(action["status tip"])
                this_action.triggered.connect(action["trigger"])
                if use_menu:
                    menu.addAction(this_action)
                toolbar.addAction(this_action)

        # Sadly, these are not regular enough to add to the menu_actions list.
        self.format_toolbar = format_toolbar = QToolBar("Format")
        format_toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(format_toolbar)
        if use_menu:
            format_menu = self.menuBar().addMenu("&Format")

        # We need references to these actions/settings to update as selection changes, so attach to self.
        self.fonts = QFontComboBox()
        self.fonts.currentFontChanged.connect(self.editor.setCurrentFont)
        format_toolbar.addWidget(self.fonts)

        self.font_size = QComboBox()
        self.font_size.addItems([str(s) for s in FONT_SIZES])

        # Connect to the signal producing the text of the current selection.
        self.font_size.currentIndexChanged.connect(
            lambda s: self.editor.setFontPointSize(FONT_SIZES[s])
        )
        format_toolbar.addWidget(self.font_size)

        if use_icons:
            self.bold_action = QAction(
                QIcon(os.path.join("icons", "edit-bold.png")), "Bold", self
            )
        else:
            self.bold_action = act = QAction("𝐁", self)
            act.setToolTip("Bold")

        self.bold_action.setStatusTip("Bold")
        self.bold_action.setShortcut(QKeySequence.StandardKey.Bold)
        self.bold_action.setCheckable(True)
        self.bold_action.toggled.connect(
            lambda x: self.editor.setFontWeight(
                QFont.Weight.Bold if x else QFont.Weight.Normal
            )
        )
        format_toolbar.addAction(self.bold_action)
        if use_menu:
            format_menu.addAction(self.bold_action)

        if use_icons:
            self.italic_action = QAction(
                QIcon(os.path.join("icons", "edit-italic.png")), "Italic", self
            )
        else:
            self.italic_action = act = QAction("𝒊", self)
            act.setToolTip('Italic')

        self.italic_action.setStatusTip("Italic")
        self.italic_action.setShortcut(QKeySequence.StandardKey.Italic)
        self.italic_action.setCheckable(True)
        self.italic_action.toggled.connect(self.editor.setFontItalic)
        format_toolbar.addAction(self.italic_action)
        if use_menu:
            format_menu.addAction(self.italic_action)

        if use_icons:
            self.underline_action = QAction(
                QIcon(os.path.join("icons", "edit-underline.png")), "Underline", self
            )
        else:
            self.underline_action = act = QAction("⎁", self)
            act.setToolTip("Underline")

        self.underline_action.setStatusTip("Underline")
        self.underline_action.setShortcut(QKeySequence.StandardKey.Underline)
        self.underline_action.setCheckable(True)
        self.underline_action.toggled.connect(self.editor.setFontUnderline)
        format_toolbar.addAction(self.underline_action)
        if use_menu:
            format_menu.addAction(self.underline_action)
            format_menu.addSeparator()

        if use_icons:
            self.align_left_action = QAction(
                QIcon(os.path.join("icons", "edit-alignment.png")), "Align left", self
            )
        else:
            self.align_left_action = act = QAction("«", self)
            act.setToolTip("Align left")

        self.align_left_action.setStatusTip("Align text left")
        self.align_left_action.setCheckable(True)
        self.align_left_action.triggered.connect(
            lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignLeft)
        )
        format_toolbar.addAction(self.align_left_action)
        if use_menu:
            format_menu.addAction(self.align_left_action)

        if use_icons:
            self.align_center_action = QAction(
                QIcon(os.path.join("icons", "edit-alignment-center.png")),
                "Align center",
                self,
            )
        else:
            self.align_center_action = act = QAction("⟺",self)
            act.setToolTip("Align center")

        self.align_center_action.setStatusTip("Align text center")
        self.align_center_action.setCheckable(True)
        self.align_center_action.triggered.connect(
            lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        )
        format_toolbar.addAction(self.align_center_action)
        if use_menu:
            format_menu.addAction(self.align_center_action)

        if use_icons:
            self.alignr_action = QAction(
                QIcon(os.path.join("icons", "edit-alignment-right.png")),
                "Align right",
                self,
            )
        else:
            self.alignr_action = act = QAction("»",self)
            act.setToolTip("Align right")

        self.alignr_action.setStatusTip("Align text right")
        self.alignr_action.setCheckable(True)
        self.alignr_action.triggered.connect(
            lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignRight)
        )
        format_toolbar.addAction(self.alignr_action)
        if use_menu:
            format_menu.addAction(self.alignr_action)

        if use_icons:
            self.align_justify_action = QAction(
                QIcon(os.path.join("icons", "edit-alignment-justify.png")), "Justify", self
            )
        else:
            self.align_justify_action = act = QAction("𝄘", self)
            act.setToolTip("Justify")

        self.align_justify_action.setStatusTip("Justify text")
        self.align_justify_action.setCheckable(True)
        self.align_justify_action.triggered.connect(
            lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignJustify)
        )
        format_toolbar.addAction(self.align_justify_action)
        if use_menu:
            format_menu.addAction(self.align_justify_action)

        format_group = QActionGroup(self)
        format_group.setExclusive(True)
        format_group.addAction(self.align_left_action)
        format_group.addAction(self.align_center_action)
        format_group.addAction(self.alignr_action)
        format_group.addAction(self.align_justify_action)
        if use_menu:
            format_menu.addSeparator()

        # A list of all format-related widgets/actions, so we can disable/enable signals when updating.
        self._format_actions = [
            self.fonts,
            self.font_size,
            self.bold_action,
            self.italic_action,
            self.underline_action,
            # We don't need to disable signals for alignment, as they are paragraph-wide.
        ]

        # Initialize.
        self.update_format()
        self.update_title()
        self.show()

    @staticmethod
    def block_signals(objects, b):
        for o in objects:
            o.blockSignals(b)

    def update_format(self):
        """
        Update the font format toolbar/actions when a new text selection is made. This is necessary to keep
        toolbars/etc. in sync with the current edit state.
        :return:
        """
        # Disable signals for all format widgets, so changing values here does not trigger further formatting.
        self.block_signals(self._format_actions, True)

        self.fonts.setCurrentFont(self.editor.currentFont())
        # Nasty, but we get the font-size as a float but want it was an int
        self.font_size.setCurrentText(str(int(self.editor.fontPointSize())))

        self.italic_action.setChecked(self.editor.fontItalic())
        self.underline_action.setChecked(self.editor.fontUnderline())
        self.bold_action.setChecked(self.editor.fontWeight() == QFont.bold)

        self.align_left_action.setChecked(
            self.editor.alignment() == Qt.AlignmentFlag.AlignLeft
        )
        self.align_center_action.setChecked(
            self.editor.alignment() == Qt.AlignmentFlag.AlignCenter
        )
        self.alignr_action.setChecked(
            self.editor.alignment() == Qt.AlignmentFlag.AlignRight
        )
        self.align_justify_action.setChecked(
            self.editor.alignment() == Qt.AlignmentFlag.AlignJustify
        )

        self.block_signals(self._format_actions, False)

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Icon.Critical)
        dlg.show()

    def file_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open file",
            "",
            "HTML documents (*.html);Text documents (*.txt);All files (*.*)",
        )

        try:
            with open(path, "r") as f:
                text = f.read()

        except Exception as e:
            self.dialog_critical(str(e))

        else:
            self.path = path
            # Qt will automatically try and guess the format as txt/html
            self.editor.setText(text)
            self.update_title()

    def file_save(self):
        if self.path is None:
            # If we do not have a path, we need to use Save As.
            return self.file_save_as()

        text = (
            self.editor.toHtml()
            if splitext(self.path) in HTML_EXTENSIONS
            else self.editor.toPlainText()
        )

        try:
            with open(self.path, "w") as f:
                f.write(text)

        except Exception as e:
            self.dialog_critical(str(e))

    def file_save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save file",
            "",
            "HTML documents (*.html);Text documents (*.txt);All files (*.*)",
        )

        if not path:
            # If dialog is cancelled, will return ''
            return

        text = (
            self.editor.toHtml()
            if splitext(path) in HTML_EXTENSIONS
            else self.editor.toPlainText()
        )

        try:
            with open(path, "w") as f:
                f.write(text)

        except Exception as e:
            self.dialog_critical(str(e))

        else:
            self.path = path
            self.update_title()

    def file_print(self):
        dlg = QPrintDialog()
        if dlg.exec():
            self.editor.print_(dlg.printer())

    def update_title(self):
        self.setWindowTitle(
            "%s - Megasolid Idiom"
            % (os.path.basename(self.path) if self.path else "Untitled")
        )

    def edit_toggle_wrap(self):
        if self.editor.lineWrapMode() == QTextEdit.LineWrapMode.NoWrap:
            self.editor.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        else:
            self.editor.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Megasolid Idiom")
    window = MegasolidEditor()
    window.reset()
    app.exec()
