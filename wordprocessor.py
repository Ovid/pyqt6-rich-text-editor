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
    )
    from PySide6.QtWidgets import (
        QTextEdit,
        QMainWindow,
        QVBoxLayout,
        QWidget,
        QStatusBar,
        QToolBar,
        QFileDialog,
        QMessageBox,
        QFontComboBox,
        QComboBox,
        QApplication,
    )
    from PySide6.QtCore import QSize, Qt, QUrl
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
    )
    from PyQt6.QtWidgets import (
        QTextEdit,
        QMainWindow,
        QVBoxLayout,
        QWidget,
        QStatusBar,
        QToolBar,
        QFileDialog,
        QMessageBox,
        QFontComboBox,
        QComboBox,
        QApplication,
    )
    from PyQt6.QtCore import QSize, Qt, QUrl
    from PyQt6.QtPrintSupport import QPrintDialog

import os
import sys
import uuid

FONT_SIZES = [7, 8, 9, 10, 11, 12, 13, 14, 18, 24, 36, 48, 64, 72, 96, 144, 288]
IMAGE_EXTENSIONS = [".jpg", ".png", ".bmp"]
HTML_EXTENSIONS = [".htm", ".html"]
ADD_SEPARATOR = "addSeparator"


def hex_uuid():
    return uuid.uuid4().hex


def splitext(p):
    return os.path.splitext(p)[1].lower()


