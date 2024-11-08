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

CONVERT = None
if os.path.isfile('/usr/bin/convert'):
    CONVERT = 'convert'

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


class MegasolidEditor(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MegasolidEditor, self).__init__(*args, **kwargs)
        self.left_widget = None
        self.right_widget = None
    def reset(self, x=100, y=100, width=840, height=600, use_icons=True, use_menu=True, use_monospace=True):
        self.setGeometry(x, y, width, height)
        layout = QHBoxLayout()
        self.editor = TextEdit()
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
        layout.addWidget(self.editor)
        if self.right_widget:
            layout.addWidget(self.right_widget)

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

class MegasolidCodeEditor( MegasolidEditor ):
    def reset(self, x=100, y=100, width=930, height=600, use_icons=False, use_menu=False):
        layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(layout)
        self.line_counts = QLabel('.')
        layout.addWidget(self.line_counts)
        layout.addStretch(1)
        self.left_widget = container
        self.images_layout = None
        self.qimages = {}
        if CONVERT:
            layout = QVBoxLayout()
            container = QWidget()
            container.setLayout(layout)
            layout.addStretch(1)
            self.right_widget = container
            self.images_layout = layout

        super(MegasolidCodeEditor,self).reset(x,y,width,height, use_icons=use_icons, use_menu=use_menu, use_monospace=True)

        self.setStyleSheet('background-color:rgb(42,42,42); color:lightgrey')
        self.editor.setStyleSheet('background-color:rgb(42,42,42); color:white')
        self.timer = QTimer()
        self.timer.timeout.connect(self.loop)
        self.timer.start(3000)
        self.prev_html = None
        self.use_syntax_highlight = True
        self.use_syntax_highlight_action = act = QAction("🗹", self)
        act.setToolTip("toggle syntax highlighting")
        act.setStatusTip("toggle syntax highlighting")
        act.setCheckable(True)
        act.setChecked(True)
        act.toggled.connect( lambda x,a=act: self.toggle_syntax_highlight(x,a) )
        self.format_toolbar.addAction(act)

    def toggle_syntax_highlight(self, val, btn):
        self.use_syntax_highlight = val
        if val:
            btn.setText('🗹')
        else:
            btn.setText('🗶')

    SYNTAX_PY = {
        'def': 'cyan',
        'assert':'cyan',
        'for': 'red',
        'in' : 'red',
        'while': 'red',
        'if':'red',
        'elif':'red',
        'else':'red',
        'class':'red',
        'return':'red',
    }
    SYNTAX_C = {
        'void'   : 'yellow',
        'static' : 'yellow',
        'const'  : 'yellow',
        'struct' : 'yellow',
    }
    C_TYPES = ['char', 'short', 'int', 'long', 'float', 'double']
    for _ in C_TYPES: SYNTAX_C[_]='lightgreen'
    SYNTAX_C3 = {}
    C3_KEYWORDS = ['true', 'false', 'fn', 'extern', 'ichar', 'ushort', 'float16', 'bool', 'bitstruct', 'distinct', 'import']
    C3_ATTRS = ['@wasm', '@packed', '@adhoc', '@align', '@benchmark', '@bigendian', '@builtin', 
        '@callc', '@deprecated', '@export', '@finalizer', '@if', '@init', '@inline', '@littleendian',
        '@local', '@maydiscard', '@naked', '@nodiscard', '@noinit', '@norecurse', '@noreturn', '@nostrip',
        '@obfuscate', '@operator', '@overlap', '@private', '@pure', '@reflect', '@section', '@test',
        '@unused', '@weak',
    ]
    for _ in C3_KEYWORDS+C3_ATTRS: SYNTAX_C3[_]='pink'

    ZIG_TYPES = ['i%s'%i for i in (8,16,32,64,128)] + ['u%s'%i for i in (8,16,32,64,128)] + ['f16', 'f32', 'f64', 'f80', 'f128']
    ZIG_TYPES += 'isize usize c_char c_short c_ushort c_int c_uint c_long c_ulong c_longlong c_ulonglong anyopaque type anyerror comptime_int comptime_float'.split()
    SYNTAX_ZIG = {
        '@intCast' : 'orange',
        '@intFromFloat' : 'orange',
    }
    ZIG_KEYWORDS = 'defer null undefined try pub comptime var or callconv export'.split()
    for _ in ZIG_KEYWORDS + ZIG_TYPES: SYNTAX_ZIG[_]='orange'

    SYNTAX = {}
    SYNTAX.update(SYNTAX_PY)
    SYNTAX.update(SYNTAX_C)
    SYNTAX.update(SYNTAX_C3)
    SYNTAX.update(SYNTAX_ZIG)

    def has_keywords(self, txt):
        tokens = txt.split()
        for kw in self.SYNTAX:
            if kw in tokens:
                return True
        return False

    def tokenize(self, txt):
        toks = []
        for c in txt:
            if c==self.OBJ_REP:
                toks.append(c)
            elif c in (' ', '\t'):
                if not toks or type(toks[-1]) is not list:
                    toks.append([])
                toks[-1].append(c)
            elif c == '\n':
                toks.append(b'\n')
            elif c in '()[]{}:':
                toks.append(tuple([c]))
            else:
                if not toks or type(toks[-1]) is not str:
                    toks.append('')
                toks[-1] += c
        return toks

    ## https://qthub.com/static/doc/qt5/qtgui/qtextdocument.html#toPlainText
    ## Note: Embedded objects, such as images, are represented by a Unicode value U+FFFC (OBJECT REPLACEMENT CHARACTER).
    OBJ_REP = chr(65532)
    def loop(self):
        if not self.use_syntax_highlight:
            return
        h = self.editor.toHtml()
        if h != self.prev_html:
            d = xml.dom.minidom.parseString(h)
            images = [img.getAttribute('src') for img in d.getElementsByTagName('img')]

            txt = self.editor.toPlainText()
            toks = self.tokenize(txt)

            cur = self.editor.textCursor()
            pos = cur.position()
            doc = xml.dom.minidom.Document()
            p = doc.createElement('p')
            p.setAttribute('style', 'margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; white-space: pre-wrap;')
            img_index = 0
            #print(images)
            for tok in toks:
                if tok==self.OBJ_REP:
                    img = doc.createElement('img')
                    src = images[ img_index ]
                    if CONVERT and not src.startswith('/tmp'):
                        a,b = os.path.split(src)
                        tmp = '/tmp/%s.png'%b
                        if tmp not in self.qimages:
                            cmd = [CONVERT, src, '-resize', '256x256', tmp]
                            print(cmd)
                            subprocess.check_call(cmd)
                            qimg = QImage(tmp)
                            #print(dir(qimg))
                            #print(dir(self.images_layout))
                            qlab = QLabel()
                            qlab.setPixmap(QPixmap.fromImage(qimg))
                            print(dir(qlab))
                            self.images_layout.addWidget(qlab)
                            self.qimages[tmp]=qimg

                        cmd = [CONVERT, src, '-resize', '32x32', tmp]
                        print(cmd)
                        subprocess.check_call(cmd)
                        src = tmp

                    img_index += 1
                    img.setAttribute('src', src)
                    p.appendChild(img)
                elif type(tok) is bytes:
                    p.appendChild(doc.createElement('br'))
                elif type(tok) is str:
                    if tok in self.SYNTAX:
                        f = doc.createElement('font')
                        f.setAttribute('color', self.SYNTAX[tok])
                        f.appendChild(doc.createTextNode(tok))
                        p.appendChild(f)
                    else:
                        p.appendChild(doc.createTextNode(tok))
                elif type(tok) in (list,tuple):
                    p.appendChild(doc.createTextNode(''.join(tok)))

            html = p.toxml()
            html = html.replace('<br />', '<br/>')
            o = []
            lines = []
            for idx, ln in enumerate(html.split('<br/>')):
                if '{' in ln and ln.count('{')==ln.count('}'):
                    ln = ln.replace('{', '{<u style="background-color:blue">')
                    ln = ln.replace('}', '</u>}')
                o.append(ln)
                lines.append(str(idx+1))
            self.line_counts.setText( "<p style='line-height: 1.1;'>%s</p>" % '<br/>'.join(lines))
            html = '<br/>'.join(o)

            html = html.replace('[', '[<b style="background-color:purple">')
            html = html.replace(']', '</b>]')

            html = html.replace('(', '<i style="background-color:black">(')
            html = html.replace(')', ')</i>')

            self.editor.setHtml(html)
            self.prev_html = self.editor.toHtml()
            cur = self.editor.textCursor()
            cur.setPosition(pos)
            self.editor.setTextCursor(cur)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Megasolid Idiom")
    if '--code-editor' in sys.argv:
        window = MegasolidCodeEditor()
    else:
        window = MegasolidEditor()
    window.reset()
    app.exec()
