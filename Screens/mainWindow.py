import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.uic import loadUi

import gnrl_database_con

import Screens.resources_rc

from PyQt5.QtCore import QPropertyAnimation, QEasingCurve


class DekiDesktopApp(QApplication):
    def __init__(self, *args):
        super(DekiDesktopApp, self).__init__(*args)
        self.database = gnrl_database_con.Database()
        self.inspectionPlannerWindow = None
        self.cached_data = {}

    def setPlannerWindow(self, reference):
        self.inspectionPlannerWindow = reference


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        # Load Ui from .ui file
        loadUi(r'mainWindow.ui', self)
        # member variables
        self.animation = None

        # Hide notification widget
        self.popupNotificationContainer.deleteLater()

        # Show/Hide extension of left Menu with width of 300 pxls
        self.MenuBtn.clicked.connect(lambda: self.showMenu(self.CenterMenuContainer, 300))

        # Show/Hide extension of right Menu with width of 250 pxls
        self.moreMenuBtn.clicked.connect(lambda: self.showMenu(self.RightMenuContainer, 250))

        from mainWindow_Pages import InspectionPlannerPage
        self.inspectionPlannerPageObj = InspectionPlannerPage(self)
        self.mainContentStackedWidget.addWidget(self.inspectionPlannerPageObj)
        self.InspectionPlanBtn.clicked.connect(
            lambda: self.mainContentStackedWidget.setCurrentWidget(self.inspectionPlannerPageObj))

        # Left Menu buttons
        self.HomeBtn.clicked.connect(lambda: self.mainContentStackedWidget.setCurrentWidget(self.HomePage))
        self.wpsCreatorBtn.clicked.connect(lambda: self.mainContentStackedWidget.setCurrentWidget(self.wpsCreatorPage))
        self.ReportsBtn.clicked.connect(lambda: self.mainContentStackedWidget.setCurrentWidget(self.ReportsPage))

        self.mainContentStackedWidget.setCurrentWidget(self.inspectionPlannerPageObj)

    # MainWindow button scripts
    def showMenu(self, menu_widget, opened_width):
        width = menu_widget.width()
        if width == 0:
            newWidth = opened_width
        else:
            newWidth = 0
        # noinspection PyAttributeOutsideInit
        self.animation = QPropertyAnimation(menu_widget, b"maximumWidth")
        self.animation.setDuration(250)
        self.animation.setStartValue(width)
        self.animation.setEndValue(newWidth)
        self.animation.setEasingCurve(QEasingCurve.InOutQuart)
        self.animation.start()

    def openNewModule(self, newModuleWindow: QWidget):
        newModuleWindow.show()
        self.close()
        # in lambda definition an "event" has to be passed for proper functionality!
        newModuleWindow.closeEvent = lambda event: self.show()


def main():
    app = DekiDesktopApp(sys.argv)

    mainWindow = MainWindow()
    mainWindow.show()

    try:
        sys.exit(app.exec_())
    except:
        print("Exiting the App")


if __name__ == '__main__':
    main()
