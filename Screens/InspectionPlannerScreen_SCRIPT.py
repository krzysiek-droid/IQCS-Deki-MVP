import sys

from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt

from Screens import db_objects, db_objects as dbo


# resources_rc has to be imported here, even if it is not used directly in code, dunno why


class InspectionPlannerScreen(QWidget):
    def __init__(self):
        try:
            super().__init__()
            self.mainConstructionObject = None
            loadUi(r'InspectionPlannerScreen_UI.ui', self)
            self.currentListItemID = None
            self.mainWindowInstance = QApplication.instance().inspectionPlannerWindow
            if self.mainWindowInstance is None:
                print(f"InspectionPlannerScreen_SCRIPT")
                raise SystemError
            # Screen loading scripts
            self.goToConstructionBtn.setEnabled(False)
            # open database connection
            self.db = QApplication.instance().database
            # defining the list of constructions widget
            self.scrolledContentWidget = None
            self.scrolledContentLayout = None

            self.constructionsObjects = self.mainWindowInstance.cached_data['mainConstructions_objects']

            # Load list of constructions
            self.loadRootConstructionsList()
            # --------------------------------------------------------------------------button allocations

            self.addConstructionBtn.clicked.connect(self.add_new_construction)

        except Exception as e:
            print(f"InspectionPlannerScreen_SCRIPT | InspectionPlannerScreen __init__ failure | err-> {e}")

    def loadRootConstructionsList(self):
        self.scrolledContentWidget = QWidget()
        self.scrolledContentWidget.setObjectName('scrolledContentWidget')
        self.scrolledContentLayout = QVBoxLayout()
        self.scrolledContentLayout.setSpacing(1)
        self.scrolledContentLayout.setAlignment(Qt.AlignTop)

        if self.constructionsObjects is None:
            db_tableLength = len(self.db.table_into_DF(f'{db_objects.database_settings["company"]}_mainConstructions'))
            for constructionID in range(db_tableLength):
                constructionObject = dbo.MainConstruction()
                constructionObject.load_info(int(constructionID) + 1)
                listItem = CustomListItem(self, constructionObject)
                self.scrolledContentLayout.addWidget(listItem, alignment=Qt.AlignTop)
        else:
            for construction_object in self.constructionsObjects:
                listItem = CustomListItem(self, construction_object)
                self.scrolledContentLayout.addWidget(listItem, alignment=Qt.AlignTop)

        self.scrolledContentWidget.setLayout(self.scrolledContentLayout)
        self.scrollArea.setWidget(self.scrolledContentWidget)

    def refresh_scrollArea(self):
        self.scrolledContentWidget.deleteLater()
        QApplication.instance().processEvents()
        self.loadConstructionsList()

    def updateRightMenu(self, mainConstructionObj):
        self.mainConstructionObject = mainConstructionObj

        # Cache selected mainConstructionObject
        self.mainWindowInstance.cached_data.update({'mainConstructionObject': self.mainConstructionObject})

        from construction_preview_SCRIPT import MainConstructionDialog
        self.goToConstructionBtn.clicked.connect(
            lambda: self.mainWindowInstance.stackedWidget.changeScreen_withSplash(MainConstructionDialog,
                                                                                [self.mainConstructionObject]))

        self.currentListItemID = mainConstructionObj.info['id']
        self.constructionName.setText(mainConstructionObj.info['name'])
        self.constructionTag.setText(mainConstructionObj.info['tag'])
        self.constructionSerialNo.setText(str(mainConstructionObj.info['serial_number']))
        self.constructionOwner.setText(mainConstructionObj.info['owner'])
        self.constructionType.setText(mainConstructionObj.info['construct_type'])
        self.constructionQualityNorm.setText(mainConstructionObj.info['quality_norm'])
        self.constructionQualityClass.setText(mainConstructionObj.info['quality_class'])
        self.constructionTolerancesNorm.setText(mainConstructionObj.info['tolerances_norm'])
        self.constructionTolerancesLevel.setText(mainConstructionObj.info['tolerances_level'])
        self.constructionCoopBody.setText(mainConstructionObj.info['subcontractor'])
        self.constructionCoopContact.setText(mainConstructionObj.info['sub_contact'])
        self.constructionPicLarge.setPixmap(
            mainConstructionObj.picture.scaledToHeight(250, mode=Qt.SmoothTransformation))
        self.goToConstructionBtn.setEnabled(True)

    def add_new_construction(self):
        from new_rootConstruction import NewConstructDialog
        try:
            dialog = NewConstructDialog()
            result = dialog.exec_()
            if result:
                listItem = CustomListItem(self, dialog.new_constructionObj)
                self.scrolledContentLayout.addWidget(listItem, alignment=Qt.AlignTop)
        except Exception as e:
            print(f"New construction dialog error -> {e}")


