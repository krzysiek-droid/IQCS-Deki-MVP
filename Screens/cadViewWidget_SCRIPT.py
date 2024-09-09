
import logging

from OCC.Core.AIS import AIS_Shape

from OCC.Core._Quantity import Quantity_TOC_RGB
from PyQt5.QtGui import QColor

import resources_rc

# Reads STEP files, checks them and translates their contents into Open CASCADE models
from OCC.Display.backend import load_backend
from OCC.Extend.DataExchange import read_step_file_with_names_colors

import sys
import ctypes
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.TopoDS import TopoDS_Compound, TopoDS_Solid, TopoDS_Iterator

from OCC.Core.IFSelect import IFSelect_RetDone
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QMainWindow, QTreeWidget, QTreeWidgetItem, QHBoxLayout, \
    QSplitter
from OCC.Core.Quantity import Quantity_Color as qc, Quantity_Color

log = logging.getLogger(__name__)
# Load the backend before initializing the display
used_backend = load_backend()
log.info("GUI backend set to: {0}".format(used_backend))
print("GUI backend set to: {0}".format(used_backend))
import OCC.Display.qtDisplay as qtDisplay

# TODO: add buttons for rotation of CAD Model etc.
class CadViewerLayout(QVBoxLayout):
    def __init__(self, step_filepath: str):
        super(CadViewerLayout, self).__init__()
        # self.setMinimumSize(viewport_width, viewport_height)
        # Class members
        self.display = None
        self.shape = None
        self.filepath = step_filepath

        # --------------------------------------------------CadViewer setup---------------------------------------------
        # Viewer init, define the widget's appearance, must be resized after definition to center itself
        # in widget container (layout)
        import OCC.Display.qtDisplay as qtDisplay
        self.canvas = qtDisplay.qtViewer3d()
        self.display = self.canvas._display
        # Nor canvas nor qtViewer3Container cannot be aligned, otherwise widget do not shows itself
        self.addWidget(self.canvas)
        # ---------------------------------------------------Buttons----------------------------------------------------

        # ------------------------------------------------Call class functions------------------------------------------
        self.read_stepFile(self.filepath)
        self.get_assembliesList()

    # ----------------------------------------------Class Functions---------------------------------------------------
    def read_stepFile(self, step_filepath):
        step_reader = STEPControl_Reader()
        status = step_reader.ReadFile(step_filepath)
        if status == IFSelect_RetDone:  # RetDone : normal execution with a result
            # to print stepByStep rendering:
            # step_reader.PrintCheckLoad(True, IFSelect_ItemsByEntity)
            step_reader.TransferRoot()
            self.shape = step_reader.Shape()

        else:
            print("Error: can't read file.")
            sys.exit(0)

    def start_display(self):
        self.canvas.InitDriver()
        from OCC.Core.Quantity import Quantity_Color as qc
        self.display.set_bg_gradient_color(qc(1, 1, 1, 0), qc(1, 1, 1, 0))
        from OCC.Core.Quantity import Quantity_Color
        self.display.DisplayColoredShape(self.shape,
                                         color=Quantity_Color(0.3, 0.3, 0.3, 0),  # fourth number means RGB
                                         update=True)
        self.display.FitAll()

    def get_assembliesList(self):
        shapes = read_step_file_with_names_colors(self.filepath)
        print(f"cadViewWidget_SCRIPT [get_assembliesList]: shapes: \n{shapes}")
        for key in shapes.keys():
            if type(key) is TopoDS_Compound:
                print(shapes[key])


