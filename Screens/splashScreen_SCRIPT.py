import sys, time

from PyQt5.QtCore import Qt, QRunnable, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QApplication, QStackedWidget, QDialog
from PyQt5 import uic

import logging
import resources_rc

counter = 0


# Has to be different class since QT does not support multiple inheritance from multiple QObjects
class WorkerSignals(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal()


class Worker(QRunnable):
    def __init__(self):
        super(Worker, self).__init__()
        self.signals = WorkerSignals()

    def run(self):
        cnt = 0
        while cnt < 100:
            self.signals.progress.emit(cnt)
            time.sleep(0.3)
            cnt += 1
        else:
            self.signals.finished.emit()


class SplashScreenDialog(QDialog):
    def __init__(self, stackedWidgetInstance, called_screen, called_screen_initArgs):
        super(SplashScreenDialog, self).__init__()
        self.calledScreen = called_screen
        self.calledScreen_initArgs = called_screen_initArgs
        self.mainAppInstance = QApplication.instance()
        self.finishSignal = None

        self.counter = 0

        self.loadedScreen = None
        uic.properties.logger.setLevel(logging.WARNING)
        uic.uiparser.logger.setLevel(logging.WARNING)
        uic.loadUi(r'splashScreen_UI.ui', self)

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # self.animation = QMovie(r'D:\CondaPy - Projects\PyGUIs\DekiApp_pyqt5\Icons\31.gif')
        # self.loadingLbl.setMovie(self.animation)

        self.stackedWidget: QStackedWidget = stackedWidgetInstance
        print(f"SHOWING SPLASH...", end=" ")
        self.show()
        self.mainAppInstance.processEvents()
        print(f"LOADING NEXT SCREEN -> {self.calledScreen}", end="...")
        try:
            self.loadedScreen = self.calledScreen(*self.calledScreen_initArgs)
        except Exception as e:
            print(f"Screen loading during Splash failure err-> {e}")
            self.reject()
        self.mainAppInstance.processEvents()
        print(f"CHANGING SCREENS...", end=' ')
        self.changeScreen()
        self.mainAppInstance.processEvents()
        print(f"DONE. SPLASH FINISHED.")

    def changeScreen(self):
        if self.loadedScreen:
            self.stackedWidget.addWidget(self.loadedScreen)
            currentScreen = self.stackedWidget.currentWidget()
            self.stackedWidget.setCurrentIndex(self.stackedWidget.currentIndex() + 1)
            self.stackedWidget.removeWidget(currentScreen)
            currentScreen.deleteLater()
            self.mainAppInstance.processEvents()
        else:
            print('Next screen has not been loaded.')

    def startAnimation(self):
        self.animation.start()

    def stopAnimation(self):
        self.animation.stop()

    # Cant make it work...
    def processThread(self):
        worker = Worker()
        worker.signals.progress.connect(self.update_progress)
        worker.signals.finished.connect(self.finishSplash)
        self.threadpool.start(worker)

    @pyqtSlot(int)
    def update_progress(self, progressValue):
        self.progressBar.setValue(progressValue)

    @pyqtSlot()
    def finishSplash(self):
        if self.loadedScreen is not None:
            self.finishSignal = 1


if __name__ == '__main__':
    app = QApplication(sys.argv)
    from inspectionPlannerWindow_SCRIPT import InspectionPlannerWindow

    # mainWindowObj = InspectionPlannerWindow()
    # mainWindowObj.show()

    try:
        sys.exit(app.exec_())
    except:
        print("Exiting the App")
