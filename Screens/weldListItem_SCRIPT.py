import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from Screens import db_objects
import gnrl_database_con


class WeldListItem(QWidget):
    def __init__(self, weldID, parent_construction, weldObject: db_objects.WeldObject = None):
        super(WeldListItem, self).__init__()
        uic.loadUi(r'weldListItem.ui', self)

        self.db: gnrl_database_con.Database = QApplication.instance().database
        self.mainWindowInstance = QApplication.instance().inspectionPlannerWindow

        self.parent_construction = parent_construction
        self.welds_db_tableName = f"{self.parent_construction.mainConstructionObject.info['serial_number']}_modelWelds"
        self.welds_db_table_df = None

        if weldObject is None:
            self.weldObj = db_objects.WeldObject()
            self.weldObj.fast_load_singleWeld(weldID)
        else:
            self.weldObj = weldObject

        if self.mainWindowInstance.cached_data['modelWelds_db'] is not None:
            self.welds_db_table_df = self.mainWindowInstance.cached_data['modelWelds_db']
        else:
            print(f'weldListItem_SCRIPT | WeldListItem __init__ | Acquiring the welds data from database...', end=' ')
            self.welds_db_table_df = self.db.table_into_DF(self.welds_db_tableName)
            print(f'Caching the data in QApplication.cached_data...', end=' ')
            QApplication.instance().cached_data.update({'modelWelds_db': self.welds_db_table_df})
            print(f'Success.')

        self.editWeldBtn.clicked.connect(self.edit_weld)

        self.create_layout()

    def create_layout(self):
        self.weldNumberLbl.setText(f"{self.weldObj.info['weld_id_generated']}")

        if self.weldObj.info['weld_continuity_type'] == 'normal':
            self.upperSpacing.hide()
            self.sidedSpacing.hide()
            self.staggerSignLbl.hide()
            # self.weldIntermittentSignFrame.hide()
        elif self.weldObj.info['weld_continuity_type'] == 'intermittent':
            self.staggerSignLbl.hide()
            self.upperSpacing.setText(self.weldObj.info['upper_weld_spacing'])

        # To insert a QIcon into QLabel, a Qicon has to be transformed to pixmap by .pixmap(size) method
        self.assemblyWeldLbl.setPixmap(
            QtGui.QPixmap(QtGui.QIcon(':/Icons/Icons/weldIcon_weldBanner.png').pixmap(20, 20)))
        self.assemblyWeldLbl.show() if bool(int(self.weldObj.info['field_weld'])) else self.assemblyWeldLbl.hide()
        self.allRoundWeldLbl.setPixmap(
            QtGui.QPixmap(QtGui.QIcon(':/Icons/Icons/weldIcon_weldRoundedLine.png').pixmap(20, 20)))
        self.allRoundWeldLbl.show() if bool(int(self.weldObj.info['all_around'])) else self.allRoundWeldLbl.hide()
        # ----------------------------------------------------------- upper weld info loading --------------------------
        self.upperWeldTypeLbl.setPixmap(QtGui.QPixmap(
            QtGui.QIcon(f':/Icons/Icons/weldIcon_{self.weldObj.info["upper_weld_type"]}.png').pixmap(12, 12)))
        self.upperSize.setText(f"{self.weldObj.info['upper_sizeType']}{self.weldObj.info['upper_size']}")
        self.upperLength.setText(f"{self.weldObj.info['upper_length']} mm")
        if self.weldObj.info['upper_weld_quant'] != '' and self.weldObj.info['upper_weld_quant'] is not None:
            self.upperQuantity.setText(f"{self.weldObj.info['upper_weld_quant']}x")
        else:
            self.upperQuantity.hide()

        for testingMethodButton in self.testingMthdsFrame.findChildren(QtWidgets.QPushButton):
            try:
                if testingMethodButton.objectName().replace('Btn', '') in self.weldObj.info['testing_methods']:
                    testingMethodButton.setChecked(True)
            except AttributeError:
                print(f'Testing methods not specified in the database.')

        self.check_sidedInfo()

        self.sameAmountLbl.setText(f"x{self.weldObj.sameWeldsAmount}")

        self.parentConstructionLbl.setText(f"({self.parent_construction.info['name']})")

    def check_sidedInfo(self):
        if not bool(int(self.weldObj.info['double_sided'])):
            self.sidedInfoFrame.hide()
            self.resize(self.width(), self.height() - self.sidedWeldTypeLbl.height())
        else:
            self.sidedSize.setText(f"{self.weldObj.info['sided_sizeType']}{self.weldObj.info['sided_size']}")
            self.sidedLength.setText(f"{self.weldObj.info['sided_length']} mm")
            if self.weldObj.info['weld_continuity_type'] == 'intermittent' or \
                    self.weldObj.info['weld_continuity_type'] == 'staggered':
                self.sidedSpacing.setText(self.weldObj.info['sided_weld_spacing'])
                self.sidedQuantity.setText(self.weldObj.info['sided_weld_quant'])
            else:
                self.sidedSpacing.hide()
                self.sidedQuantity.hide()
            self.sidedWeldTypeLbl.setPixmap(QtGui.QPixmap(
                QtGui.QIcon(f':/Icons/Icons/weldIcon_{self.weldObj.info["sided_weld_type"]}.png').pixmap(
                    12, 12).transformed(QtGui.QTransform().scale(1, -1))))

    def removeWeld(self):  # TODO
        pass

    def edit_weld(self):
        from weldPreviewDialog_SCRIPT import WeldPreviewDialog
        try:
            dialog = WeldPreviewDialog(weldObject=self.weldObj, parentConstruction=self.parent_construction)
            dialog_result = dialog.exec_()
        except Exception as e:
            print(f"weldListItem_SCRIPT | Func(edit_weld) failure | err-> {e}")
            return 0

        if dialog_result:
            self.welds_db_table_df = self.db.table_into_DF(self.welds_db_tableName)
            self.weldObj.db_content = self.welds_db_table_df
            self.mainWindowInstance.cached_data.update({'modelWelds_db': self.welds_db_table_df})
            self.weldObj.fast_load_singleWeld(self.weldObj.info['id'])
            print(f"Weld has been edited")



if __name__ == '__main__':
    app = QApplication(sys.argv)

    construction = db_objects.MainConstruction()
    construction.load_info(1)

    mainWindow = WeldListItem(6, construction)
    mainWindow.show()

    try:
        sys.exit(app.exec_())
    except:
        print("Exiting the App")