class CadViewer(QWidget):
    opengl32 = ctypes.windll.opengl32
    wglDeleteContext = opengl32.wglDeleteContext

    def __init__(self, step_filepath: str):
        super(CadViewer, self).__init__()

        self.display = None
        self.shape = None
        self.filepath = step_filepath
        self.layout = QVBoxLayout()

        # Initialize qtDisplay and the canvas
        self.canvas = qtDisplay.qtViewer3d()
        self.display = self.canvas._display
        self.canvas.resize(200, 200)

        # Add canvas to the layout
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)

        # Read and display the STEP file
        self.read_stepFile(self.filepath)

    def closeEvent(self, QCloseEvent):
        super(CadViewer, self).closeEvent(QCloseEvent)
        self.wglDeleteContext(self.context().handle())
        QCloseEvent.accept()

    def read_stepFile(self, step_filepath):
        print(f"cadViewWidget_SCRIPT | CadViewer, func: read_step: Reading STEP file: {step_filepath}")
        step_reader = STEPControl_Reader()
        status = step_reader.ReadFile(step_filepath)
        if status == IFSelect_RetDone:  # RetDone : normal execution with a result
            step_reader.TransferRoot()
            self.shape = step_reader.Shape()
            print("cadViewWidget_SCRIPT | CadViewer, func: read_step: STEP file read successfully.")
        else:
            print("cadViewWidget_SCRIPT | CadViewer, func: read_step: Error: can't read file.")
            sys.exit(0)

    def start_display(self):
        self.canvas.InitDriver()
        self.display.set_bg_gradient_color(qc(1, 1, 1, 0), qc(1, 1, 1, 0))
        self.display.DisplayColoredShape(self.shape, color=qc(0.3, 0.3, 0.3, 0), update=True)
        self.display.FitAll()

    def get_assembliesList(self):
        shapes = self.read_step_file_with_names_colors(self.filepath)
        for key in shapes.keys():
            if isinstance(key, TopoDS_Compound):
                print(shapes[key])

    def read_step_file_with_names_colors(self, filepath):
        # Placeholder function, you need to implement the logic for reading STEP file with names and colors
        shapes = {}
        # Example logic to populate shapes with TopoDS_Compound and their properties
        # shapes[some_TopoDS_Compound] = some_property
        return shapes


