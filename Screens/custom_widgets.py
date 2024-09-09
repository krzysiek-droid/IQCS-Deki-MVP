from PyQt5.QtCore import pyqtSignal, QPropertyAnimation, QRect
from PyQt5.QtWidgets import QLineEdit, QSizePolicy, QToolButton, QPushButton
from PyQt5.uic.properties import QtGui


class CustomLineEdit(QLineEdit):
    def __init__(self, *args):
        super(CustomLineEdit, self).__init__(*args)
        self.clearAction = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.textChanged.connect(lambda: self.customLineEdit_textChanged())
        self.customLineEdit_textChanged()
        self.setClearButtonEnabled(False)

        self.setStyleSheet('CustomLineEdit[readOnly="true"]{'
                           '    background-color: rgb(230, 230, 230);}'
                           'CustomLineEdit[readOnly="false"]{'
                           '    background-color: rgb(255, 255, 255);'
                           '    color: green;}'
                           'CustomLineEdit{'
                           '    border-bottom: 1px solid;'
                           '    border-color: gray;}'
                           )

    def customLineEdit_textChanged(self):
        try:
            if self.isReadOnly() and self.clearAction is None:
                clear_icon = QtGui.QIcon(fr'D:\CondaPy - Projects\PyGUIs\DekiApp_pyqt5\Icons\edit-3.svg')
                self.clearAction = self.addAction(clear_icon, QLineEdit.ActionPosition.TrailingPosition)
                self.clearAction.triggered.connect(self.clear_line)
                self.setClearButtonEnabled(False)
                self.setReadOnly(True)
            else:
                self.removeAction(self.clearAction)
                self.clearAction = None
                self.setClearButtonEnabled(True)
        except Exception as e:
            print(f"custom_widgets | CustomLineEdit Func(customLineEdit_textChanged) failre | -> {e}")

    def clear_line(self):
        self.setReadOnly(False)
        self.customLineEdit_textChanged()


class MouseClearableLineEdit(QLineEdit):
    clicked = pyqtSignal()
    confirmed = pyqtSignal(bool)
    isConfirmed = False
    hasValue = False

    def mousePressEvent(self, event):
        super(MouseClearableLineEdit, self).mousePressEvent(event)
        if not self.isReadOnly():
            self.clicked.emit()

    def setValue(self, a0: str):
        if float(a0) > 0:
            self.hasValue = True
        else:
            self.hasValue = False

    def setNeutral(self):
        style = "border-bottom: 2px solid rgb(125, 125, 125);"
        self.setStyleSheet(style)
        self.hasValue = False

    def setConfirmed(self, boolean: bool):
        self.confirmed.emit(boolean)
        if boolean:
            style = "border-bottom: 2px solid rgb(30, 210, 80);"
            self.setStyleSheet(style)
            self.setReadOnly(True)
            self.isConfirmed = True
            return self.isConfirmed
        elif not boolean:
            style = "border-bottom: 2px solid rgb(255, 150, 0);"
            self.setStyleSheet(style)
            self.setReadOnly(False)
            self.isConfirmed = False
            return self.isConfirmed


class CustomPushCircleButton(QPushButton):
    def __init__(self, *arg, **kwargs):
        super(CustomPushCircleButton, self).__init__(*arg, **kwargs)

        self.clicked.connect(lambda x: print(x))

    def focusInEvent(self, event):
        super(CustomPushCircleButton, self).focusInEvent(event)
        print('Mouse moved')
        # animation = QPropertyAnimation(self, "size")
        # animation.setDuration(250)
        # animation.setStartValue(QRect(60, 60, self.width(), self.height()))
        # animation.setEndValue(QRect(80, 80, self.width(), self.height()))
        # animation.start()

    def focusOutEvent(self, e: QtGui.QFocusEvent) -> None:
        super(CustomPushCircleButton, self).focusOutEvent(e)
        print('focused out')
