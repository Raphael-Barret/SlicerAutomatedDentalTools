"""The dark palette the modules of this extension share.

Eleven modules carried their own copy: nine of `applyDarkModeStyles` and eleven
of the recursive pass below, 1926 lines in all, and the copies had started to
drift -- a docstring here, an inert `!important` there, and one missing the
`hasattr` guard that keeps the recursion off a parent with no children.

Two modules are deliberately NOT on this. ASO and AREG style widgets the others
do not have (ctkCollapsibleButton, qMRMLNodeComboBox) and AREG uses a darker
palette throughout; folding them in is a decision about how they should look,
not a refactor. They keep their own stylesheet and share the recursive pass.

Qt's stylesheet subset has no `!important`: the token one copy carried was
inert, and dropping it changes nothing.
"""
import qt


def is_dark_mode():
    """Whether Slicer is running under a dark palette."""
    palette = qt.QApplication.instance().palette()
    return palette.color(qt.QPalette.Window).lightness() < 128


def apply_dark_mode(ui_widget):
    """Give `uiWidget` the dark palette, when Slicer is running dark.

    Does nothing under a light palette, so a module can call it
    unconditionally from its setup().
    """
    app = qt.QApplication.instance()
    palette = app.palette()
    bg_color = palette.color(qt.QPalette.Window)
    if bg_color.lightness() < 128:
        # Complete dark mode stylesheet
        dark_stylesheet = """
QLineEdit, QTextEdit {
  background-color: #3c3c3c;
  border: 1px solid #555555;
  border-radius: 4px;
  padding: 6px;
  color: #ffffff;
  selection-background-color: #5dade2;
}
QLineEdit:focus, QTextEdit:focus {
  border: 2px solid #5dade2;
}
QComboBox {
  background-color: #3c3c3c;
  border: 1px solid #555555;
  border-radius: 4px;
  padding: 4px 6px;
  color: #ffffff;
}
QComboBox:focus {
  border: 2px solid #5dade2;
}
QComboBox::drop-down {
  width: 20px;
  border: none;
}
QComboBox QAbstractItemView {
  background-color: #3c3c3c;
  color: #ffffff;
  selection-background-color: #5dade2;
}
QLabel {
  color: #ffffff;
  font-weight: 500;
  background-color: transparent;
}
QPushButton {
  background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5dade2, stop:1 #3498db);
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 10pt;
  padding: 8px;
  margin-top: 4px;
}
QPushButton:hover:!pressed {
  background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7bbcef, stop:1 #5dade2);
}
QPushButton:pressed {
  background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2980b9, stop:1 #1e638d);
}
QPushButton:disabled {
  background-color: #555555;
  color: #888888;
}
QCheckBox {
  color: #ffffff;
  font-weight: 500;
  spacing: 6px;
  background-color: transparent;
}
QCheckBox::indicator {
  width: 18px;
  height: 18px;
  border: 1px solid #555555;
  border-radius: 3px;
  background-color: #3c3c3c;
}
QCheckBox::indicator:hover {
  border: 1px solid #5dade2;
}
QCheckBox::indicator:checked {
  width: 18px;
  height: 18px;
  border: 1px solid #5dade2;
  border-radius: 3px;
  background-color: #5dade2;
  image: url(:/Icons/SmallCheckMark.png);
}
QCheckBox::indicator:checked:hover {
  border: 1px solid #7bbcef;
  background-color: #7bbcef;
}
QProgressBar {
  border: 1px solid #555555;
  border-radius: 4px;
  background-color: #3c3c3c;
  padding: 2px;
  color: #ffffff;
}
QProgressBar::chunk {
  background-color: #5dade2;
  border-radius: 3px;
}
QSpinBox, QDoubleSpinBox {
  background-color: #3c3c3c;
  border: 1px solid #555555;
  border-radius: 4px;
  padding: 4px 6px;
  color: #ffffff;
}
QSpinBox:focus, QDoubleSpinBox:focus {
  border: 2px solid #5dade2;
}
QSlider::groove:horizontal {
  background-color: #555555;
  border-radius: 4px;
}
QSlider::handle:horizontal {
  background-color: #5dade2;
  width: 12px;
  margin: -4px 0;
  border-radius: 6px;
}
QSlider::handle:horizontal:hover {
  background-color: #7bbcef;
}
        """
        ui_widget.setStyleSheet(dark_stylesheet)
        
        # Update QLineEdit, QComboBox, and QLabel for dark mode
        update_line_edit_and_combo_box(ui_widget)

def update_line_edit_and_combo_box(parent):
    """
    Recursively apply dark mode styles to QLineEdit, QComboBox, and QLabel widgets.
    """
    # Update QLabel
    if isinstance(parent, qt.QLabel):
        try:
            parent.setStyleSheet("""
                QLabel {
                  color: #ffffff;
                  font-weight: 500;
                }
            """)
        except (AttributeError, RuntimeError):
            # Un widget sans cette methode, ou dont l objet C++ a deja disparu.
            pass
    
    # Update QLineEdit
    if isinstance(parent, qt.QLineEdit):
        try:
            parent.setStyleSheet("""
                QLineEdit {
                  background-color: #3c3c3c;
                  border: 1px solid #555555;
                  border-radius: 4px;
                  padding: 6px;
                  color: #ffffff;
                }
                QLineEdit:focus {
                  border: 2px solid #5dade2;
                }
            """)
        except (AttributeError, RuntimeError):
            pass
    
    # Update QComboBox
    if isinstance(parent, qt.QComboBox):
        try:
            parent.setStyleSheet("""
                QComboBox {
                  background-color: #3c3c3c;
                  border: 1px solid #555555;
                  border-radius: 4px;
                  padding: 4px 6px;
                  color: #ffffff;
                }
                QComboBox:focus {
                  border: 2px solid #5dade2;
                }
                QComboBox::drop-down {
                  width: 20px;
                  border: none;
                }
                QComboBox QAbstractItemView {
                  background-color: #3c3c3c;
                  color: #ffffff;
                  selection-background-color: #5dade2;
                }
            """)
        except (AttributeError, RuntimeError):
            pass
    
    # Recursively update all children
    if hasattr(parent, 'children'):
        for child in parent.children():
            update_line_edit_and_combo_box(child)