class AdvancedCadViewer(QWidget):
    opengl32 = ctypes.windll.opengl32
    wglDeleteContext = opengl32.wglDeleteContext

    def __init__(self, step_filepath: str):
        super(AdvancedCadViewer, self).__init__()
        self.shape_tool = None
        self.shape_labels = None
        self.shapes = []
        self.display = None
        self.shape = None
        self.filepath = step_filepath
        self.splitter = QSplitter()

        # Initialize qtDisplay and the canvas
        self.cadViewerCanvas = qtDisplay.qtViewer3d()
        self.display = self.cadViewerCanvas._display
        self.cadViewerCanvas.resize(200, 200)

        # Create the QTreeWidget to display component hierarchy
        self.component_tree = QTreeWidget()
        self.component_tree.setHeaderLabels(["Component", "Type"])
        self.splitter.addWidget(self.component_tree)

        # Add canvas to the layout
        self.splitter.addWidget(self.cadViewerCanvas)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.splitter)

        # Read and display the STEP file
        self.read_stepFile(self.filepath)

        self.component_tree.itemDoubleClicked.connect(self.on_treeItem_clicked)

    def closeEvent(self, QCloseEvent):
        super(AdvancedCadViewer, self).closeEvent(QCloseEvent)
        self.wglDeleteContext(self.context().handle())
        QCloseEvent.accept()

    def read_stepFile(self, step_filepath):
        # app = XCAFApp_Application.GetApplication()
        # doc = TDocStd_Document("MDTV-XCAF")
        # app.NewDocument("MDTV-XCAF", doc)

        print(f"cadViewWidget_SCRIPT | CadViewer, func: read_step: Reading STEP file: {step_filepath}")
        step_reader = STEPControl_Reader()
        status = step_reader.ReadFile(step_filepath)

        if status == IFSelect_RetDone:  # RetDone : normal execution with a result
            step_reader.TransferRoot()
            # Populate the component tree
            self.populate_component_tree()
            # shape = step_reader.Shape()
            # self.shape: AIS_Shape = AIS_Shape(shape)
            # self.shape_tool = XCAFDoc_DocumentTool.ShapeTool(doc.Main())
            # self.shape_labels = TDF_LabelSequence()
            # self.shape_tool.GetFreeShapes(self.shape_labels)
            print("cadViewWidget_SCRIPT | CadViewer, func: read_step: STEP file read successfully.")
        else:
            print("cadViewWidget_SCRIPT | CadViewer, func: read_step: Error: can't read file.")
            sys.exit(0)

    # def start_display(self):
    #     self.cadViewerCanvas.InitDriver()
    #     self.display.set_bg_gradient_color(qc(1, 1, 1, 0), qc(1, 1, 1, 0))
    #     self.display.Context.Display(self.shape, True)
    #     self.display.FitAll()

    def display_shape(self, shape):
        """Convert TopoDS_Shape to AIS_Shape and display it."""
        ais_shape = AIS_Shape(shape)
        self.display.Context.Display(ais_shape, True)
        self.display.FitAll()
        return ais_shape


    def populate_component_tree(self):
        # Pobierz listę komponentów z pliku STEP
        shapes = read_step_file_with_names_colors(self.filepath)
        component_item = QTreeWidgetItem()
        for shape in list(shapes.items()):
            ais_shape = self.display_shape(shape[0])
            if isinstance(shape[0], TopoDS_Compound):
                component_item = QTreeWidgetItem(self.component_tree)
                component_item.setText(0, str(shape[1][0]))
                component_item.setText(1, "Assembly")
                new_shape = (str(shape[1][0]), ais_shape, 'Compound', component_item)
                self.shapes.append(new_shape)
            if isinstance(shape[0], TopoDS_Solid):
                sub_item = QTreeWidgetItem(component_item)
                sub_item.setText(0, str(shape[1][0]))
                sub_item.setText(1, "3D Object")
                new_shape = (str(shape[1][0]), ais_shape, '3D Object', sub_item)
                self.shapes.append(new_shape)

    def on_treeItem_clicked(self, item: QTreeWidgetItem):
        item.setSelected(True)
        item.setBackground(0, QColor(144, 238, 144))

        treeItems = self.get_all_tree_items()
        for otherItem in treeItems:
            if otherItem is not item:
                otherItem.setSelected(False)
                otherItem.setBackground(0, QColor(255, 255, 255))

        # Find the 3D object of which name has been selected on TreeWidget
        for shape_info in self.shapes:
            clicked_object = shape_info[1]
            if item == shape_info[3]:
                self.set_shape_color(clicked_object, QColor(0, 255, 00))
            else:
                clicked_object.UnsetColor()

    def get_all_tree_items(self):
        """
        Retrieves all QTreeWidgetItem objects from a QTreeWidget.

        Args:
            self.tree_widget (QTreeWidget): The QTreeWidget to retrieve items from.

        Returns:
            list: A list containing all QTreeWidgetItem objects in the tree.
        """

        def recursive_get_items(item):
            items = []
            child_count = item.childCount()
            for i in range(child_count):
                child = item.child(i)
                items.append(child)
                items.extend(recursive_get_items(child))
            return items
        # Initialize an empty list to store all items
        all_items = []
        # Iterate over all top-level items
        top_level_item_count = self.component_tree.topLevelItemCount()
        for i in range(top_level_item_count):
            top_item = self.component_tree.topLevelItem(i)
            all_items.append(top_item)
            all_items.extend(recursive_get_items(top_item))
        return all_items

    def set_shape_color(self, ais_shape: AIS_Shape, color: QColor):
        """Ustawienie koloru dla danego obiektu AIS_Shape."""
        # Konwersja koloru PyQt na kolor Open Cascade
        occ_color = Quantity_Color(color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0, Quantity_TOC_RGB)
        ais_shape.SetColor(occ_color)  # Ustawienie koloru
        self.display.Context.Redisplay(ais_shape, True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = QMainWindow()
    nw = AdvancedCadViewer("../DekiResources/Zbiornik LNG assembly.stp")


    # nw.start_display()
    mw.setCentralWidget(nw)
    mw.show()
    mw.resize(1200, 900)

    try:
        sys.exit(app.exec_())
    except:
        print("Exiting the App")
