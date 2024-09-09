from datetime import datetime
import sys

from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from Screens import db_objects
import gnrl_database_con
import new_rootConstruction as newConstructionScreen

import re


def last_three_letters(s):
    """
    Returns the last three letters from a given string after filtering out non-letter characters.
    Args:
        s (str): The string to extract the letters from.
    Returns:
        A string containing the last three letters from the input string, or None if no letters are found.
    """
    # Use regular expression to match only letters
    letters = re.findall('[a-zA-Z]', s)
    # If there are at least three letters, return the last three letters
    if len(letters) >= 3:
        return ''.join(letters[-3:])
    # Otherwise, return None
    else:
        return None


class NewSubconstructionDialog(QDialog):
    # parentConstructionObject has to be a database new_screen_ref class -> db_object.MainConstruction
    def __init__(self, parentConstruction: db_objects.Construction = None):
        # TODO: Add database connection parse
        super(NewSubconstructionDialog, self).__init__()
        self.new_subConstruction = None
        self.db: gnrl_database_con.Database = QApplication.instance().database
        self.pdfViewerWidget = None
        self.cadModelViewWidget = None
        self.parentConstruction = parentConstruction
        loadUi(r'new_subconstruction_UI.ui', self)

        #   ------------------------------------Hidden content----------------------------------------------------------
        self.newSubconstructionSubcontractor.hide()
        self.newSubconstructionSubcontractorContact.hide()

        # ----------------------------------------Screen boarding
        # scripts-----------------------------------------------------
        self.parentConstructionPicture.setPixmap(self.parentConstruction.picture.scaled(250, 250, 1, 1))
        self.parentConstructNameLabel.setText(self.parentConstruction.info['name'])
        self.parentConstructTagLabel.setText(self.parentConstruction.info['tag'])
        self.parentConstructNumberLabel.setText(self.parentConstruction.info['serial_number'])
        self.parentConstructOwnerLabel.setText(self.parentConstruction.info['owner'])
        self.parentConstructMaterialLabel.setText(self.parentConstruction.info['material'])
        self.parentConstructLocalizationLabel.setText(self.parentConstruction.info['localization'])
        self.parentConstructAdditionalInfoLabel.setText(self.parentConstruction.info['additional_info'])
        self.parentConstructTypeLabel.setText(self.parentConstruction.info['construct_type'])
        self.parentConstructQualityNormLabel.setText(self.parentConstruction.info['quality_norm'])
        self.parentConstructQualityClassLabel.setText(self.parentConstruction.info['quality_class'])
        self.parentConstructTolerancesNormLabel.setText(self.parentConstruction.info['tolerances_norm'])
        self.parentConstructTolerancesLevelLabel.setText(self.parentConstruction.info['tolerances_level'])
        self.parentConstructSubcontractorLabel.setText(self.parentConstruction.info['subcontractor'])
        self.parentConstructSubcontractorContactLabel.setText(self.parentConstruction.info['sub_contact'])

        subConstructions_number = self.db.table_length(
            f"{self.parentConstruction.mainConstructionObject.info['serial_number']}_SubConstructions")
        self.newSubconstructionSerialNo.setText(self.parentConstruction.info['serial_number'] +
                                                f'_SC0{subConstructions_number}')
        # ----------------------------------------Button
        # scripts--------------------------------------------------------------
        self.showParentConstructionCadModel.clicked.connect(lambda: print(f'show parent CAD'))
        self.goToParentConstructionPreview.clicked.connect(lambda: print(f'going back to parent construction'))
        self.showParentConstructionDocs.clicked.connect(lambda: print(f'showing parent construction 2D documentary'))
        self.newSubconstructionAddCadBtn.clicked.connect(lambda: self.showStepModel())
        self.newSubconstructionAddDocsBtn.clicked.connect(lambda: self.showPdfViewer())

        self.newSubconstructionAddSubcontractorBtn.toggled.connect(lambda: (self.newSubconstructionSubcontractor.show(),
                                                                            self.newSubconstructionSubcontractorContact.show()) if self.newSubconstructionAddSubcontractorBtn.isChecked()
        else (self.newSubconstructionSubcontractor.hide(), self.newSubconstructionSubcontractorContact.hide()))

        self.newSubconstructionAddSubconstruction.clicked.connect(lambda: self.addSubConstruction())
        #   -----------------------------------------Signals------------------------------------------------------------

        #   ------------------------------------ComboBoxes scripts------------------------------------------------------
        self.newSubconstructionTypeCombo.addItems(newConstructionScreen.quality_norms.keys())
        self.newSubconstructionTypeCombo.activated.connect(
            lambda: self.quality_combos_activate(self.newSubconstructionTypeCombo.currentText()))
        self.newSubconstructionQualityNormCombo.addItems(
            norm[0] for norm in newConstructionScreen.quality_norms.values())
        self.quality_combos_activate(self.newSubconstructionTypeCombo.currentText())
        self.newSubconstructionTolerancesNormCombo.addItems(newConstructionScreen.tolerances_norms.keys())
        self.newSubconstructionTolerancesNormCombo.activated.connect(lambda: self.tolerances_combos_activate(
            self.newSubconstructionTolerancesNormCombo.currentText()))
        self.tolerances_combos_activate(self.newSubconstructionTolerancesNormCombo.currentText())

    def showStepModel(self):
        # define filechooser dialog
        options = QFileDialog.Options()
        # open filechooser dialog and save selection
        fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "stp (*.stp);;All Files (*);;step (*.step)", options=options)
        if fileName:
            from new_rootConstruction import CadViewerExtended
            if not self.cadModelViewWidget:
                self.cadModelViewWidget = CadViewerExtended(fileName)
                # Create Layout for cadModelViewWidget
                grid = QVBoxLayout()
                grid.addWidget(self.cadModelViewWidget)
                self.cadViewerContainer.setLayout(grid)
            else:
                old_viewer = self.cadViewerContainer.findChild(CadViewerExtended)
                old_viewer.deleteLater()
                old_viewer.hide()
                # Replace old Viewer with new Viewer with new CAD model
                self.cadModelViewWidget = CadViewerExtended(fileName)
                self.cadViewerContainer.layout().addWidget(self.cadModelViewWidget)
        else:
            pass

    def showPdfViewer(self):
        from Screens import pdfViewWidget_SCRIPT as pdfviewer
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "pdf (*.pdf);;All Files (*)", options=options)
        if fileName:
            if not self.pdfViewerWidget:
                self.pdfViewerWidget = pdfviewer.pdfViewerWidget(fileName)
                layout = QVBoxLayout()
                layout.addWidget(self.pdfViewerWidget)
                self.docsViewerContainer.setLayout(layout)

            else:
                old_viewer = self.docsViewerContainer.findChild(pdfviewer.pdfViewerWidget)
                old_viewer.deleteLater()
                old_viewer.hide()
                # Replace old Viewer with new Viewer with new CAD model
                self.cadModelViewWidget = pdfviewer.pdfViewerWidget(fileName)
                self.docsViewerContainer.layout().addWidget(self.cadModelViewWidget)

    def addSubConstruction(self):
        try:
            print('adding to database...')
            self.new_subConstruction = db_objects.SubConstruction(
                mainConstructionObject=self.parentConstruction.mainConstructionObject)

            self.new_subConstruction.info = \
                {'id': self.new_subConstruction.update_records_amount() + 1,
                 'parent_construction_id': int(self.parentConstruction.info['id']) if type(
                     self.parentConstruction) is not
                                                                                      db_objects.MainConstruction else None,
                 'main_construction_id': self.parentConstruction.info['id'] if type(self.parentConstruction) is
                                                                               db_objects.MainConstruction else
                 self.parentConstruction.info['main_construction_id'],
                 'name': self.newSubconstructionName.text(),
                 'tag': self.newSubconstructionTag.text(),
                 'serial_number': self.newSubconstructionSerialNo.text(),
                 'owner': self.newSubconstructionOwner.text(),
                 'localization': self.newSubconstructionLocalization.text(),
                 'material': self.newSubconstructionMainMaterial.text(),
                 'additional_info': "N/A" if len(self.newSubconstructionAdditionalInfoLine.text()) == 0 else
                 self.newSubconstructionAdditionalInfoLine.text(),
                 'subcontractor': "N/A" if len(self.newSubconstructionSubcontractor.text()) == 0 else
                 self.newSubconstructionSubcontractor.text(),
                 'sub_contact': "N/A" if len(self.newSubconstructionSubcontractorContact.text()) == 0 else
                 self.newSubconstructionSubcontractorContact.text(),
                 'construct_type': str(self.newSubconstructionTypeCombo.currentText()),
                 'quality_norm': str(self.newSubconstructionQualityNormCombo.currentText()),
                 'quality_class': str(self.newSubconstructionQualityClassCombo.currentText()),
                 'tolerances_norm': str(self.newSubconstructionTolerancesNormCombo.currentText()),
                 'tolerances_level': str(self.newSubconstructionTolerancesLevelCombo.currentText()),
                 'tier': int(self.parentConstruction.info['tier']) + 1 if type(self.parentConstruction) is
                                                                          db_objects.SubConstruction else 1,
                 'update_time': f'{datetime.now().strftime("%Y-%m-%d %H:%M")}',
                 'update_by': 'admin'}
        except Exception as e:
            print(f"Construction info gathering error -> {e}")
            self.reject()

        try:
            self.new_subConstruction.picture = self.cadModelViewWidget.screenshot
            self.new_subConstruction.pdfDocsPath = self.pdfViewerWidget.filepath
            self.new_subConstruction.stpModelPath = self.cadModelViewWidget.filepath
            print(f'SubConstruction {self} creation succeeded. ------------ ', end='')
        except Exception as e:
            print(f"Construction files save error -> {e}")
            self.reject()

        self.new_subConstruction.save_subConstruction()
        print("SubConstruction added to database successfully.")
        self.accept()

    def quality_combos_activate(self, chosen):
        self.newSubconstructionQualityNormCombo.setCurrentText(newConstructionScreen.quality_norms[chosen][0])
        self.newSubconstructionQualityClassCombo.clear()
        self.newSubconstructionQualityClassCombo.setEnabled(True)
        self.newSubconstructionQualityClassCombo.addItems(
            newConstructionScreen.quality_norms[chosen][1]) if type(
            newConstructionScreen.quality_norms[chosen][
                1]) == list else self.newSubconstructionQualityClassCombo.addItem(
            newConstructionScreen.quality_norms[chosen][1])

    def tolerances_combos_activate(self, chosen):
        self.newSubconstructionTolerancesLevelCombo.clear()
        self.newSubconstructionTolerancesLevelCombo.setEnabled(True)
        self.newSubconstructionTolerancesLevelCombo.addItems(newConstructionScreen.tolerances_norms[chosen])


#   ----------------------------------------Main script (for Screen testing purposes)-----------------------------------
if __name__ == '__main__':
    from mainWindow import DekiDesktopApp

    app = DekiDesktopApp(sys.argv)

    # mainWindowObj = CadViewerExtended("../DekiResources/Zbiornik LNG assembly.stp")
    dummy_constructionObject = db_objects.MainConstruction()
    dummy_constructionObject.load_info(2)
    mainWindow = NewSubconstructionDialog(parentConstruction=dummy_constructionObject)
    mainWindow.show()

    try:
        sys.exit(app.exec_())
    except:
        print("Exiting the App")