class TextEdit(QTextEdit):
    def canInsertFromMimeData(self, source):
        if source.hasImage():
            return True
        else:
            return super(TextEdit, self).canInsertFromMimeData(source)

    def insertFromMimeData(self, source):
        cursor = self.textCursor()
        document = self.document()

        if source.hasUrls():
            for u in source.urls():
                file_ext = splitext(str(u.toLocalFile()))
                if u.isLocalFile() and file_ext in IMAGE_EXTENSIONS:
                    image = QImage(u.toLocalFile())
                    document.addResource(QTextDocument.ResourceType.ImageResource, u, image)
                    cursor.insertImage(u.toLocalFile())

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


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setGeometry(100, 100, 800, 600)
        layout = QVBoxLayout()
        self.editor = TextEdit()
        # Set up the QTextEdit editor configuration
        self.editor.setAutoFormatting(QTextEdit.AutoFormattingFlag.AutoAll)
        self.editor.selectionChanged.connect(self.update_format)
        # Initialize default font size.
        font = QFont("Times New Roman", 12)
        self.editor.setFont(font)
        # We need to repeat the size to init the current format.
        self.editor.setFontPointSize(12)

        # self.path holds the path of the currently open file.
        # If none, we haven't got a file open yet (or creating new).
        self.path = None

        layout.addWidget(self.editor)

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
                        "trigger": self.file_open,
                    },
                    {
                        "status tip": "Save File",
                        "menu name": "Save",
                        "icon": "disk.png",
                        "trigger": self.file_save,
                    },
                    {
                        "status tip": "Save current page to specified file",
                        "menu name": "Save As...",
                        "icon": "disk--pencil.png",
                        "trigger": self.file_save_as,
                    },
                    {
                        "status tip": "Print current page",
                        "menu name": "Print...",
                        "icon": "printer.png",
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
                        "trigger": self.editor.undo,
                    },
                    {
                        "status tip": "Redo last change",
                        "menu name": "Redo",
                        "icon": "arrow-curve.png",
                        "trigger": self.editor.redo,
                    },
                    ADD_SEPARATOR,
                    {
                        "status tip": "Cut selected text",
                        "menu name": "Cut",
                        "icon": "scissors.png",
                        "trigger": self.editor.cut,
                        "shortcut": QKeySequence.StandardKey.Cut,
                    },
                    {
                        "status tip": "Copy selected text",
                        "menu name": "Copy",
                        "icon": "document-copy.png",
                        "trigger": self.editor.copy,
                        "shortcut": QKeySequence.StandardKey.Copy,
                    },
                    {
                        "status tip": "Paste from clipboard",
                        "menu name": "Paste",
                        "icon": "clipboard-paste-document-text.png",
                        "trigger": self.editor.paste,
                        "shortcut": QKeySequence.StandardKey.Paste,
                    },
                    {
                        "status tip": "Select all text",
                        "menu name": "Select all",
                        "icon": "selection-input.png",
                        "trigger": self.editor.selectAll,
                        "shortcut": QKeySequence.StandardKey.SelectAll,
                    },
                    ADD_SEPARATOR,
                    {
                        "status tip": "Toggle wrap text to window",
                        "menu name": "Wrap text to window",
                        "icon": "arrow-continue.png",
                        "trigger": self.edit_toggle_wrap,
                    },
                ],
            },
        ]
        for menu_action in menu_actions:
            toolbar = QToolBar(menu_action["name"])
            toolbar.setIconSize(QSize(16, 16))
            self.addToolBar(toolbar)
            menu = self.menuBar().addMenu(menu_action["menu"])

            for action in menu_action["actions"]:
                if ADD_SEPARATOR == action:
                    menu.addSeparator()
                    continue

                this_action = QAction(
                    QIcon(os.path.join("icons", action["icon"])),
                    action["menu name"],
                    self,
                )
                this_action.setStatusTip(action["status tip"])
                this_action.triggered.connect(action["trigger"])
                menu.addAction(this_action)
                toolbar.addAction(this_action)

        # Sadly, these are not regular enough to add to the menu_actions list.
        format_toolbar = QToolBar("Format")
        format_toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(format_toolbar)
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

        self.bold_action = QAction(
            QIcon(os.path.join("icons", "edit-bold.png")), "Bold", self
        )
        self.bold_action.setStatusTip("Bold")
        self.bold_action.setShortcut(QKeySequence.StandardKey.Bold)
        self.bold_action.setCheckable(True)
        self.bold_action.toggled.connect(
            lambda x: self.editor.setFontWeight(
                QFont.Weight.Bold if x else QFont.Weight.Normal
            )
        )
        format_toolbar.addAction(self.bold_action)
        format_menu.addAction(self.bold_action)

        self.italic_action = QAction(
            QIcon(os.path.join("icons", "edit-italic.png")), "Italic", self
        )
        self.italic_action.setStatusTip("Italic")
        self.italic_action.setShortcut(QKeySequence.StandardKey.Italic)
        self.italic_action.setCheckable(True)
        self.italic_action.toggled.connect(self.editor.setFontItalic)
        format_toolbar.addAction(self.italic_action)
        format_menu.addAction(self.italic_action)

        self.underline_action = QAction(
            QIcon(os.path.join("icons", "edit-underline.png")), "Underline", self
        )
        self.underline_action.setStatusTip("Underline")
        self.underline_action.setShortcut(QKeySequence.StandardKey.Underline)
        self.underline_action.setCheckable(True)
        self.underline_action.toggled.connect(self.editor.setFontUnderline)
        format_toolbar.addAction(self.underline_action)
        format_menu.addAction(self.underline_action)

        format_menu.addSeparator()

        self.align_left_action = QAction(
            QIcon(os.path.join("icons", "edit-alignment.png")), "Align left", self
        )
        self.align_left_action.setStatusTip("Align text left")
        self.align_left_action.setCheckable(True)
        self.align_left_action.triggered.connect(
            lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignLeft)
        )
        format_toolbar.addAction(self.align_left_action)
        format_menu.addAction(self.align_left_action)

        self.align_center_action = QAction(
            QIcon(os.path.join("icons", "edit-alignment-center.png")),
            "Align center",
            self,
        )
        self.align_center_action.setStatusTip("Align text center")
        self.align_center_action.setCheckable(True)
        self.align_center_action.triggered.connect(
            lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        )
        format_toolbar.addAction(self.align_center_action)
        format_menu.addAction(self.align_center_action)

        self.alignr_action = QAction(
            QIcon(os.path.join("icons", "edit-alignment-right.png")),
            "Align right",
            self,
        )
        self.alignr_action.setStatusTip("Align text right")
        self.alignr_action.setCheckable(True)
        self.alignr_action.triggered.connect(
            lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignRight)
        )
        format_toolbar.addAction(self.alignr_action)
        format_menu.addAction(self.alignr_action)

        self.align_justify_action = QAction(
            QIcon(os.path.join("icons", "edit-alignment-justify.png")), "Justify", self
        )
        self.align_justify_action.setStatusTip("Justify text")
        self.align_justify_action.setCheckable(True)
        self.align_justify_action.triggered.connect(
            lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignJustify)
        )
        format_toolbar.addAction(self.align_justify_action)
        format_menu.addAction(self.align_justify_action)

        format_group = QActionGroup(self)
        format_group.setExclusive(True)
        format_group.addAction(self.align_left_action)
        format_group.addAction(self.align_center_action)
        format_group.addAction(self.alignr_action)
        format_group.addAction(self.align_justify_action)

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
        dlg.setIcon(QMessageBox.StandardButton.Critical)
        dlg.show()

    def file_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open file",
            "",
            "HTML documents (*.html);Text documents (*.txt);All files (*.*)",
        )

        try:
            with open(path, "rU") as f:
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
    window = MainWindow()
    app.exec()
