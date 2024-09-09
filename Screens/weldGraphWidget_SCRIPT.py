import sys

from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
from PyQt5 import QtCore

import resources_rc


class WeldGraphWidget(QWidget):
    def __init__(self):
        super(WeldGraphWidget, self).__init__()
        loadUi(r"weldGraphWidget.ui", self)
        self.upperWeldData = {}
        self.lowerWeldData = {}
        self.weldBanners = {'field_weld': False, 'all_around': False, 'double_sided': False, 'tail_info': None}
        # --------------------------------------------------------------Loading scripts--------------------------------
        self.lowerWeldInfo.hide()
        self.lowerWeldInfo.setEnabled(False)
        self.lineEdits = {'upper_size': self.upperSizeLine,
                          'upper_weld_quant': self.upperWeldQuantityLine,
                          'upper_length': self.upperWeldLengthLine,
                          'upper_weld_spacing': self.upperWeldSpacingLine,
                          'sided_size': self.lowerSizeLine,
                          'sided_weld_quant': self.lowerWeldQuantityLine,
                          'sided_length': self.lowerWeldLengthLine,
                          'sided_weld_spacing': self.lowerWeldSpacingLine,
                          }
        self.pushButtons = {
            'field_weld': self.weldAsemblyIcon,
            'all_around': self.weldRoundedIcon,
            'upper_weld_type': self.upperWeldTypeIcon,
            'upper_weld_face': self.upperWeldFaceIcon,
            'sided_weld_type': self.lowerWeldTypeIcon,
            'sided_weld_face': self.lowerWeldFaceIcon
        }
        # ---------------------------------------------------------------Button scripting------------------------------
        self.addSideWeld.clicked.connect(lambda: self.toggleSideWeld())
        self.upperWeldTypeIcon.clicked.connect(
            lambda: self.openWeldTypeDialog(self.upperWeldTypeIcon, 'weldType', False))
        self.upperWeldFaceIcon.clicked.connect(
            lambda: self.openWeldTypeDialog(self.upperWeldFaceIcon, 'weldFace', False))
        self.lowerWeldTypeIcon.clicked.connect(
            lambda: self.openWeldTypeDialog(self.lowerWeldTypeIcon, 'weldType', True))
        self.lowerWeldFaceIcon.clicked.connect(
            lambda: self.openWeldTypeDialog(self.lowerWeldFaceIcon, 'weldFace', True))
        self.weldAsemblyIcon.clicked.connect(
            lambda: self.updateWeldBanner(self.weldAsemblyIcon, r':/Icons/Icons/weldIcon_weldBanner.png',
                                          r':/Icons/Icons/banner_weld_face.png', 'field_weld'))
        self.weldRoundedIcon.clicked.connect(
            lambda: self.updateWeldBanner(self.weldRoundedIcon, r':/Icons/Icons/weldIcon_weldRoundedLine.png',
                                          r':/Icons/Icons/weldIcon_weldLine.png', 'all_around'))
        # ---------------upper weld line-----------------------
        self.upperSizeCombo.currentTextChanged.connect(lambda x: self.updateWeldData(x, 'upper_sizeType', 'upper'))
        self.upperSizeCombo.setCurrentIndex(2)
        self.upperSizeLine.textChanged.connect(
            lambda: self.updateWeldData(self.upperSizeLine.text(), 'upper_size', 'upper'))
        self.upperWeldQuantityLine.textChanged.connect(
            lambda: self.updateWeldData(self.upperWeldQuantityLine.text(), 'upper_weld_quant', 'upper'))
        self.upperWeldLengthLine.textChanged.connect(
            lambda: self.updateWeldData(self.upperWeldLengthLine.text(), 'upper_length', 'upper'))
        self.upperWeldSpacingLine.textChanged.connect(
            lambda: self.updateWeldData(self.upperWeldSpacingLine.text(), 'upper_weld_spacing', 'upper'))
        # ---------------lower weld line----------------------
        self.lowerSizeCombo.currentTextChanged.connect(lambda x: self.updateWeldData(x, 'sided_sizeType', 'lower'))
        self.lowerSizeCombo.setCurrentIndex(2)
        self.lowerSizeLine.textChanged.connect(
            lambda: self.updateWeldData(self.lowerSizeLine.text(), 'sided_size', 'lower'))
        self.lowerWeldQuantityLine.textChanged.connect(
            lambda: self.updateWeldData(self.lowerWeldQuantityLine.text(), 'sided_weld_quant', 'lower'))
        self.lowerWeldLengthLine.textChanged.connect(
            lambda: self.updateWeldData(self.lowerWeldLengthLine.text(), 'sided_length', 'lower'))
        self.lowerWeldSpacingLine.textChanged.connect(
            lambda: self.updateWeldData(self.lowerWeldSpacingLine.text(), 'sided_weld_spacing', 'lower'))
        self.tailMultiline.textChanged.connect(
            lambda: (self.weldBanners.update({"tail_info": self.tailMultiline.toPlainText()}),
                     print(f"Weld banners updated: {self.weldBanners}")))

        self.editGraphBtn.hide()

    def toggleSideWeld(self):
        if self.addSideWeld.isChecked():
            self.lowerWeldInfo.show()
            # self.addSideWeld.setStyleSheet("color: rgb(0, 0, 0);"
            #                                "background-color : rgb(30, 210, 80)")
            self.lowerWeldInfo.setEnabled(True)
            self.weldBanners['double_sided'] = True
        else:
            self.lowerWeldInfo.hide()
            self.lowerWeldInfo.setEnabled(False)
            # self.addSideWeld.setStyleSheet("color: rgb(150, 150, 150);"
            #                                "background-color : rgb(255, 255, 255)")
            self.weldBanners['double_sided'] = False
        print(f'Weld banners changed -- Double sided weld : {self.weldBanners}')

    def openWeldTypeDialog(self, triggering_btn: QPushButton, dialogType: str, rotated: bool):
        weld_dialog = weldTypeDialog(dialogType)
        weld_dialog.setWindowFlags(Qt.FramelessWindowHint)
        # Let's move the new dialog to open in place of calling btn
        # Firstly get the position in relation to the global (0,0) of the calling widget
        global_position = triggering_btn.mapToGlobal(QtCore.QPoint(0, 0))
        # Then translate this global position in relation to calling widget (triggering_btn), bcs "move" function of
        # a widget moves it in relation to parent widget, not global
        move_vect = weld_dialog.mapFromGlobal(global_position)
        weld_dialog.move(move_vect)
        weld_dialog.exec_()  # exec_() opens the Dialog and waits for user input
        # save the clicked options for upper weld in Dialog specific dict
        if weld_dialog.selectedBtn_Name.count('Type') > 0:
            self.upperWeldData['upper_weld_type'] = weld_dialog.selectedBtn_Name.replace('weldType_', '')
        else:
            self.upperWeldData['upper_weld_face'] = weld_dialog.selectedBtn_Name.replace('weldFace_', '')
        px = weld_dialog.selected_btn_icon.pixmap(QtCore.QSize(20, 20))
        # rotate the icon in case the calling button is rotated
        if rotated:
            px = px.transformed(QtGui.QTransform().scale(1, -1))
            # save the clicked options for lower weld in Dialog specific dict
            if weld_dialog.selectedBtn_Name.count('Type') > 0:
                self.lowerWeldData['sided_weld_type'] = weld_dialog.selectedBtn_Name.replace('weldType_', '')
            else:
                self.lowerWeldData['sided_weld_face'] = weld_dialog.selectedBtn_Name.replace('weldFace_', '')
        px = QtGui.QIcon(px)
        triggering_btn.setIcon(px)

    def transformWeldSymbolType(self, new_type):
        if new_type == "normal":
            self.staggeredGraph.hide()
            self.upperWeldAmountLabel.show()
            self.upperWeldLengthLine.show()
            self.upperWeldSpacingFrame.hide()
            self.lowerWeldLengthLine.show()
            self.lowerWeldAmountLabel.show()
            self.lowerWeldSpacingFrame.hide()
            self.upperWeldQuantityLine.hide()
            self.upperWeldAmountLabel.hide()
            self.lowerWeldQuantityLine.hide()
            self.lowerWeldAmountLabel.hide()
        elif new_type == 'staggered':
            self.staggeredGraph.hide()
            self.upperStaggerSpacer.hide()
            self.lowerStaggerSpacer.hide()
            self.upperWeldAmountLabel.show()
            self.upperWeldLengthLine.show()
            self.upperWeldSpacingFrame.show()
            self.lowerWeldAmountLabel.show()
            self.lowerWeldLengthLine.show()
            self.lowerWeldSpacingFrame.show()
            self.upperWeldQuantityLine.show()
            self.upperWeldAmountLabel.show()
            self.lowerWeldQuantityLine.show()
            self.lowerWeldAmountLabel.show()
        else:
            self.staggeredGraph.show()
            self.upperStaggerSpacer.show()
            self.lowerStaggerSpacer.show()
            self.upperWeldAmountLabel.show()
            self.upperWeldLengthLine.show()
            self.upperWeldSpacingFrame.show()
            self.lowerWeldAmountLabel.show()
            self.lowerWeldLengthLine.show()
            self.lowerWeldSpacingFrame.show()
            self.upperWeldQuantityLine.show()
            self.upperWeldAmountLabel.show()
            self.lowerWeldQuantityLine.show()
            self.lowerWeldAmountLabel.show()

    def updateWeldData(self, updated_value, key_ref: str, weld_line: str):
        if weld_line == "upper":
            self.upperWeldData[key_ref] = updated_value if len(updated_value) > 0 else None
        else:
            self.lowerWeldData[key_ref] = updated_value if len(updated_value) > 0 else None
        # print(f"Weld data updated: upper -> {self.upperWeldData}", end=" -> ")
        # print(f"Weld data updated: lower -> {self.lowerWeldData}")

    def updateWeldBanner(self, weldBannerBtn: QPushButton, checkedIcon_path, uncheckedIcon_path, banner_type: str):
        if weldBannerBtn.isChecked():
            weldBannerBtn.setIcon(QtGui.QIcon(QtGui.QPixmap(checkedIcon_path)))
            self.weldBanners[banner_type] = True
        else:
            weldBannerBtn.setIcon(QtGui.QIcon(QtGui.QPixmap(uncheckedIcon_path)))
            self.weldBanners[banner_type] = False
        print(f'Weld banners changed: {self.weldBanners}')