class CustomListItem(QWidget):
    def __init__(self, parentScreenObj: InspectionPlannerScreen, loadedConstructionObject: dbo.MainConstruction):
        super(CustomListItem, self).__init__()
        # set attribute that deletes the instance of this class on closeEvent
        self.setAttribute(Qt.WA_DeleteOnClose)
        loadUi(r'MainConstructionListItem_UI.ui', self)
        self.constructionID = loadedConstructionObject.info['id']
        self.parentScreen = parentScreenObj
        self.constructionObj = loadedConstructionObject
        self.db = loadedConstructionObject.db

        self.mouseReleaseEvent = lambda event: self.parentScreen.updateRightMenu(self.constructionObj)

        self.releaseConstructionBtn.clicked.connect(self.releaseConstruction)

        self.assignInfoToWidgets()

    def releaseConstruction(self):
        from constructionReleaseScreen_SCRIPT import ConstructionReleaseWindow
        dialog = ConstructionReleaseWindow(self.constructionObj)
        self.parentScreen.mainWindowInstance.close()
        dialog.show()

    def assignInfoToWidgets(self):
        self.constructionTag.setText(self.constructionObj.info["tag"])
        self.constructionName.setText(self.constructionObj.info['name'])
        self.constructionPicture.setPixmap(
            self.constructionObj.picture.scaledToHeight(120, mode=Qt.SmoothTransformation))
        self.seriesSize.setText(self.constructionObj.info['serial_number'])
        self.clientLbl.setText(self.constructionObj.info['owner'])
        in_preparation_style = 'color: rgb(255, 255, 255);' \
                               'font: 75 bold 9pt "Arial";' \
                               'background-color: rgb(250,150,0);' \
                               'border-radius: 10px;'
        released_style = 'color: rgb(255,255,255);' \
                         'font: 75 bold 9pt "Arial";' \
                         'text-decoration: underline;' \
                         'background-color: rgb(30, 210, 80);' \
                         'border-radius: 10px;'
        (self.stateLbl.setText('In preparation'), self.stateLbl.setStyleSheet(in_preparation_style)) if not \
            self.db.is_table(f'{self.constructionObj.info["serial_number"]}_welds') else \
            (self.stateLbl.setText('Released at: 17 Dec 22'), self.stateLbl.setStyleSheet(released_style))
        counter = len(self.db.df_from_filteredTable(f"{self.constructionObj.info['serial_number']}_SubConstructions",
                                                    'main_construction_id', self.constructionObj.info['id']))
        self.subsAmountLbl.setText(str(counter))
        counter = len(self.db.table_into_DF(f"{self.constructionObj.info['serial_number']}_modelWelds"))
        self.weldsAmountLbl.setText(str(counter))


if __name__ == '__main__':
    from mainWindow import DekiDesktopApp, MainWindow

    app = DekiDesktopApp(sys.argv)

    mw = MainWindow()

    test_widgtet = InspectionPlannerScreen(mw)

    test_widgtet.show()

    try:
        sys.exit(app.exec_())
    except:
        print("Exiting the App")
