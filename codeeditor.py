from wordprocessor import *

class MegasolidCodeEditor( MegasolidEditor ):
    def reset(self, x=100, y=100, width=930, height=600, use_icons=False, use_menu=False):
        self.tables = []

        layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(layout)
        self.line_counts = QLabel('.')
        layout.addWidget(self.line_counts)
        layout.addStretch(1)
        self.left_widget = container
        self.images_layout = None
        self.qimages = {}

        layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(layout)
        layout.addStretch(1)
        self.right_widget = container
        self.images_layout = layout

        super(MegasolidCodeEditor,self).reset(
            x,y,width,height, 
            use_icons=use_icons, 
            use_menu=use_menu, 
            use_monospace=True, 
            allow_inline_tables=False)

        self.editor.tables = self.tables

        self.setStyleSheet('background-color:rgb(42,42,42); color:lightgrey')
        self.editor.setStyleSheet('background-color:rgb(42,42,42); color:white')

        self.editor.on_link_clicked = self.on_link_clicked
        self.editor.on_new_table = self.on_new_table
        self.editor.on_mouse_over_anchor = self.on_mouse_over_anchor

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

        if sys.platform=='win32' and not os.path.isdir('/tmp'):
            os.mkdir('/tmp')


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
            if c==self.OBJ_REP or c==self.OBJ_TABLE:
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
    OBJ_TABLE = '▦' #'\x00'
    def loop(self):
        if not self.use_syntax_highlight:
            return
        h = self.editor.toHtml()
        if h != self.prev_html:
            if '\x00' in h:
                ## this can happen on copy and paste from libreoffice a null byte at the end
                h = h.replace('\x00', '')

            try:
                d = xml.dom.minidom.parseString(h)
            except xml.parsers.expat.ExpatError as err:
                for i,ln in enumerate(h.splitlines()):
                   print(i+1,ln.encode('utf-8'))
                raise err

            #tables = [elt for elt in d.getElementsByTagName('table')]
            #if tables:
            #    self.tables = tables
            images = [img.getAttribute('src') for img in d.getElementsByTagName('img')]

            txt = self.editor.toPlainText()
            print('-'*80)
            print(txt.encode('utf-8'))
            print('_'*80)
            toks = self.tokenize(txt)
            print(toks)

            cur = self.editor.textCursor()
            pos = cur.position()
            doc = xml.dom.minidom.Document()
            p = doc.createElement('p')
            p.setAttribute('style', 'margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; white-space: pre-wrap;')
            img_index = 0
            tab_index = 0
            nodes = []
            for tok in toks:
                if tok==self.OBJ_TABLE:
                    tab = self.tables[tab_index]
                    print(tab)
                    print(tab.toxml())
                    anchor = doc.createElement('a')
                    anchor.setAttribute('href', str(tab_index))
                    anchor.setAttribute('style', 'color:cyan')
                    anchor.appendChild(doc.createTextNode(self.OBJ_TABLE))
                    nodes.append(anchor)
                    tab_index += 1
                elif tok==self.OBJ_REP:
                    img = doc.createElement('img')
                    src = images[ img_index ]
                    if not src.startswith('/tmp'):
                        q = QImage(src)
                        a,b = os.path.split(src)
                        tmp = '/tmp/%s.png'%b
                        if tmp not in self.qimages:
                            qlab = QLabel()
                            qs = q.scaled(256,256, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                            qpix = QPixmap.fromImage(qs)
                            qlab.setPixmap(qpix)
                            self.images_layout.addWidget(qlab)
                            self.qimages[tmp]=qpix

                        qs = q.scaled(32,32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        qs.save(tmp)
                        src = tmp

                    img_index += 1
                    img.setAttribute('src', src)
                    anchor = doc.createElement('a')
                    anchor.setAttribute('href', src)
                    anchor.appendChild(img)
                    nodes.append(anchor)
                elif type(tok) is bytes:
                    assert tok==b'\n'
                    nodes.append( doc.createElement('br') )
                elif type(tok) is str:
                    if tok in self.SYNTAX:
                        f = doc.createElement('font')
                        f.setAttribute('color', self.SYNTAX[tok])
                        f.appendChild(doc.createTextNode(tok))
                        nodes.append(f)
                    else:
                        nodes.append(doc.createTextNode(tok))
                elif type(tok) in (list,tuple):
                    nodes.append(doc.createTextNode(''.join(tok)))

            for elt in nodes:
                p.appendChild(elt)

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


    def on_link_clicked(self, url):
        print('clicked:', url)
        if url.isdigit():
            index = int(url)
            print('clicked on table:', index)
            tab = self.table_to_qt(self.tables[index])
            clear_layout(self.images_layout)
            self.images_layout.addWidget(tab)
            tab.show()
        elif url in self.qimages:
            qlab = QLabel()
            qlab.setPixmap(self.qimages[url])
            clear_layout(self.images_layout)
            self.images_layout.addWidget(qlab)
            qlab.show()

    def table_to_qt(self, elt):
        tab = QTableWidget()
        tab.setStyleSheet('background-color:white; color:black;')
        rows = elt.getElementsByTagName('tr')
        tab.setRowCount(len(rows))
        tab.setColumnCount( len(rows[0].getElementsByTagName('td')) )
        for y, tr in enumerate( elt.getElementsByTagName('tr') ):
            for x, td in enumerate( tr.getElementsByTagName('td') ):
                txt = get_dom_text(td.childNodes).strip()
                print(x,y, txt)
                tab.setItem(y,x, QTableWidgetItem(txt))

        tab.resizeColumnsToContents()
        return tab

    def on_new_table(self, elt):
        tab = self.table_to_qt(elt)
        clear_layout(self.images_layout)
        self.images_layout.addStretch(1)
        self.images_layout.addWidget(tab)
        return elt

    def on_mouse_over_anchor(self, event, url, sym):
        if sym==self.OBJ_TABLE:
            assert url.isdigit()
            tab = self.tables[int(url)]
            arr = self.table_to_code(tab)
            print(arr)
            QToolTip.showText(event.globalPosition().toPoint(), arr)

    def table_to_code(self, elt):
        o = []
        rows = elt.getElementsByTagName('tr')
        if len(rows)==1:
            tr = rows[0]
            for x, td in enumerate( tr.getElementsByTagName('td') ):
                txt = get_dom_text(td.childNodes).strip()
                o.append(txt)
        else:
            for y, tr in enumerate( rows ):
                r = []
                for x, td in enumerate( tr.getElementsByTagName('td') ):
                    txt = get_dom_text(td.childNodes).strip()
                    if not txt:
                        r.append('0')
                    else:
                        r.append(txt)
                o.append('{%s}' % ','.join(r))

        return '{%s}' % ','.join(o)


def get_dom_text(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
        else:
            rc.append(get_dom_text(node.childNodes))
    return ''.join(rc)

def clear_layout(layout):
    for i in reversed(range(layout.count())):
        widget = layout.itemAt(i).widget()
        if widget is not None: widget.setParent(None)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Megasolid Idiom")
    window = MegasolidCodeEditor()
    window.reset()
    app.exec()