class weldTypeDialog(QDialog):
    def __init__(self, dialogType):
        super(weldTypeDialog, self).__init__()
        if dialogType == "weldType":
            loadUi(r"weldTypeDialog.ui", self)
            self.selectedBtn_Name = str
            self.selected_btn_icon = None
            self.weldType_184.clicked.connect(lambda: self.select_button(self.weldTypesBtns, self.weldType_184))
            self.weldType_114.clicked.connect(lambda: self.select_button(self.weldTypesBtns, self.weldType_114))
            self.weldType_064.clicked.connect(lambda: self.select_button(self.weldTypesBtns, self.weldType_064))
            self.weldType_134.clicked.connect(lambda: self.select_button(self.weldTypesBtns, self.weldType_134))
            self.weldType_164.clicked.connect(lambda: self.select_button(self.weldTypesBtns, self.weldType_164))
            self.weldType_174.clicked.connect(lambda: self.select_button(self.weldTypesBtns, self.weldType_174))
            self.weldType_014.clicked.connect(lambda: self.select_button(self.weldTypesBtns, self.weldType_014))
            self.weldType_104.clicked.connect(lambda: self.select_button(self.weldTypesBtns, self.weldType_104))
            self.weldType_074.clicked.connect(lambda: self.select_button(self.weldTypesBtns, self.weldType_074))
            self.weldType_124.clicked.connect(lambda: self.select_button(self.weldTypesBtns, self.weldType_124))
            self.weldType_204.clicked.connect(lambda: self.select_button(self.weldTypesBtns, self.weldType_204))
            self.weldType_194.clicked.connect(lambda: self.select_button(self.weldTypesBtns, self.weldType_194))
            self.weldType_024.clicked.connect(lambda: self.select_button(self.weldTypesBtns, self.weldType_024))
            self.weldType_094.clicked.connect(lambda: self.select_button(self.weldTypesBtns, self.weldType_094))
            self.weldType_144.clicked.connect(lambda: self.select_button(self.weldTypesBtns, self.weldType_144))
            self.weldType_054.clicked.connect(lambda: self.select_button(self.weldTypesBtns, self.weldType_054))
            self.weldType_044.clicked.connect(lambda: self.select_button(self.weldTypesBtns, self.weldType_044))
            self.weldType_084.clicked.connect(lambda: self.select_button(self.weldTypesBtns, self.weldType_084))
            self.weldType_214.clicked.connect(lambda: self.select_button(self.weldTypesBtns, self.weldType_214))
        else:
            loadUi(r"weldFaceDialog.ui", self)

            self.selectedBtn_Name = None
            self.selected_btn_icon = None
            self.weldFace_circline.clicked.connect(
                lambda: self.select_button(self.weldFaceBtns, self.weldFace_circline))
            self.weldFace_convex.clicked.connect(
                lambda: self.select_button(self.weldFaceBtns, self.weldFace_convex))
            self.weldFace_rect.clicked.connect(lambda: self.select_button(self.weldFaceBtns, self.weldFace_rect))
            self.weldFace_flat.clicked.connect(lambda: self.select_button(self.weldFaceBtns, self.weldFace_flat))
            self.weldFace_concave.clicked.connect(
                lambda: self.select_button(self.weldFaceBtns, self.weldFace_concave))
            self.weldFace_anchor.clicked.connect(
                lambda: self.select_button(self.weldFaceBtns, self.weldFace_anchor))
            self.weldFace_chord.clicked.connect(lambda: self.select_button(self.weldFaceBtns, self.weldFace_chord))
            self.weldFace_banner.clicked.connect(
                lambda: self.select_button(self.weldFaceBtns, self.weldFace_banner))
            self.weldFace_circ.clicked.connect(lambda: self.select_button(self.weldFaceBtns, self.weldFace_circ))

    def select_button(self, btns_container: QFrame, selected_btn: QPushButton):
        if not selected_btn.isChecked():
            selected_btn.setStyleSheet("background-color : rgb(255, 255, 255)")
        else:
            for btn in btns_container.findChildren(QPushButton):
                if not btn == selected_btn:
                    btn.setStyleSheet("background-color : rgb(255, 255, 255)")
            selected_btn.setStyleSheet("background-color : rgb(30, 210, 80)")
            self.selectedBtn_Name = selected_btn.objectName()
            self.selected_btn_icon = selected_btn.icon()
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = WeldGraphWidget()
    dialog.show()

    try:
        sys.exit(app.exec_())
    except:
        print("Exiting the App")
