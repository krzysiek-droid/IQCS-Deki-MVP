import datetime
import logging
import os
import sys

import gfunctions

import pandas
from PyQt5.QtCore import Qt, QRegExp, pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtGui

from Screens import db_objects as dbo

import json

with open(r"D:\CondaPy - Projects\PyGUIs\DekiApp_pyqt5\app_settings.json", 'r') as s:
    file = s.read()
    quality_norms = json.loads(file)['quality_norms']
    tolerances_norms = json.loads(file)['tolerances_norms']
    srv_files_filepath = json.loads(file)['srv_files_filepath']

with open(r"D:\CondaPy - Projects\PyGUIs\DekiApp_pyqt5\db_settings.json", 'r') as o:
    file = o.read()
    realWelds_db_cols = json.loads(file)['realWelds_columns']


def save_dataframe_to_textfile(dataframe, filename):
    dataframe.to_csv(filename, sep='\t', index=False)


class ConfirmationButton(QPushButton):
    enabled = pyqtSignal()

    #   Function overloading
    def setEnabled(self, a0: bool) -> None:
        super(ConfirmationButton, self).setEnabled(a0)
        if not a0:
            self.setIcon(QtGui.QIcon())
            self.setText('')
        else:
            self.setIcon(QtGui.QIcon(r':/Icons/Icons/mouse-pointer.svg'))
            self.setText('Click to confirm')
            self.enabled.emit()


class ConstructionReleaseWindow(QDialog):
    def __init__(self, constructionObject: dbo.MainConstruction):
        super(ConstructionReleaseWindow, self).__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)
        # self.setWindowFlags(Qt.FramelessWindowHint)

        uic.properties.logger.setLevel(logging.WARNING)
        uic.uiparser.logger.setLevel(logging.WARNING)
        uic.loadUi(r'constructionReleaseWindow_UI.ui', self)
        #   -------------------------------- BUTTONS
        self.closeBtn.clicked.connect(self.close)

        #   ------------------------------------------------------------------- SCREEN MANAGER
        from inspectionPlannerWindow_SCRIPT import CustomStackedWidget
        self.screenManager = CustomStackedWidget(self)
        self.mainLayout.addWidget(self.screenManager)

        first_screen = ConstructionReleaseScreen(self.screenManager, constructionObject, self)
        self.screenManager.addWidget(first_screen)

    def centerWindow(self, window: QWidget = None):
        qtRectangle = self.frameGeometry() if window is None else window.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        centerPoint.setY(centerPoint.y() - 50)
        centerPoint.setX(centerPoint.x() - 30)

        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())


