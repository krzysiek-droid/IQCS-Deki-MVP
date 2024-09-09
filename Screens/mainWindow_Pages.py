import sys

from PyQt5 import Qt, QtGui
from PyQt5.QtWidgets import QDialog, QWidget, QVBoxLayout, QScrollArea, QApplication, QMainWindow
from PyQt5.uic import loadUi

from Screens import db_objects as dbo
import gnrl_database_con


class InspectionPlannerPage(QDialog):
    def __init__(self, mainWindowRef: QMainWindow):
        super(InspectionPlannerPage, self).__init__()
        self.previously_selected_constructionItem = None
        loadUi(r'inspectionPlannerPage_UI.ui', self)
        self.mainWindow = mainWindowRef

        # self.rightSidedMenu.setFixedWidth(0)

        self.setObjectName('InspectionPlannerPage')
        self.db: gnrl_database_con.Database = QApplication.instance().database
        self.scrollAreaContent: QWidget
        self.scrollLayout = QVBoxLayout()
        self.scrollArea: QScrollArea
        self.scrollArea.setLayout(self.scrollLayout)

        self.constructions_objects = self.loadConstructionList()
        self.rightSidedMenu.setCurrentIndex(0)

        # -------------------------------------------------- Buttons script

        import inspectionPlannerWindow_SCRIPT
        self.openModuleBtn.clicked.connect(
            lambda: (self.openNewModule(inspectionPlannerWindow_SCRIPT.InspectionPlannerWindow(
                self.constructions_objects))))

    def loadConstructionList(self):
        construction_objects = []
        for construct_id in range(len(self.db.table_into_DF('Deki_mainConstructions'))):
            construction = dbo.MainConstruction()
            construction.load_info(construct_id + 1)
            construction_objects.append(construction)
            constructionListItem = ConstructionListItemPageVersion(self, construction)
            constructionListItem.clicked.connect(self.updateRightMenu)
            self.scrollLayout.addWidget(constructionListItem, alignment=Qt.Qt.AlignTop)
        self.scrollLayout.setAlignment(Qt.Qt.AlignTop)
        return construction_objects

    def updateRightMenu(self):
        if self.previously_selected_constructionItem is None:
            for constructionItem in self.scrollArea.findChildren(ConstructionListItemPageVersion):
                if constructionItem.selected:
                    self.previously_selected_constructionItem = constructionItem
                    self.load_selectedItemInfo(constructionItem.constructionObj)
                    break
        else:
            for constructionItem in self.scrollArea.findChildren(ConstructionListItemPageVersion):
                if constructionItem.selected and constructionItem != self.previously_selected_constructionItem:
                    self.previously_selected_constructionItem.deselect()
                    self.load_selectedItemInfo(constructionItem.constructionObj)
                    self.previously_selected_constructionItem = constructionItem

    def load_selectedItemInfo(self, constructionObj):
        if not constructionObj.released:
            self.rightSidedMenu.setCurrentIndex(1)
            welds_df = self.db.table_into_DF(f"{constructionObj.info['serial_number']}_modelWelds")
            unique_welds = welds_df[welds_df['same_as_weldID'].isna()]
            if len(unique_welds) != 0:
                self.uniqueWeldsBtn.setText(f"{len(unique_welds)}")
            else:
                self.uniqueWeldsBtn.setText(f"0")
            test_assigned = self.db.df_from_filteredTable(
                f"{constructionObj.info['serial_number']}_modelWelds", 'testing_methods',
                "''", False)
            if len(test_assigned) != 0:
                self.testAssignedBtn.setText(f"{len(test_assigned)}")
            else:
                self.testAssignedBtn.setText(f"0")
        else:
            self.rightSidedMenu.setCurrentIndex(2)

    def openNewModule(self, newModuleWindow: QWidget):
        newModuleWindow.show()
        # self.close()
        # in lambda definition an "event" has to be passed for proper functionality!
        newModuleWindow.closeEvent = lambda event: self.show()


class ConstructionListItemPageVersion(QWidget):
    clicked = Qt.pyqtSignal(object)
    deselected = Qt.pyqtSignal(object)

    def __init__(self, parentScreenObj: InspectionPlannerPage, loadedConstructionObject: dbo.MainConstruction):
        super(ConstructionListItemPageVersion, self).__init__()
        # set attribute that deletes the instance of this class on closeEvent
        loadUi(r'MainConstructionListItem_UI.ui', self)

        self.constructionID = loadedConstructionObject.info['id']
        self.parentScreen = parentScreenObj
        self.constructionObj = loadedConstructionObject
        self.db = QApplication.instance().database
        self.subConstructions_db_table = f"{self.constructionObj.info['serial_number']}_SubConstructions"

        self.releaseConstructionBtn.hide()

        self.selected = False

        self.assignInfoToWidgets()

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        super(ConstructionListItemPageVersion, self).mousePressEvent(a0)
        if not self.selected and self.constructionObj.released:
            # If construction has been released mark it as clicked and released (Green)
            self.selected = True
            self.mainFrame.setStyleSheet("#mainFrame{border-width: 3px;"
                                         "border-style: solid;"
                                         "border-color: rgb(30, 210, 80);}")
        elif not self.selected and not self.constructionObj.released:
            # If construction hasn't been released mark it as clicked but not released (Orange)
            self.mainFrame.setStyleSheet("#mainFrame{border-width: 3px;"
                                         "border-style: solid;"
                                         "border-color: rgb(255, 150, 0);}")
            self.selected = True

        # Has to be at the end in order to call the connected function after run of above code
        self.clicked.emit(self.constructionObj)

    def assignInfoToWidgets(self):
        self.constructionTag.setText(self.constructionObj.info["tag"])
        self.constructionName.setText(self.constructionObj.info['name'])
        self.constructionPicture.setPixmap(
            self.constructionObj.picture.scaledToHeight(120, mode=Qt.Qt.SmoothTransformation))
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
        counter = len(self.constructionObj.subConstructions_df)
        self.subsAmountLbl.setText(str(counter))
        counter = len(self.constructionObj.modelWelds_df)
        self.weldsAmountLbl.setText(str(counter))

    def deselect(self):
        print(f"{self} deselected")
        self.mainFrame.setStyleSheet("#mainFrame{border-width: 0px;")
        self.selected = False
        self.deselected.emit(self.constructionObj)


if __name__ == "__main__":
    from mainWindow import DekiDesktopApp, MainWindow

    qApp = DekiDesktopApp(sys.argv)

    mw = MainWindow()
    mw.show()

    try:
        sys.exit(qApp.exec_())
    except:
        print("Exiting the App")
