import pathlib
import sys
from typing import Union

from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt

from Screens import pdfViewWidget_SCRIPT as pdfviewer, db_objects


class NewWeldDialog(QDialog):
    def __init__(self, parentConstruction):
        super(NewWeldDialog, self).__init__()
        loadUi(r'new_weld_UI.ui', self)
        # self.setWindowFlag(Qt.FramelessWindowHint)
        self.parentConstruction = parentConstruction
        self.mainConstruction = parentConstruction.mainConstructionObject
        self.db = QApplication.instance().database
        self.new_weld_DbName = f'{self.mainConstruction.info["serial_number"]}_modelWelds'
        self.wps_filepath = None
        from Screens.db_objects import WeldObject
        self.new_weldObj = WeldObject()
        # ---------------------------------------------------------------Screen loading functions----------------------
        self.parentConstructionLbl.setText(
            f"{self.parentConstruction.info['name']}-{self.parentConstruction.info['tag']}")
        self.mainConstructionLbl.setText(f"{self.mainConstruction.info['name']}-{self.mainConstruction.info['tag']}")
        self.new_weldObj.info.update({'belonging_construction_tag': self.parentConstruction.info['tag'],
                                      'belonging_construction_ID': self.parentConstruction.info['id']})
        import weldGraphWidget_SCRIPT as weldGraphWidget
        self.weldGraph = weldGraphWidget.WeldGraphWidget()
        self.weldGraphLayout.addWidget(self.weldGraph)
        self.select_jointContinuity(self.normalWeldBtn)
        self.weldGraph.transformWeldSymbolType("normal")

        # ----------------------------------------------------------------Buttons scripting----------------------------
        self.closeBtn.clicked.connect(lambda: self.close())
        self.testMthdBtnLT.clicked.connect(lambda: self.select_testingMethod(self.testMthdBtnLT))
        self.testMthdBtnMT.clicked.connect(lambda: self.select_testingMethod(self.testMthdBtnMT))
        self.testMthdBtnPT.clicked.connect(lambda: self.select_testingMethod(self.testMthdBtnPT))
        self.testMthdBtnVT.clicked.connect(lambda: self.select_testingMethod(self.testMthdBtnVT))
        self.testMthdBtnRT.clicked.connect(lambda: self.select_testingMethod(self.testMthdBtnRT))
        self.testMthdBtnUT.clicked.connect(lambda: self.select_testingMethod(self.testMthdBtnUT))
        self.buttJointBtn.clicked.connect(lambda: self.select_jointType(self.buttJointBtn))
        self.lapJointBtn.clicked.connect(lambda: self.select_jointType(self.lapJointBtn))
        self.cornerJointBtn.clicked.connect(lambda: self.select_jointType(self.cornerJointBtn))
        self.teeJointBtn.clicked.connect(lambda: self.select_jointType(self.teeJointBtn))
        self.edgeJointBtn.clicked.connect(lambda: self.select_jointType(self.edgeJointBtn))
        self.normalWeldBtn.clicked.connect(
            lambda: (self.select_jointContinuity(self.normalWeldBtn),
                     self.weldGraph.transformWeldSymbolType("normal")))
        self.intermittentWeldBtn.clicked.connect(
            lambda: (self.select_jointContinuity(self.intermittentWeldBtn),
                     self.weldGraph.transformWeldSymbolType("intermittent")))
        self.staggeredWeldBtn.clicked.connect(
            lambda: (self.select_jointContinuity(self.staggeredWeldBtn),
                     self.weldGraph.transformWeldSymbolType("staggered")))
        self.addWeldBtn.clicked.connect(lambda: (self.saveWeld(), self.accept()))
        self.addWPSBtn.clicked.connect(lambda: self.showPdfViewer(self.wpsDocsViewer))
        # -----------------------------------------------------------------LineEdits scripts---------------------------
        self.firstMaterialLine.editingFinished.connect(
            lambda: self.new_weldObj.info.update({'first_material': self.firstMaterialLine.text()}))
        self.firstMaterialLine.textChanged.connect(lambda x: self.secondMaterialLine.setText(x))
        self.firstJointPartLine.editingFinished.connect(
            lambda: self.new_weldObj.info.update({'first_welded_part': self.firstJointPartLine.text()}))
        self.secondMaterialLine.editingFinished.connect(
            lambda: self.new_weldObj.info.update({'second_material': self.secondMaterialLine.text()}))
        self.secondJointPartLine.editingFinished.connect(
            lambda: self.new_weldObj.info.update({'second_welded_part': self.secondJointPartLine.text()}))
        self.wpsNumberLine.editingFinished.connect(
            lambda: self.new_weldObj.info.update({'wps_number': self.wpsNumberLine.text()}))
        self.weldIDprefixLine.editingFinished.connect(
            lambda: self.new_weldObj.info.update({'weld_id_prefix': self.weldIDprefixLine.text()}))
        self.weldIDsuffixLine.editingFinished.connect(
            lambda: self.new_weldObj.info.update({'weld_id_suffix': self.weldIDsuffixLine.text()}))
        self.wpsMissingCBox.toggled.connect(
            lambda status: (self.wpsNumberLine.setEnabled(False), self.wpsNumberLine.setText("WPS missing checked"),
                            self.new_weldObj.info.update({'wps_number': 'missing'}))
            if status is True else
            self.wpsNumberLine.setEnabled(True))
        self.TMnotSpecifiedRadioBtn.toggled.connect(
            lambda status: (self.new_weldObj.info.update({'testing_methods': []}),
                            [(btn.setEnabled(False), btn.setChecked(False)) for btn in
                             self.weldTestingBtns.findChildren(QPushButton)])
            if status is True else [btn.setEnabled(True) for btn in self.weldTestingBtns.findChildren(QPushButton)])
        self.TMnotSpecifiedRadioBtn.toggle()

        self.addMultipleWeldsBtn.clicked.connect(lambda: self.openMultipleSaveDialog())
        self.discardBtn.clicked.connect(lambda: self.close())
        # -----------------------------------------------------------------UPDATE INFO---------------------------------
        self.mainConstructionLbl.setText(f"{self.parentConstruction.mainConstructionObject.info['name']} \n"
                                         f"{self.parentConstruction.mainConstructionObject.info['tag']}")
        self.parentConstructionLbl.setText(f"{self.parentConstruction.info['name']} \n"
                                           f"{self.parentConstruction.info['tag']}")
        self.showPdfViewer(self.drawingDocsViewer, filepath=self.parentConstruction.pdfDocsPath)

        self.generated_id = \
            str(self.new_weldObj.info[
                    'belonging_construction_tag']) + f'-{self.new_weldObj.update_records_amount() + 1}'
        self.new_weldObj.info['id'] = self.new_weldObj.db_records + 1
        self.weldIDgeneratedLabel.setText(f"/ {self.generated_id} /")

    def showPdfViewer(self, container: QWidget, filepath=None):
        if filepath is None:
            options = QFileDialog.Options()
            filepath, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                      "pdf (*.pdf);;All Files (*)", options=options)
            self.wpsMissingCBox.setChecked(False)
            self.wpsNumberLine.setText(pathlib.Path(filepath).stem)
            self.wps_filepath = filepath
            self.new_weldObj.info.update({'wps_number': self.wpsNumberLine.text()})
        if len(container.findChildren(QLayout)) == 0:
            pdfViewerWidget = pdfviewer.pdfViewerWidget(fr'{filepath}')
            print(f"Creating layout for pdfViewerWidget...")
            layout = QVBoxLayout()
            layout.setObjectName(f'wpsDocsViewerLayout')
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(pdfViewerWidget)
            container.setLayout(layout)
        else:
            old_pdf = container.findChild(pdfviewer.pdfViewerWidget)
            old_pdf.deleteLater()
            old_pdf.hide()
            newPdfViewer = pdfviewer.pdfViewerWidget(fr'{filepath}')
            container.layout().addWidget(newPdfViewer)

    def select_jointType(self, selected_btn: QPushButton):
        # button status changes before execution of this function!
        for JTBtn in self.jointTypesBtnsLayout.findChildren(QPushButton):
            if JTBtn is not selected_btn:
                JTBtn.setStyleSheet("border: 0px")
                JTBtn.setChecked(False)
        if not selected_btn.isChecked():
            selected_btn.setStyleSheet("border: 0px")
            self.new_weldObj.info['joint_type'] = None
           # print(f"Joint type reset: {self.new_weldObj.info['joint_type']}")
        else:
            self.new_weldObj.info['joint_type'] = selected_btn.objectName().replace('JointBtn', ' joint')
            print(f"Joint type saved: {self.new_weldObj.info['joint_type']}")
            selected_btn.setStyleSheet("border: 2px solid rgb(30, 210, 80)")

    def select_testingMethod(self, selected_btn: QPushButton):
        if not selected_btn.isChecked():
            methods_list = self.new_weldObj.info['testing_methods']
            methods_list.remove(selected_btn.text())
            methods_list.sort()
            print(f'{selected_btn.text()} removed from testing methods. New list {methods_list} saved.')
            self.new_weldObj.info['testing_methods'] = methods_list
        else:
            if self.new_weldObj.info['testing_methods'] is None:
                self.new_weldObj.info['testing_methods'] = [selected_btn.text()]
                print(f"Single testing method selected: {self.new_weldObj.info['testing_methods']} has been saved.")
            else:
                methods_list = self.new_weldObj.info['testing_methods']
                methods_list.append(selected_btn.text())
                methods_list.sort()
                self.new_weldObj.info['testing_methods'] = methods_list
                print(f"Selected testing methods: {self.new_weldObj.info['testing_methods']} has been saved")

    def select_jointContinuity(self, selected_btn: QPushButton):
        for btn in self.weldTypeFrame.findChildren(QPushButton):
            if btn is not selected_btn:
                btn.setStyleSheet("background-color : rgb(255, 255, 255)")
                btn.setChecked(False)
            else:
                btn.setStyleSheet("background-color : rgb(30, 210, 80)")
                btn.setChecked(True)
        self.new_weldObj.info['weld_continuity_type'] = selected_btn.text().lower()
        # print(f"Joint continuity type saved: {self.new_weldObj.info['weld_continuity_type']}")

    def saveWeld(self, close_after=True, single_weld=True):
        for key in self.weldGraph.upperWeldData.keys():
            self.new_weldObj.info[key] = self.weldGraph.upperWeldData[key]
        if self.weldGraph.lowerWeldInfo.isVisible():  # if sided weld info is given
            for key in self.weldGraph.lowerWeldData.keys():
                self.new_weldObj.info[key] = self.weldGraph.lowerWeldData[key]
        for key in self.weldGraph.weldBanners.keys():
            self.new_weldObj.info[key] = self.weldGraph.weldBanners[key]
        if type(self.new_weldObj.info['testing_methods']) is not list:
            self.new_weldObj.info['testing_methods'] = self.new_weldObj.info['testing_methods'].split(';')
        if self.new_weldObj.info['testing_methods'] is not None:
            self.new_weldObj.info['testing_methods'] = ';'.join(self.new_weldObj.info['testing_methods'])
        else:
            self.new_weldObj.info['testing_methods'] = None

        try:
            # save the weld ID
            if single_weld:
                full_weldID = \
                    f"{self.weldIDprefixLine.text()}/{self.generated_id}/{self.weldIDsuffixLine.text()} "
                full_weldID = full_weldID.replace(' ', '')
                full_weldID = full_weldID[1::] if full_weldID[0] == '/' else full_weldID
                full_weldID = full_weldID[0:len(full_weldID) - 1:] if full_weldID[-1] == '/' else full_weldID
                self.new_weldObj.sameWeldsAmount = 1
            else:
                full_weldID = self.new_weldObj.info['weld_id_generated']

            self.new_weldObj.info.update({'weld_id_generated': full_weldID})
            self.new_weldObj.save_weld(self.wps_filepath)

            if close_after:
                self.accept()
        except Exception as e:
            print(f"new_weld_SCRIPT | Func(saveWeld) failure | err-> {e}")
            self.reject()

    def openMultipleSaveDialog(self):
        dialog = QDialog()
        dialog.setModal(True)
        layout = QVBoxLayout()
        label = QLabel()
        label.setText('How many the same welds u want to add?')
        lineEdit = QLineEdit()
        layout.addWidget(label, alignment=Qt.AlignCenter)
        layout.addWidget(lineEdit, alignment=Qt.AlignCenter)
        dialogBtns = QDialogButtonBox()
        dialogBtns.setStandardButtons(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        dialogBtns.setEnabled(False)
        lineEdit.setEnabled(True)
        lineEdit.textChanged.connect(lambda: dialogBtns.setEnabled(True))
        dialogBtns.rejected.connect(dialog.reject)
        dialogBtns.accepted.connect(dialog.accept)
        layout.addWidget(dialogBtns, alignment=Qt.AlignCenter)
        dialog.setLayout(layout)
        result = dialog.exec_()
        if result:
            print(f"Dialog {dialog} accepted.")
            self.saveMultipleWelds(lineEdit.text())

    def saveMultipleWelds(self, welds_amount):

        self.saveWeld()

        curr_ID = self.new_weldObj.info['id']
        curr_id_generated = self.new_weldObj.info['weld_id_generated']

        self.new_weldObj.info['same_as_weldID'] = curr_id_generated
        for i in range(int(welds_amount))[1::]:
            incremented_id = curr_id_generated + f"-#{i}"
            # the text in the QLineEdit related to generated ID must be changed in order to properly insert the weld
            self.new_weldObj.info.update({'weld_id_generated': incremented_id})
            print(f"Saving {i} weld...", end=' ')
            self.saveWeld(False, False)
        # Reset the weld obj info in order to point for the unique weld id
        self.new_weldObj.info['same_as_weldID'] = None
        self.new_weldObj.info['id'] = int(curr_ID)
        self.new_weldObj.info['weld_id_generated'] = curr_id_generated
        self.new_weldObj.sameWeldsAmount = int(welds_amount)
        # close the dialog with returned value of 1 (accepted)
        print(f"Added weld -> {self.new_weldObj.info}")
        self.accept()

if __name__ == '__main__':
    from mainWindow import DekiDesktopApp

    app = DekiDesktopApp(sys.argv)
    mainConstruction = db_objects.MainConstruction()
    mainConstruction.load_info(1)
    subConstruction = db_objects.SubConstruction()
    subConstruction.load_info(4)
    # mainWindowObj = NewWeldDialog(parentConstructionObject=subConstruction)
    mainWindow = NewWeldDialog(subConstruction)
    mainWindow.show()

    try:
        sys.exit(app.exec_())
    except:
        print("Exiting the App")
