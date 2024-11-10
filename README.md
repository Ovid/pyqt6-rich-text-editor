# Megasolid Code — A rich text code editor in PySide6

* syntax highlighting for: zig, c3, and python
* insert: images, tables, and blender files


# Megasolid Idiom — A rich text editor in PySide6

Python GUIs has a great example of [a rich-text editor in
PyQt5](https://www.pythonguis.com/examples/python-rich-text-editor/).
However, their code uses PyQt5. I'm using PySide6, so I've updated their code to
use that. Also:

* black formatting for standardization
* Refactored some repetitive code

[The original code is available under an MIT
license](https://martinfitzpatrick.com/legal), as is this code.

# Original README:

The word processor for all your small, poorly formatted documents.  An
extension of the notepad, again using a QTextEdit but with rich text editing
enabled. 
 
The editor supports multiple fonts, styles and paragraph text alignment.
There is also support for drag-drop of images, which are automatically opened
and embedded.

Saves and opens HTML format documents.
 
![Wordprocessor](screenshot-wordprocessor.jpg)

> If you think this app is neat and want to learn more about
PyQt in general, take a look at my [free PyQt tutorials](https://www.learnpyqt.com)
which cover everything you need to know to start building your own applications with PyQt.

# Note

Originally ported to PyQt6, but given that PySide6 is the official Python
module from the Qt for Python project, I accepted a PR from
[7gxycn08](https://github.com/7gxycn08) for the update.


## Other licenses

Icons used in the application are by [Yusuke Kamiyaman](http://p.yusukekamiyamane.com/).
