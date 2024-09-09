import logging
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtCore

import gfunctions
from Screens import cadViewWidget_SCRIPT as cadviewer, db_objects as dbo
from Screens import pdfViewWidget_SCRIPT as pdfviewer


def clearLayout(layout):
    print(f'Clearing layout -> {layout}', end="... ")
    while layout.count():
        child = layout.takeAt(0)
        if child.widget() is not None:
            child.widget().hide()
            child.widget().deleteLater()
            child.widget().setParent(None)
    print(f'Finished.')


class ConstructionListItem(QWidget):
    selected = QtCore.pyqtSignal()
    opened = QtCore.pyqtSignal(object)

    def __init__(self, subConstruction_loaded: dbo.SubConstruction):
        super(ConstructionListItem, self).__init__()
        uic.loadUi(r'ListItem.ui', self)
        print(f"---------------------------------------- INIT OF {subConstruction_loaded.info['name']} list item.")
        self.subConstructionObject = subConstruction_loaded
        self.subConstructionID = subConstruction_loaded.info['id']
        # Get access to QMainWindow instance for its member methods, and save its reference as a member variable
        self.mainWindowInstance = None

        self.isSelected = False
        self.isTopConstruction = False

        self.selectConstructionBtn.clicked.connect(self.select_item)
        # TODO: functions to filter allWelds by the item
        # self.weldFilterBtn.clicked.connect(lambda: self.filter_welds(self.subConstructionObject))
        self.openSubConstructionBtn.clicked.connect(lambda: (self.opened.emit(self.subConstructionObject),
                                                             print(f"{self} -> open clicked -> "
                                                                   f"{self.subConstructionObject}")))
        self.load_info()

    def load_info(self):
        self.constructionTag.setText(self.subConstructionObject.info["tag"])
        self.constructionName.setText(self.subConstructionObject.info['name'])
        self.constructionPicture.setPixmap(self.subConstructionObject.picture.scaled(120, 120, 1, 1))
        self.typeLbl.setText(self.subConstructionObject.info['construct_type'])
        self.tierLbl.setText(f"Tier: {self.subConstructionObject.info['tier']}")

        belonging_constructions = self.subConstructionObject.get_children()
        belonging_welds = self.subConstructionObject.get_belonging_welds()
        self.subsLbl.setText(f"{len(belonging_constructions)} \n subs")
        self.weldsLbl.setText(f"{len(belonging_welds)} \n welds")

    def select_item(self):
        self.isSelected = True
        self.mainFrame.setStyleSheet('QFrame{ background-color: rgb(255, 255, 255);}'
                                     '#mainFrame{'
                                     'border-width: 2px;'
                                     'bordr-radius: 25px;'
                                     'border-style: solid;'
                                     'border-color: rgb(30, 210, 80);}')
        self.selectConstructionBtn.setEnabled(False)
        self.selected.emit()

    def deselect_item(self):
        self.isSelected = False
        self.mainFrame.setStyleSheet('QFrame{ background-color: rgb(255, 255, 255);}'
                                     '#mainFrame{'
                                     'border-width: 0px;}'
                                     '#mainFrame::hover{'
                                     'border-width: 2px;'
                                     'bordr-radius: 25px;'
                                     'border-style: solid;'
                                     'border-color: rgb(30, 210, 80);}')
        self.selectConstructionBtn.setEnabled(True)

    def setAsLower(self):
        self.selectConstructionBtn.setEnabled(False)
        self.selectConstructionBtn.hide()

    def setAsTop(self):
        self.isTopConstruction = True
        self.tierLbl.setText('TOP')
        self.tierLbl.setStyleSheet('color: rgb(255, 150, 0);'
                                   'font: italic bold 12pt "Calibri";')

    def transform_into_subConstructionScreenItem(self, disconnect_signals=False):
        self.selectConstructionBtn.setEnabled(False)
        self.selectConstructionBtn.hide()
        self.isSelected = False

        # Disconnect all previous signals
        if disconnect_signals:
            try:
                self.opened.disconnect()
                self.selected.disconnect()
            except Exception as e:
                print(f"Couldnt disconnect listItem's signal -> {e}")