class ConstructionReleaseScreen(QDialog):
    def __init__(self, screenManager_ref, constructionObject: dbo.MainConstruction,
                 parentWindow: ConstructionReleaseWindow):

        super(ConstructionReleaseScreen, self).__init__()
        self.mainConstructionObject = constructionObject
        self.screenManager = screenManager_ref
        self.setObjectName(f'ConstructionReleaseScreen')
        self.confirmedTestingLevels = {'vt': 0, 'pt': 0, 'mt': 0, 'ut': 0, 'rt': 0, 'lt': 0}
        self.checklist = {'seriesNumberLine': False,
                          'confirmationBtnsFrame': False}

        self.parentWindow = parentWindow

        uic.loadUi(r'constructionReleaseScreen_UI.ui', self)

        # --- init UI
        self.constructPicture.setPixmap(self.mainConstructionObject.picture.scaled(260, 230, 1, 1))
        self.seriesTagLine.setText(self.mainConstructionObject.info['serial_number'])
        self.weldsBtn.setText(f"127 \n Welds")
        self.constructionsBtn.setText(f"3 \n Constructions")
        self.cadsBtn.setText(f"0 \n CADs missing")
        self.docsBtn.setText(f"0 \n DOCs missing")
        self.wpsesBtn.setText(f"2 \n WPS missing")
        self.qualityNormLine.setText(self.mainConstructionObject.info['quality_norm'])
        self.qualityClassLine.setText(self.mainConstructionObject.info['quality_class'])
        self.tollerancesNormLine.setText(self.mainConstructionObject.info['tolerances_norm'])
        self.tollerancesLevelLine.setText(self.mainConstructionObject.info['tolerances_level'])
        self.constructNameLbl.setText(self.mainConstructionObject.info['name'])
        self.constructTagLbl.setText(self.mainConstructionObject.info['tag'])

        subcontractors = 0
        if self.mainConstructionObject.info['subcontractor'] != 'N/A':
            self.cooperationLine.setText(self.mainConstructionObject.info['subcontractor'])
        else:
            self.cooperationLine.setText('None')

        #   ---------------------------------------- BUTTONS -------------------------------
        #   -- Testing Level Confirmation buttons --
        self.resetSizeBtn.hide()

        for btn in self.confirmationBtnsFrame.findChildren(QPushButton):
            btn.setEnabled(False)
            btn.setText("")

        self.vtLvlConfirmBtn.clicked.connect(lambda postClickChecked:
                                             self.confirm_testing_level(self.vtLvlConfirmBtn, postClickChecked))
        self.ptLvlConfirmBtn.clicked.connect(lambda postClickChecked:
                                             self.confirm_testing_level(self.ptLvlConfirmBtn, postClickChecked))
        self.mtLvlConfirmBtn.clicked.connect(lambda postClickChecked:
                                             self.confirm_testing_level(self.mtLvlConfirmBtn, postClickChecked))
        self.utLvlConfirmBtn.clicked.connect(lambda postClickChecked:
                                             self.confirm_testing_level(self.utLvlConfirmBtn, postClickChecked))
        self.rtLvlConfirmBtn.clicked.connect(lambda postClickChecked:
                                             self.confirm_testing_level(self.rtLvlConfirmBtn, postClickChecked))
        self.ltLvlConfirmBtn.clicked.connect(lambda postClickChecked:
                                             self.confirm_testing_level(self.ltLvlConfirmBtn, postClickChecked))
        self.resetSizeBtn.clicked.connect(self.resetSizeInput)

        self.discardBtn.clicked.connect(self.closeFunc)

        self.releaseBtn.clicked.connect(self.releaseConstruction)

        #   ---------------------------------------- FUNCTIONS CALLS -----------------------
        self.checkConstructionData()
        self.check_assigned_tests()
        self.load_lineEdits()

        parentWindow.centerWindow(self)
        print(f"Screen {self} - {self.objectName()} loaded.")

    def load_lineEdits(self):
        #   ---------------------------------------- LINE EDITS -------------------------------
        validator = QtGui.QIntValidator()
        self.seriesNumberLine.setValidator(validator)
        self.seriesNumberLine.editingFinished.connect(self.update_series_amount)

        prev_series_size = self.mainConstructionObject.info['series_size']
        if prev_series_size is not None or len(prev_series_size) != 0:
            self.seriesNumberLine.setText(f"{self.mainConstructionObject.info['series_size']}")
            self.update_series_amount()

        validator = QtGui.QRegExpValidator(QRegExp("^[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)$"))
        self.vtLine.setValidator(validator)
        self.ptLine.setValidator(validator)
        self.mtLine.setValidator(validator)
        self.utLine.setValidator(validator)
        self.rtLine.setValidator(validator)
        self.ltLine.setValidator(validator)

        self.vtLine.clicked.connect(lambda: self.clear_line(self.vtLine))
        self.vtLine.editingFinished.connect(lambda: self.change_testing_level(self.vtLine))
        self.vtLine.textChanged.connect(lambda: (self.vtLvlConfirmBtn.setChecked(False),
                                                 self.confirm_testing_level(self.vtLvlConfirmBtn, False)))

        self.ptLine.clicked.connect(lambda: self.clear_line(self.ptLine))
        self.ptLine.editingFinished.connect(lambda: self.change_testing_level(self.ptLine))
        self.ptLine.textChanged.connect(lambda: (self.ptLvlConfirmBtn.setChecked(False),
                                                 self.confirm_testing_level(self.ptLvlConfirmBtn, False)))

        self.mtLine.clicked.connect(lambda: self.clear_line(self.mtLine))
        self.mtLine.editingFinished.connect(lambda: self.change_testing_level(self.mtLine))
        self.mtLine.textChanged.connect(lambda: (self.mtLvlConfirmBtn.setChecked(False),
                                                 self.confirm_testing_level(self.mtLvlConfirmBtn, False)))

        self.utLine.clicked.connect(lambda: self.clear_line(self.utLine))
        self.utLine.editingFinished.connect(lambda: self.change_testing_level(self.utLine))
        self.utLine.textChanged.connect(lambda: (self.utLvlConfirmBtn.setChecked(False),
                                                 self.confirm_testing_level(self.utLvlConfirmBtn, False)))

        self.rtLine.clicked.connect(lambda: self.clear_line(self.rtLine))
        self.rtLine.editingFinished.connect(lambda: self.change_testing_level(self.rtLine))
        self.rtLine.textChanged.connect(lambda: (self.rtLvlConfirmBtn.setChecked(False),
                                                 self.confirm_testing_level(self.rtLvlConfirmBtn, False)))

        self.ltLine.clicked.connect(lambda: self.clear_line(self.ltLine))
        self.ltLine.editingFinished.connect(lambda: self.change_testing_level(self.ltLine))
        self.ltLine.textChanged.connect(lambda: (self.ltLvlConfirmBtn.setChecked(False),
                                                 self.confirm_testing_level(self.ltLvlConfirmBtn, False)))

    # Function for series size QLineEdit functionality      -- connected (eF) to QLineEdit, seriesSizeLine
    def update_series_amount(self):
        if len(self.seriesNumberLine.text()) > 0:
            try:
                int(self.seriesNumberLine.text())
                self.checklist.update({'seriesNumberLine': True})
                self.seriesNumberLine.setConfirmed(True)
                self.resetSizeBtn.show()
            except ValueError:
                print('Integer value needed.')
        self.validate_inputs()

    def resetSizeInput(self):
        self.seriesNumberLine.clear()
        self.seriesNumberLine.setConfirmed(False)
        self.resetSizeBtn.hide()
        self.checklist.update({'seriesNumberLine': False})
        self.validate_inputs()

    #   Function to check completeness of data for construction (whether CAD or Docs are missing)
    def checkConstructionData(self):
        #   Check amount of welds
        welds_amount = \
            self.mainConstructionObject.db.check_records_number(
                f"{self.mainConstructionObject.info['serial_number']}_modelWelds")
        self.weldsBtn.setText(f'{welds_amount} \n Welds')

        #   Check amount of sub constructions
        sub_constructions = \
            self.mainConstructionObject.db.table_into_DF(
                f"{self.mainConstructionObject.info['serial_number']}_SubConstructions")
        self.constructionsBtn.setText(f'{len(sub_constructions)} \n Constructions')

        #   Check missing files for CAD models and Documentation
        files_missing = {'cads': 0, 'docs': 0}
        for index, construct in sub_constructions.iterrows():
            constructionObject = dbo.SubConstruction(self.mainConstructionObject)
            constructionObject.load_info(construct['id'])
            check_status = constructionObject.check_files()
            if not check_status['CAD']:
                files_missing['cads'] = files_missing['cads'] + 1
            if not check_status['Docs']:
                files_missing['docs'] = files_missing['docs'] + 1
        if files_missing['cads'] == 0:
            self.cadsBtn.setText(f"{files_missing['cads']} \n CAD missing")
            self.cadsBtn.setChecked(False)
        else:
            self.cadsBtn.setText(f"{files_missing['cads']} \n CAD missing")
            self.cadsBtn.setChecked(True)

        if files_missing['docs'] == 0:
            self.docsBtn.setText(f"{files_missing['docs']} \n docs missing")
            self.docsBtn.setChecked(False)
        else:
            self.docsBtn.setText(f"{files_missing['docs']} \n docs missing")
            self.docsBtn.setChecked(True)

        #   Check the existence of WPS docs (pdf files)
        welds_list = self.mainConstructionObject.db.table_into_DF(
            f"{self.mainConstructionObject.info['serial_number']}_modelWelds")
        missing_WPSes = 0
        from Screens.db_objects import srv_wps_files_path as WPS_path
        for index, weld_as_DFseries in welds_list.iterrows():
            if not os.path.isfile(WPS_path + fr'\{weld_as_DFseries["wps_number"]}.pdf'):
                missing_WPSes += 1
        if missing_WPSes == 0:
            self.wpsesBtn.setText(f"{missing_WPSes} \n WPS missing")
            self.wpsesBtn.setChecked(False)
        else:
            self.wpsesBtn.setText(f"{missing_WPSes} \n WPS missing")
            self.wpsesBtn.setChecked(True)

    # Function for initialization to check tests assigned to welds      -- INIT
    def check_assigned_tests(self):
        db_content = self.mainConstructionObject.db.table_into_DF(
            f"{self.mainConstructionObject.info['serial_number']}_modelWelds")
        for method_label in self.testsFoundFrame.findChildren(QLabel):
            method: str = method_label.objectName()[:2].upper()
            method_count = ';'.join(db_content['testing_methods'].values.tolist()).split(';').count(method)
            method_label.setText(f"{method_count} welds assigned. \n"
                                 f"({round((method_count / len(db_content) * 100), 1)}%)")
            related_lineEdit = self.testingLevelsGroupBox.findChild(QLineEdit, f"{method.lower()}Line")
            related_lineEdit.setText(f"{round((method_count / len(db_content) * 100), 1)}")
            self.change_testing_level(related_lineEdit)
            confirmBtn: ConfirmationButton = self.confirmationBtnsFrame.findChild(QPushButton,
                                                                                  f"{method.lower()}LvlConfirmBtn")
            if method_count > 0 and confirmBtn is not None:
                confirmBtn.setEnabled(True)
            else:
                confirmBtn.setEnabled(False)
                related_lineEdit.setNeutral()

    # applied to QPushButton for testing level confirmation      -- INIT
    def confirm_testing_level(self, method_relatedConfirmBtn: QPushButton, hasBeenChecked):
        method = method_relatedConfirmBtn.objectName()[:2]
        relatedLineEdit: QLineEdit = self.testingLevelsGroupBox.findChild(QLineEdit,
                                                                          f"{method}Line")
        if hasBeenChecked:
            print(f'Confirmed - {method.upper()} - {relatedLineEdit.text()}%')
            method_relatedConfirmBtn.setText(f"Confirmed.")
            method_relatedConfirmBtn.setIcon(QtGui.QIcon(r':/Icons/Icons/user-check.svg'))
            relatedLineEdit.setConfirmed(True)
            confirmedValue = int(float(relatedLineEdit.text().replace(' %', '')))
            self.confirmedTestingLevels.update({f'{method}': confirmedValue})
        else:
            method_relatedConfirmBtn.setText(f"Click to confirm")
            method_relatedConfirmBtn.setIcon(QtGui.QIcon(r':/Icons/Icons/mouse-pointer.svg'))
            self.confirmedTestingLevels.update({f'{method}': 0})
            relatedLineEdit.setConfirmed(False)

        self.validate_inputs()

    # Functionality of testing level lineEdits        -- connected (eF) to QLineEdits, all in testingLevelsGroupBox
    def change_testing_level(self, methodRelated_lineEdit):
        method: str = methodRelated_lineEdit.objectName()[:2].lower()
        relatedConfirmBtn: QPushButton = self.confirmationBtnsFrame.findChild(QPushButton, f"{method}LvlConfirmBtn")

        if type(methodRelated_lineEdit.text()) == str and float(methodRelated_lineEdit.text()) > 0:
            input_text = methodRelated_lineEdit.text()
            methodRelated_lineEdit.setText(f"{float(input_text)} %")
            self.confirmedTestingLevels.update({f'{method}': 0})
            methodRelated_lineEdit.setConfirmed(False)
            methodRelated_lineEdit.setValue(float(input_text))
            self.validate_inputs()

            if not relatedConfirmBtn.isEnabled() and float(input_text) != 0:
                relatedConfirmBtn.setEnabled(True)
                self.confirm_testing_level(relatedConfirmBtn, False)

        else:
            methodRelated_lineEdit.setNeutral()
            relatedConfirmBtn.setEnabled(False)
            methodRelated_lineEdit.setValue(0)

    # Functionality of testing level lineEdits        -- connected (clicked) to QLineEdits, all in testingLevelsGroupBox
    def clear_line(self, lineEdit_ref: QLineEdit):
        method: str = lineEdit_ref.objectName()[:2]
        relatedConfirmBtn = self.confirmationBtnsFrame.findChild(QPushButton, f"{method}LvlConfirmBtn")
        lineEdit_ref.clear()
        lineEdit_ref.setNeutral()
        relatedConfirmBtn.setEnabled(False)
        lineEdit_ref.setValue(0)
        self.validate_inputs()

    def validate_inputs(self):
        lineEdits = self.testingLevelsGroupBox.findChildren(QLineEdit)
        editedLines = [lineEdit for lineEdit in lineEdits if lineEdit.hasValue is True]

        if all([editedLine.isConfirmed for editedLine in editedLines]) and self.checklist['seriesNumberLine']:
            self.checklist.update({"confirmationBtnsFrame": True})
            confirmedTestingLevels = {
                f'{editedLine.objectName().replace("Line", "")}': editedLine.text().replace(' %', '')
                for editedLine in editedLines if editedLine.isConfirmed is True}
            self.releaseBtn.setEnabled(True)
        else:
            self.checklist.update({"confirmationBtnsFrame": False})
            self.releaseBtn.setEnabled(False)

    def closeFunc(self):
        self.parentWindow.close()
        from inspectionPlannerWindow_SCRIPT import InspectionPlannerWindow
        nw = InspectionPlannerWindow()
        nw.show()

    def releaseConstruction(self):
        if False in self.checklist.values():
            # Check whether all required inputs were given - if not print the unsatisfied conditions
            print(f"Cannot release construction -> {' - '.join(key for key,value in self.checklist.items() if not value)}")
        else:
            try:
                mConstruct_id = int(self.mainConstructionObject.info['id'])
                self.mainConstructionObject.load_info(mConstruct_id)
                modelWelds_df: pandas.DataFrame = self.mainConstructionObject.modelWelds_df
                subConstructions_df = self.mainConstructionObject.subConstructions_df
                series_size = int(self.seriesNumberLine.text())

                # create a DataFrame with real welds
                realWelds_df = pandas.DataFrame(columns=realWelds_db_cols)
                # First loop for the number of constructions in a given Series
                print(f"------------------------", end=' ')
                print(f"Starting to generate the realWelds table long for {len(modelWelds_df) * series_size} rows")
                st_time = datetime.datetime.now()
                realWeld_rows = []
                for construction_increment in range(series_size + 1)[1::]:
                    # 2nd loop for the welds in the construction
                    for index, modelWeld_info in modelWelds_df.iterrows():
                        parent_construction_info: pandas.DataFrame = \
                            subConstructions_df[subConstructions_df['id'] == modelWeld_info[
                                'belonging_construction_ID']].iloc[0]
                        parent_construction_info = parent_construction_info.to_dict()
                        realWeld_key = realWelds_db_cols
                        parent_serialNo = parent_construction_info['serial_number']
                        # for keys meaning refer to db_settings.json
                        realWeld_row = {realWeld_key[0]: len(realWeld_rows) + 1,
                                        realWeld_key[1]: parent_construction_info['serial_number'],
                                        realWeld_key[2]: parent_construction_info['tag'],
                                        realWeld_key[3]: construction_increment,
                                        realWeld_key[4]: f"{parent_serialNo}-{construction_increment}-"
                                                         f"{modelWeld_info['id']}",
                                        realWeld_key[5]: modelWeld_info['id'],
                                        realWeld_key[6]: modelWeld_info['weld_id_generated']}
                        if bool(modelWeld_info['same_as_weldID']):
                            realWeld_row.update({'modelWeld_generatedID': modelWeld_info['same_as_weldID']})
                        realWeld_rows.append(realWeld_row)
                realWelds_df = pandas.concat([realWelds_df, pandas.DataFrame(realWeld_rows)])
                generate_time = st_time - datetime.datetime.now()
                print(f"Generation ended by {-1 * generate_time.total_seconds()}")
                save_dataframe_to_textfile(realWelds_df, r"D:\CondaPy - Projects\PyGUIs\DekiApp_pyqt5\teste_df.txt")

                self.mainConstructionObject.releaseConstruction(realWelds_df)

                self.accept()
            except Exception as exc:
                print(gfunctions.log_exception(exc))
                return 0


if __name__ == '__main__':
    from mainWindow import DekiDesktopApp

    app = DekiDesktopApp(sys.argv)

    from inspectionPlannerWindow_SCRIPT import InspectionPlannerWindow

    ins = InspectionPlannerWindow()

    construction = dbo.MainConstruction()
    construction.load_info(1)

    mainWindow = ConstructionReleaseWindow(construction)
    mainWindow.show()

    try:
        sys.exit(app.exec_())
    except:
        print("Exiting the App")
