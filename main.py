
from Screens.mainWindow import *


def main():
    app = QApplication(sys.argv)

    mainWindow = MainWindow()
    mainWindow.show()

    try:
        sys.exit(app.exec_())
    except:
        print("Exiting the App")


if __name__ == '__main__':
    main()