class MainConstructionDialog(QDialog):
    def __init__(self, constructionObject: dbo.MainConstruction):
        super(MainConstructionDialog, self).__init__()
        self.cadModelViewWidget = None
        uic.properties.logger.setLevel(logging.WARNING)
        uic.uiparser.logger.setLevel(logging.WARNING)
        uic.loadUi(r'construction_preview_UI.ui', self)
        # self.setWindowState(Qt.WindowMaximized)


        self.mainWindowInstance = QApplication.instance().inspectionPlannerWindow
        if self.mainWindowInstance is None:
            gfunctions.log_exception("Cant find the inspectionPlannerWindow in QApplication.instance()")
            raise SystemError

        self.lowerTierConstructionsTab.setEnabled(False)
        self.upperTierConstructionsTab.setEnabled(False)

        self.setObjectName('mainConstructionPreviewScreen')
        self.mainConstructionObject = constructionObject
        self.mainConstructionIdNum = int(self.mainConstructionObject.info['id'])
        # open database connection
        self.db = QApplication.instance().database

        self.subConstructions_table = \
            self.db.table_into_DF(f"{self.mainConstructionObject.info['serial_number']}_SubConstructions")
        self.mainWindowInstance.cached_data.update({'subConstructions_db': self.subConstructions_table})

        self.selected_construction = None

        # --------------------------------------------------------------- Constructions Scroll Area ------------------
        self.constructions_items_list = []
        self.constructions_objects = []
        self.lowerLevelConstructions_ItemList = []
        self.upperLevelConstructions_ItemList = []

        # must be called before load_weldList func
        self.load_subConstructionsList()
        self.prepare_constructions_ScrollArea()

        # -------------------------------------------------------------- Welds Scroll Area ----------------------------
        self.weld_items_list = []

        self.load_weldList()
        self.prepare_welds_ScrollArea()
        # ---------------------------------------------------------------Screen loading functions----------------------
        self.showStepModel()
        self.showPdfViewer()
        for constructionItem in self.constructions_items_list:
            if constructionItem.isTopConstruction:
                constructionItem.select_item()
                break
        self.subAssembliesTabWidget.setCurrentIndex(0)
        # ---------------------------------------------------------------Button scripting------------------------------
        from InspectionPlannerScreen_SCRIPT import InspectionPlannerScreen
        self.goBackBtn.clicked.connect(
            lambda: self.mainWindowInstance.changeScreen(InspectionPlannerScreen, []))

        self.addSubassemblyBtn.clicked.connect(self.add_TopTier_construction)

        # -----------------------------------------------------------------UPDATE INFO---------------------------------
        self.constructPicture.setPixmap(self.mainConstructionObject.picture.scaled(200, 200, 1, 1))
        self.constructNameLabel.setText(self.mainConstructionObject.info['name'])
        self.constructTagLabel.setText(self.mainConstructionObject.info['tag'])
        self.constructNumberLabel.setText(self.mainConstructionObject.info['serial_number'])
        self.constructOwnerLabel.setText(self.mainConstructionObject.info['owner'])
        self.constructMaterialLabel.setText(self.mainConstructionObject.info['material'])
        self.constructLocalizationLabel.setText(self.mainConstructionObject.info['localization'])
        self.constructAdditionalInfoLabel.setText(self.mainConstructionObject.info['additional_info'])
        self.constructTypeLabel.setText(self.mainConstructionObject.info['construct_type'])
        self.qualityNormLabel.setText(self.mainConstructionObject.info['quality_norm'])
        self.qualityClassLabel.setText(self.mainConstructionObject.info['quality_class'])
        self.tolerancesNormLabel.setText(self.mainConstructionObject.info['tolerances_norm'])
        self.tolerancesLevelLabel.setText(self.mainConstructionObject.info['tolerances_level'])
        self.subcontractorLabel.setText(self.mainConstructionObject.info['subcontractor'])
        self.subcontractorContactLabel.setText(self.mainConstructionObject.info['sub_contact'])

        self.cadDocsTab.currentChanged.connect(lambda idx: self.cadModelViewWidget.fitToParent())

    def showStepModel(self):
        # Delete old widget -> for in case CAD model is changed
        for oldWidget in self.cadViewerContainer.findChildren(QWidget):
            oldWidget.deleteLater()
            oldWidget.hide()
            print(f"Step widget -- {oldWidget} -- {oldWidget.objectName()} deleted... OK")
        tmp_layout = QVBoxLayout()
        # create a widget for viewing CAD (CAD canvas widget/new_screen_ref)
        self.cadModelViewWidget = cadviewer.CadViewer(self.mainConstructionObject.stpModelPath)
        tmp_layout.addWidget(self.cadModelViewWidget)
        self.cadViewerContainer.setLayout(tmp_layout)
        # self.cadViewerContainer.setLayout(cadModelViewWidget) --> If cadViewer is a layout
        self.cadModelViewWidget.start_display()

    def showPdfViewer(self):
        pdfViewerWidget = pdfviewer.pdfViewerLayout(fr'{self.mainConstructionObject.pdfDocsPath}',
                                                    parent=self.docsViewerContainer)
        self.docsViewerContainer.setLayout(pdfViewerWidget)

    def load_subConstructionsList(self):
        if len(self.constructions_items_list) == 0:
            subConstructions_IDs = self.subConstructions_table['id'].tolist()

            if len(subConstructions_IDs) != 0:
                for constructionID in subConstructions_IDs:
                    constructionObject = dbo.SubConstruction(self.mainConstructionObject)
                    constructionObject.load_info(int(constructionID))
                    self.constructions_objects.append(constructionObject)
                    listItem = ConstructionListItem(constructionObject)
                    listItem.opened.connect(self.open_construction)
                    listItem.selected.connect(self.select_subConstruction)
                    if constructionObject.info['parent_construction_id'] is None:
                        listItem.setAsTop()
                    self.constructions_items_list.append(listItem)
        return self.constructions_items_list

    def prepare_constructions_ScrollArea(self):
        # Condition required for list refreshment after every call of this function
        if self.allConstructsScroll.layout() is not None:
            layout = self.allConstructsScroll.layout()
            curr_itemsList = set(layout.findChildren(QWidget))

            for lbl in self.allConstructsScroll.findChildren(QLabel):
                lbl.hide()
                lbl.deleteLater()

            # Section for adding/removal of listItem
            if not curr_itemsList == self.constructions_items_list:
                # there is new listItem added
                if len(self.constructions_items_list) > len(curr_itemsList):
                    difference = set(self.constructions_items_list).symmetric_difference(curr_itemsList)
                    for new_constructionListItem in difference:
                        new_constructionListItem.opened.connect(self.open_construction)
                        new_constructionListItem.selected.connect(self.select_subConstruction)
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
            self.allConstructsScroll.setLayout(layout)

    def load_weldList(self):
        # Must be called after load_subConstructions!
        # get dataframe with welds belonging to mainConstruction, by ID
        if len(self.weld_items_list) == 0:
            welds_df = self.db.table_into_DF(f"{self.mainConstructionObject.info['serial_number']}_modelWelds")
            if len(welds_df) != 0:
                from weldListItem_SCRIPT import WeldListItem
                print(f'Initialization of welds items -> found {len(welds_df)} welds', end="... --- ")
                for weld_row in welds_df.iterrows():
                    if not bool(weld_row[1]['same_as_weldID']):
                        weld_parent_constructionObject = None
                        for constructionObject in self.constructions_objects:
                            if int(constructionObject.info['id']) == int(weld_row[1]["belonging_construction_ID"]):
                                weld_parent_constructionObject = constructionObject
                                break
                        if weld_parent_constructionObject is None:
                            weld_parent_constructionObject = dbo.SubConstruction(self.mainConstructionObject)
                            weld_parent_constructionObject.load_info(int(weld_row[1]["belonging_construction_ID"]))
                        weldListItem = WeldListItem(int(weld_row[1]["id"]), weld_parent_constructionObject)
                        self.weld_items_list.append(weldListItem)
                print(f'{len(self.weld_items_list)} unique welds found.')

    def prepare_welds_ScrollArea(self):
        if self.weldListWidgetContent.layout() is not None:
            layout = self.weldListWidgetContent.layout()
            curr_welds_list = set(layout.findChildren(QWidget))
            # judge whether current weld items list has the same amount of welds as self.weld_list_items
            # it required for fast refreshment of scrollArea
            if not curr_welds_list == self.weld_items_list:
                # there is new weld added
                if len(self.weld_items_list) > len(curr_welds_list):
                    difference = set(self.weld_items_list).symmetric_difference(curr_welds_list)
                    for new_weld_item in difference:
                        if not bool(new_weld_item.weldObj[1]['same_as_weldID']):
                            new_weld_item.clicked.connect(self.select_subConstruction)
                            layout.addWidget(new_weld_item, alignment=Qt.AlignTop)
                else:
                    # a weld has been removed
                    difference = set(self.weld_items_list).symmetric_difference(curr_welds_list)
                    for removed_weld_item in difference:
                        removed_weld_item.hide()
                        removed_weld_item.deleteLater()
        else:
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
                self.weldListWidgetContent.adjustSize()
            else:
                label = QLabel()
                label.setText(f'No welds found in database.')
                label.setStyleSheet('font: 12pt "Calibri";'
                                    'background-color: none;')
                layout.addWidget(label, alignment=Qt.AlignCenter)
                layout.setAlignment(Qt.AlignCenter)

    def filter_welds(self):  # TODO
        print('filtering welds...')

    def select_subConstruction(self):
        # Deselect Previous constructions
        if self.selected_construction is not None:
            self.allConstructsScroll.layout().addWidget(self.selected_construction)
            self.selected_construction.deselect_item()

        # acquire newly clicked construction
        for item in self.constructions_items_list:
            if item.isSelected:
                self.selected_construction = item
        self.selectedFrameLayout.addWidget(self.selected_construction)
        # prepare the lower tier construction into the lower tier tab
        try:
            self.prepare_lowerTierScroll(self.selected_construction)
            self.prepare_upperTierScroll(self.selected_construction)
        except Exception as e:
            print(f"Upper/Lower construction loading failure err-> {e}")

    def prepare_lowerTierScroll(self, selectedListItem):
        # Get a layout widget
        if self.lowerTierScrollWidget.layout() is not None:
            clearLayout(self.lowerTierScrollWidget.layout())
            layout = self.lowerTierScrollWidget.layout()
        else:
            layout = QVBoxLayout()
            layout.setSpacing(2)

        # Get listItems that represent construction belonging to clicked construction
        selected_constructionID = selectedListItem.subConstructionObject.info['id']
        lowerConstructionsItems = []
        tree_ids = self.db.get_subConstruction_branch(selected_constructionID, df=self.subConstructions_table)

        if len(tree_ids) != 0:
            tree_ids = tree_ids['id'].tolist()
            for item in self.constructions_items_list:
                if item.subConstructionObject.info['id'] in tree_ids:
                    lowerItem = ConstructionListItem(item.subConstructionObject)
                    lowerItem.opened.connect(self.open_construction)
                    lowerConstructionsItems.append(lowerItem)

                    # show tab with lower constructions
                    self.lowerTierConstructionsTab.setEnabled(True)
                    # add listItems of constructions belonging to clicked construction into the scroll area
                    for listItem in lowerConstructionsItems:
                        # make the listItem specifically a lower construction
                        listItem.setAsLower()
                        layout.addWidget(listItem, alignment=Qt.AlignTop)
                    layout.setAlignment(Qt.AlignTop)
        else:
            print(f'No children constructions found.')
            lbl = QLabel()
            lbl.setText(f'No lower tier constructions.')
            layout.addWidget(lbl, alignment=Qt.AlignCenter)

        # add layout with the listItems to lowerConstructions Tab
        self.lowerTierScrollWidget.setLayout(layout)

    def prepare_upperTierScroll(self, selectedListItem):
        # Get a layout widget
        if self.upperTierScrollWidget.layout() is not None:
            clearLayout(self.upperTierScrollWidget.layout())
            layout = self.upperTierScrollWidget.layout()
        else:
            layout = QVBoxLayout()
            layout.setSpacing(2)

        # Get listItems that represent constructions upper to clicked construction in the constructions tree

        selected_construction_id = selectedListItem.subConstructionID
        parents_df = self.db.get_subConstruction_core(selected_construction_id, df=self.subConstructions_table)

        if not parents_df.empty:
            self.upperTierConstructionsTab.setEnabled(True)
            upperConstructionsItems = []
            # Get subConstructions dataframe
            # get row at which a parent construction of clicked item is placed
            # iterate through constructions tree to get all constructions above to clicked one

            # get list of items representing upper constructions
            for item in self.constructions_items_list:
                if item.subConstructionObject.info['id'] in parents_df['id'].tolist():
                    upperConstructionsItems.append(ConstructionListItem(item.subConstructionObject))

            # add listItems of construction's upper constructions into the scroll area
            for listItem in upperConstructionsItems:
                # make the listItem specifically a lower construction
                layout.addWidget(listItem, alignment=Qt.AlignTop)
                listItem.setAsLower()
                listItem.adjustSize()
            layout.setAlignment(Qt.AlignTop)
        else:
            lbl = QLabel()
            lbl.setText(f'Selected construction is a Top Tier construction.')
            layout.addWidget(lbl, alignment=Qt.AlignCenter)
        # add layout with the listItems to lowerConstructions Tab
        self.upperTierScrollWidget.setLayout(layout)

    def showDialog(self, dialog, refreshment: bool = False):
        dialog.exec_()
        if refreshment:
            self.load_SubConstructionsList()

    def open_construction(self, subConstructionObject):
        from subConstruction_preview_SCRIPT import SubConstructPreviewScreen
        self.mainWindowInstance.changeScreen(SubConstructPreviewScreen,
                                             [subConstructionObject])

    def add_TopTier_construction(self):
        from new_subconstruction_SCRIPT import NewSubconstructionDialog
        dialog = NewSubconstructionDialog(self.mainConstructionObject)
        dialog.dialogTitleLabel.setText(f"Top Tier Construction Info:")
        result = dialog.exec_()
        if result:
            try:
                print(f"New construction added -{dialog.new_subConstruction}. Showing...", end=' ')
                new_constructionObject = dialog.new_subConstruction
                new_constructionItem = ConstructionListItem(new_constructionObject)
                new_constructionItem.setAsTop()
                # add new listItem (created from added subConstruction) to items_list
                self.constructions_items_list.append(new_constructionItem)
                # Refresh the subConstructions ScrollArea
                self.prepare_constructions_ScrollArea()
                # update the subConstructions list
                self.subConstructions_table = \
                    self.db.table_into_DF(f"{self.mainConstructionObject.info['serial_number']}_SubConstructions")
                # cache the updated data
                self.mainWindowInstance.cached_data.update({'subConstructions_db': self.subConstructions_table})
                print(f"Success.")
            except Exception as e:
                print(f"Showing failed err-> {e}")


if __name__ == '__main__':
    from mainWindow import DekiDesktopApp
    from inspectionPlannerWindow_SCRIPT import InspectionPlannerWindow

    app = DekiDesktopApp(sys.argv)

    ins = InspectionPlannerWindow()
    # ins.show()
    mC = dbo.MainConstruction()
    print(f'main construction initialized')
    mC.load_info(2)
    ins.cached_data['mainConstructionObject'] = mC
    tW = MainConstructionDialog(mC)
    tW.show()
    try:
        sys.exit(app.exec_())
    except:
        print("Exiting the App")
