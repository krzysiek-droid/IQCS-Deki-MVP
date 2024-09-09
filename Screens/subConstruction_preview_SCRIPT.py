import logging
import sys

from gfunctions import log_exception

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5 import uic

from Screens import cadViewWidget_SCRIPT as cadviewer, db_objects as dbo
from Screens import pdfViewWidget_SCRIPT as pdfviewer
from weldListItem_SCRIPT import WeldListItem


def showDialog(dialog, closeEventFunc):
    dialog.closeEvent = lambda event: closeEventFunc()
    dialog.exec_()


class SubConstructPreviewScreen(QDialog):
    def __init__(self, subConstructionObject: dbo.SubConstruction):
        super(SubConstructPreviewScreen, self).__init__()
        # set loggers to print only Warnings during screen changes, w/o it prints all debug lines, which is annoying
        uic.properties.logger.setLevel(logging.WARNING)
        uic.uiparser.logger.setLevel(logging.WARNING)
        uic.loadUi(r'subconstruction_preview_UI.ui', self)

        self.mainWindowInstance = QApplication.instance().inspectionPlannerWindow
        if self.mainWindowInstance is None:
            print(f'No main window instance found.!')
            raise ValueError

        self.subConstructionObject = subConstructionObject
        if self.subConstructionObject.info['parent_construction_id'] is not None:
            self.mainConstructionObject = self.mainWindowInstance.cached_data['mainConstructionObject']
            self.parentConstructionObject = dbo.SubConstruction(self.mainConstructionObject)
            self.parentConstructionObject.load_info(int(self.subConstructionObject.info['parent_construction_id']))
        else:
            # the parent construction has no other parent construction but the main construction
            if self.mainWindowInstance.cached_data['mainConstructionObject'] is None:
                self.mainConstructionObject = dbo.MainConstruction()
                self.mainConstructionObject.load_info(self.subConstructionObject.info['main_construction_id'])
            else:
                self.mainConstructionObject = self.mainWindowInstance.cached_data['mainConstructionObject']
            self.parentConstructionObject = self.mainConstructionObject

        self.db = QApplication.instance().database
        self.constructID = self.subConstructionObject.info['id']

        self.pdfViewerWidget = None
        self.cadModelViewWidget = None

        self.subConstructions_table = \
            self.db.table_into_DF(f"{self.mainConstructionObject.info['serial_number']}_SubConstructions")

        self.constructions_items_list = self.load_belonging_constructions()
        self.weld_items_list = self.load_welds()
        # ---------------------------------------------------------------Screen loading functions----------------------
        self.qualityMoreInfoFrame.hide()
        self.subConstructContractorFrame.hide()
        self.showParentInfoBtn.hide()
        self.hideParentInfoBtn.hide()
        self.update_parentConstructionInfo()
        self.update_subConstructionInfo()
        self.load_SubConstructionsScrollArea()
        self.load_welds_ScrollArea()
        # ---------------------------------------------------------------Button scripting------------------------------
        self.qualityMoreBtn.clicked.connect(
            lambda: self.qualityMoreInfoFrame.show() if not self.qualityMoreInfoFrame.isVisible() else
            self.qualityMoreInfoFrame.hide())
        self.showParentInfoBtn.clicked.connect(lambda: self.leftSidedContent.show())
        self.hideParentInfoBtn.clicked.connect(lambda: self.leftSidedContent.hide())

        self.addWeldBtn.clicked.connect(self.add_weld)

        self.addSubConstructionBtn.clicked.connect(self.addConstruction_dialog)

        self.cadDocsTab.currentChanged.connect(lambda idx: self.cadModelViewWidget.fitToParent())

        self.showParentConstructionBtn.clicked.connect(self.goToParent)
        self.goToMainConstructionBtn.clicked.connect(self.goToMain)

        # -----------------------------------------------------------------UPDATE INFO---------------------------------

        self.cadDocsTab.setCurrentIndex(0)

    def goToParent(self):
        if type(self.parentConstructionObject) is dbo.SubConstruction:
            self.mainWindowInstance.changeScreen(SubConstructPreviewScreen, [self.parentConstructionObject])
        elif type(self.parentConstructionObject) is dbo.MainConstruction:
            from construction_preview_SCRIPT import MainConstructionDialog
            self.mainWindowInstance.changeScreen(MainConstructionDialog, [self.mainConstructionObject])

    def goToMain(self):
        from construction_preview_SCRIPT import MainConstructionDialog
        self.mainWindowInstance.changeScreen(MainConstructionDialog, [self.mainConstructionObject])

    def showStepModel(self, construction):
        # Delete old widget -> for case CAD model is changed
        for oldWidget in self.cadViewerContainer.findChildren(QWidget):
            oldWidget.deleteLater()
            oldWidget.hide()
            print(f"Step widget -- {oldWidget} -- {oldWidget.objectName()} deleted... OK")
        tmp_layout = QVBoxLayout()
        # create a widget for viewing CAD (CAD canvas widget/new_screen_ref)
        self.cadModelViewWidget = cadviewer.CadViewer(construction.stpModelPath)
        tmp_layout.addWidget(self.cadModelViewWidget)
        self.cadViewerContainer.setLayout(tmp_layout)
        # self.cadViewerContainer.setLayout(cadModelViewWidget) --> If cadViewer is a layout
        self.cadModelViewWidget.start_display()

    def showPdfViewer(self, construction):
        self.pdfViewerWidget = pdfviewer.pdfViewerLayout(fr'{construction.pdfDocsPath}',
                                                         parent=self.docsViewerContainer)
        self.docsViewerContainer.setLayout(self.pdfViewerWidget)

    def update_parentConstructionInfo(self):
        self.constructPicture.setPixmap(
            self.parentConstructionObject.picture.scaledToHeight(200, mode=Qt.SmoothTransformation))
        self.constructNameLbl.setText(self.parentConstructionObject.info['name'])
        self.constructTagLbl.setText(self.parentConstructionObject.info['tag'])
        self.constructLocalizationLbl.setText(self.parentConstructionObject.info['localization'])
        self.constructOwnerLbl.setText(self.parentConstructionObject.info['owner'])
        self.constructMaterialLbl.setText(self.parentConstructionObject.info['material'])
        self.constructNumberLbl.setText(self.parentConstructionObject.info['serial_number'])
        self.constructAdditionalInfoLbl.setText(self.parentConstructionObject.info['additional_info'])
        self.qualityNormLbl.setText(self.parentConstructionObject.info['quality_norm'])
        self.qualityClassLbl.setText(self.parentConstructionObject.info['quality_class'])
        self.tolerancesNormLbl.setText(self.parentConstructionObject.info['tolerances_norm'])
        self.tolerancesLevelLbl.setText(self.parentConstructionObject.info['tolerances_level'])
        if self.parentConstructionObject.info['subcontractor'] == 'N/A':
            self.mainConstrucContractorFrame.hide()
        else:
            self.mainConstructContractorNameLbl.setText(self.parentConstructionObject.info['subcontractor'])
            self.mainConstructContractorContactLbl.setText(self.parentConstructionObject.info['sub_contact'])

    def update_subConstructionInfo(self):
        self.subConstructionPictureLbl.setPixmap(
            self.subConstructionObject.picture.scaledToHeight(200, mode=Qt.SmoothTransformation))
        self.showStepModel(self.subConstructionObject)
        self.showPdfViewer(self.subConstructionObject)
        self.subConstructNameLbl.setText(self.subConstructionObject.info['name'])
        self.subConstructAdditionalInfoLbl.setText(self.subConstructionObject.info['additional_info'])
        self.subConstructSerialLbl.setText(self.subConstructionObject.info['serial_number'])
        self.subConstructOwnerLbl.setText(self.subConstructionObject.info['owner'])
        self.subConstructTypeLbl.setText(self.subConstructionObject.info['construct_type'])
        self.subConstructTagLbl.setText(self.subConstructionObject.info['tag'])
        self.subConstructTolerancesNormLbl.setText(self.subConstructionObject.info['tolerances_norm'])
        self.subConstructQualityNormLbl.setText(self.subConstructionObject.info['quality_norm'])
        self.subConstructMaterialLbl.setText(self.subConstructionObject.info['material'])
        self.subConstructTolerancesLevelLbl.setText(self.subConstructionObject.info['tolerances_level'])
        self.subConstructLocalizationLbl.setText(self.subConstructionObject.info['localization'])
        self.subConstructQualityClassLbl.setText(self.subConstructionObject.info['quality_class'])

    def load_belonging_constructions(self, construction_items=None):
        if construction_items is None:
            child_constructions_df = self.db.get_subConstruction_branch(self.constructID,
                                                                        df=self.subConstructions_table)
            child_list = []
            if not child_constructions_df.empty:
                from construction_preview_SCRIPT import ConstructionListItem
                for row in child_constructions_df.iterrows():
                    construction = dbo.SubConstruction(self.mainConstructionObject)
                    construction.load_info(row[1]['id'])
                    new_listItem = ConstructionListItem(construction)
                    new_listItem.transform_into_subConstructionScreenItem()
                    new_listItem.opened.connect(self.open_construction)
                    child_list.append(new_listItem)
                print(f"Found {len(child_list)} children constructions.")
                return child_list
            else:
                return []
        else:
            if len(construction_items) > 0:
                child_constructions_df = self.db.get_subConstruction_branch(self.constructID,
                                                                            df=self.subConstructions_table)
                child_constructions_ids = child_constructions_df['id'].tolist()
                child_list = []
                for listItem in construction_items:
                    if listItem.subConstructionID in child_constructions_ids:
                        listItem.transform_into_subConstructionScreenItem(True)
                        listItem.opened.connect(self.open_construction)
                        child_list.append(listItem)
                return child_list
            else:
                return []

    def load_SubConstructionsScrollArea(self):
        # Condition required for list refreshment after every call of this function
        if self.subComponentsListContent.layout() is not None:
            layout = self.subComponentsListContent.layout()
            for lbl in self.subComponentsList.findChildren(QLabel):
                lbl.deleteLater()
                lbl.hide()
            curr_itemsList = set(layout.findChildren(QWidget))
            # Section for adding/removal of listItem with changes in AllListItems
            # Every change in db_subConstructions has to be followed by load_subConstructionList function!
            if not curr_itemsList == self.constructions_items_list:
                # there is new listItem added
                if len(self.constructions_items_list) > len(curr_itemsList):
                    difference = set(self.constructions_items_list).symmetric_difference(curr_itemsList)
                    for new_constructionListItem in difference:
                        new_constructionListItem.transform_into_subConstructionScreenItem()
                        new_constructionListItem.opened.connect(self.open_construction)
                        layout.addWidget(new_constructionListItem, alignment=Qt.AlignTop)
                    layout.setAlignment(Qt.AlignTop)
                else:
                    # a construction has been removed
                    difference = set(self.constructions_items_list).symmetric_difference(curr_itemsList)
                    for removed_constructionItem in difference:
                        removed_constructionItem.hide()
                        removed_constructionItem.deleteLater()

        # First time loading section
        else:
            layout = QVBoxLayout()
            layout.setSpacing(2)
            # iterate throughout subConstruction list to load them as ConstructionListItem new_screen_ref into the
            # screen
            if len(self.constructions_items_list) != 0:
                for constructionListItem in self.constructions_items_list:
                    layout.addWidget(constructionListItem, alignment=Qt.AlignTop)
                layout.setAlignment(Qt.AlignTop)
            else:
                label = QLabel()
                label.setText(f'No Subconstructions found in database.')
                label.setStyleSheet('font: 12pt "Calibri";'
                                    'background-color: none;')
                layout.addWidget(label, alignment=Qt.AlignCenter)
                layout.setAlignment(Qt.AlignCenter)
            self.subComponentsListContent.setLayout(layout)
        self.tabWidget.setTabText(1, f'Subconstructions ({len(self.constructions_items_list)})')

    def load_welds(self, weld_items=None):
        if weld_items is None:
            weld_list = []
            # get dataframe with welds belonging to mainConstruction, by ID
            table_name = f"{self.mainConstructionObject.info['serial_number']}_modelWelds"
            belonging_welds_df = self.db.df_from_filteredTable(table_name, 'belonging_construction_ID',
                                                               self.constructID)
            if len(belonging_welds_df) != 0:
                print(f'---------- Initialization of welds items -> found {len(belonging_welds_df)} welds',
                      end='         ')
                for weld_row in belonging_welds_df.iterrows():
                    if not bool(weld_row[1]['same_as_weldID']):
                        weldListItem = WeldListItem(int(weld_row[1]["id"]), self.mainConstructionObject)
                        weld_list.append(weldListItem)
                print(f'---------- Initialization ended with {len(weld_list)} unique welds.')
                return weld_list
            else:
                return []
        else:
            table_name = f"{self.mainConstructionObject.info['serial_number']}_modelWelds"
            belonging_welds_df = self.db.df_from_filteredTable(table_name, 'belonging_construction_ID',
                                                               self.constructID)
            weld_list = []
            for weldItem in weld_items:
                if weldItem.weldObj.info['id'] in belonging_welds_df['id'].tolist():
                    # weldItem.parentScreen = self
                    weld_list.append(weldItem)
            return weld_list

    def load_welds_ScrollArea(self):
        print(f'Preparing the welds scroll area...')
        if self.weldListWidgetContent.layout() is not None:
            layout = self.weldListWidgetContent.layout()
            if self.weldListWidget.findChild(QLabel) is not None:
                self.weldListWidget.findChild(QLabel).hide()
                self.weldListWidget.findChild(QLabel).deleteLater()
            QApplication.instance().processEvents()
            # Refresh ScrollArea
            # Delete previous items
            for i in reversed(range(layout.count())):
                layout.itemAt(i).widget().setParent(None)
            QApplication.instance().processEvents()
            # Reset the first item in Scroll Area - has to be done bcs of some kind of glitch that changes
            # visibility issues of weldNumberLine
            if len(self.weld_items_list) > 1:
                reset_listItem = self.weld_items_list[0]
                self.weld_items_list[0] = WeldListItem(int(reset_listItem.weldObj.info['id']),
                                                       reset_listItem.parent_construction)
            # Add all items again (with new Item being included)
            for weldListItem in self.weld_items_list:
                layout.addWidget(weldListItem, alignment=Qt.AlignTop)
            layout.setAlignment(Qt.AlignTop)
            layout.setSpacing(2)

        else:
            print('Preparing new welds scroll area...')
            layout = QVBoxLayout()
            layout.setSpacing(2)
            self.weldListWidgetContent.setLayout(layout)
            # iterate throughout subConstruction list to load them as ConstructionListItem new_screen_ref into the
            # screen
            if len(self.weld_items_list) != 0:
                for weld_list_item in self.weld_items_list:
                    layout.addWidget(weld_list_item, alignment=Qt.AlignTop)
                    weld_list_item.adjustSize()
                layout.setAlignment(Qt.AlignTop)
                # self.weldListWidgetContent.adjustSize()
            else:
                label = QLabel()
                label.setText(f'No Subconstructions found in database.')
                label.setStyleSheet('font: 12pt "Calibri";'
                                    'background-color: none;')
                layout.addWidget(label, alignment=Qt.AlignCenter)
                layout.setAlignment(Qt.AlignCenter)
        self.tabWidget.setTabText(0, f'Welds ({len(self.weld_items_list)})')

    def adjustItems_Size(self, listItemsWidget: QWidget, itemType):
        try:
            for listItem in listItemsWidget.findChildren(itemType):
                listItem.weldNumberLbl.setText(f"{listItem.weldObj.info['weld_id_generated']}")
                listItem.adjustSize()
            return 1
        except Exception as e:
            print(log_exception(e))

    def open_construction(self, subConstructionObject):
        self.mainWindowInstance.change_to_SubConstructionScreen(subConstructionObject)

    def addConstruction_dialog(self):
        from new_subconstruction_SCRIPT import NewSubconstructionDialog
        try:
            dialog = NewSubconstructionDialog(self.subConstructionObject)
            result = dialog.exec_()
            if bool(result):
                try:
                    from construction_preview_SCRIPT import ConstructionListItem
                    new_constructionItem = ConstructionListItem(dialog.new_subConstruction)
                    self.constructions_items_list.append(new_constructionItem)
                    self.load_SubConstructionsScrollArea()
                    # update the subConstructions list
                    self.subConstructions_table = \
                        self.db.table_into_DF(f"{self.mainConstructionObject.info['serial_number']}_SubConstructions")
                    # cache the updated data
                    self.mainWindowInstance.cached_data.update({'subConstructions_db': self.subConstructions_table})
                except Exception as e:
                    print(f"New construction list item couldn't be shown err-> {e}")
            else:
                print(f'Dialog closed without changes.')
        except Exception as e:
            print(f"New subConstruction Dialog couldn't been open -> {e}")

    def add_weld(self):
        from new_weld_SCRIPT import NewWeldDialog
        try:
            dialog = NewWeldDialog(self.subConstructionObject)
            result = dialog.exec_()
            if bool(result):
                new_weldItem = WeldListItem(int(dialog.new_weldObj.info['id']), self.subConstructionObject,
                                            dialog.new_weldObj)
                self.weld_items_list.append(new_weldItem)
                self.load_welds_ScrollArea()
            else:
                print(f"Dialog closed without changes.")
        except Exception as e:
            print(f'subConstruction_preview_SCRIPT | Func(add_weld) failure |  err-> {e}')


if __name__ == '__main__':
    from mainWindow import DekiDesktopApp
    from inspectionPlannerWindow_SCRIPT import InspectionPlannerWindow

    app = DekiDesktopApp(sys.argv)
    ins = InspectionPlannerWindow()

    app.inspectionPlannerWindow = ins

    main_construction = dbo.MainConstruction()
    main_construction.load_info(1)
    ins.cached_data['mainConstructionObject'] = main_construction
    sub_construction = dbo.SubConstruction(main_construction)
    sub_construction.load_info(1)

    screen = SubConstructPreviewScreen(sub_construction)
    screen.show()

    try:
        sys.exit(app.exec_())
    except:
        print("Exiting the App")
