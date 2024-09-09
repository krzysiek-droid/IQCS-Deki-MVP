import logging
import sys
import time

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
import InspectionPlannerScreen_SCRIPT

# resources_rc has to be imported here, even if it is not used directly in code, dunno why
import gnrl_database_con
import resources_rc

import pathlib


class CustomStackedWidget(QStackedWidget):
    def __init__(self, mainWindowInstance):
        super(CustomStackedWidget, self).__init__()
        self.mainWindowInstance = mainWindowInstance
        self.mainAppInstance = QApplication.instance()

    def changeScreen(self, calling_screen, called_screen):
        print(f'Changing screens...')
        calling_screen.close()
        self.addWidget(called_screen)
        self.setCurrentIndex(self.currentIndex() + 1)
        self.removeWidget(calling_screen)
        calling_screen.deleteLater()

    def changeScreen_woDelete(self, called_screen, pageTitle):
        print(f'Changing screens without deletion of current screen...')
        self.addWidget(called_screen)
        self.setCurrentIndex(self.currentIndex() + 1)
        for topLevelWidget in QApplication.topLevelWidgets():
            if type(topLevelWidget) is InspectionPlannerWindow:
                topLevelWidget.currentPageLabel.setText(pageTitle)

    # TODO: do splash screen!
    def changeScreen_withSplash(self, called_screen_ref, called_screen_init_args: list):
        print(f'Changing screens with splash...')
        self.mainWindowInstance.hide()
        from splashScreen_SCRIPT import SplashScreenDialog
        s = SplashScreenDialog(self, called_screen_ref, called_screen_init_args)
        self.mainWindowInstance.showMaximized()
        QApplication.instance().processEvents()
        QApplication.instance().processEvents()
        s.close()
        s.deleteLater()
        QApplication.instance().processEvents()
        # print(f"Stacked widget after screens change -> \n {self.children()}")


class InspectionPlannerWindow(QMainWindow):
    def __init__(self, constructionObjects=None):
        super(InspectionPlannerWindow, self).__init__()
        # set atribute that deletes the instance of this class on closeEvent
        self.setAttribute(Qt.WA_DeleteOnClose)
        # self.setWindowFlags(Qt.FramelessWindowHint)
        # set loggers to print only Warnings during screen changes, w/o it prints all debug lines, which is annoying
        uic.properties.logger.setLevel(logging.WARNING)
        uic.uiparser.logger.setLevel(logging.WARNING)
        # load UI frontend from .ui file
        uic.loadUi(r'InspectionPlannerWindow_UI.ui', self)
        self.setObjectName('inspectionPlannerWindow')
        self.setMinimumSize(1500, 950)

        # Cache the Window instance in Application memory
        QApplication.instance().setPlannerWindow(self)

        self.db = QApplication.instance().database

        self.cached_data = {'mainConstructionObject': None,
                            'modelWelds_db': None,
                            'subConstructions_db': None,
                            'mainConstructions_objects': constructionObjects}

        # define QStackedWidget for screen changing purposes
        self.stackedWidget = CustomStackedWidget(self)
        self.stackedWidget.setObjectName('screenManager')
        # QStackedWidget contains QStackedLayout, which is important in case of children and parent finding
        self.stackedWidgetContainer.addWidget(self.stackedWidget)
        # add the first screen (QWidget) to screenManager (stackedWidget)
        self.stackedWidget.addWidget(InspectionPlannerScreen_SCRIPT.InspectionPlannerScreen())

        # button allocations
        self.closeBtn.clicked.connect(lambda: self.close())

    def changeScreen(self, target_screen_type, target_screen_init_args: list):
        QApplication.instance().processEvents()
        self.stackedWidget.changeScreen_withSplash(target_screen_type, target_screen_init_args)
        QApplication.instance().processEvents()

    def change_to_SubConstructionScreen(self, subConstructionObject):
        from subConstruction_preview_SCRIPT import SubConstructPreviewScreen
        QApplication.instance().processEvents()
        self.stackedWidget.changeScreen_withSplash(SubConstructPreviewScreen, [subConstructionObject])

    def centerWindow(self, window: QWidget = None):
        self.move(QApplication.desktop().screen().rect().center() - self.rect().center())


if __name__ == '__main__':
    from mainWindow import DekiDesktopApp

    app = DekiDesktopApp(sys.argv)

    mainWindow = InspectionPlannerWindow()

    mainWindow.show()

    try:
        sys.exit(app.exec_())
    except:
        print("Exiting the App")
