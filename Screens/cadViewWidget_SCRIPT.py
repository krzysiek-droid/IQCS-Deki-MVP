
import logging

from OCC.Core.AIS import AIS_Shape
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.STEPCAFControl import STEPCAFControl_Reader
from OCC.Core.TDF import TDF_LabelSequence, TDF_Label, TDF_ChildIterator, TDF_ChildIDIterator
from OCC.Core.TDocStd import TDocStd_Document
from OCC.Core.TopAbs import TopAbs_ShapeEnum
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.XCAFDoc import XCAFDoc_DocumentTool
from OCC.Core._IFSelect import IFSelect_ItemsByEntity
from OCC.Display.wxDisplay import wxViewer3d

from OCC.Core._Quantity import Quantity_TOC_RGB
from PyQt5.QtGui import QColor

import resources_rc

# Reads STEP files, checks them and translates their contents into Open CASCADE models
from OCC.Display.backend import load_backend
from OCC.Extend.DataExchange import read_step_file_with_names_colors, read_step_file

import sys
import ctypes
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.TopoDS import TopoDS_Compound, TopoDS_Solid, TopoDS_Iterator, TopoDS_Shape

from OCC.Core.IFSelect import IFSelect_RetDone
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QMainWindow, QTreeWidget, QTreeWidgetItem, QHBoxLayout, \
    QSplitter, QSizePolicy
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


class AdvancedCadViewer(QWidget):
    opengl32 = ctypes.windll.opengl32
    wglDeleteContext = opengl32.wglDeleteContext

    shape_enum_dict = {
        'TopAbs_COMPOUND': 0,
        'TopAbs_COMPSOLID': 1,
        'TopAbs_SOLID': 2,
        'TopAbs_SHELL': 3,
        'TopAbs_FACE': 4,
        'TopAbs_WIRE': 5,
        'TopAbs_EDGE': 6,
        'TopAbs_VERTEX': 7,
        'TopAbs_SHAPE': 8}

    def translate_shape(self, value):
        if value is str:
            return self.shape_enum_dict[value]
        else:
            for stype, ival in self.shape_enum_dict.items():  # Get name of shape type
                if ival == value:
                    return stype

    def __init__(self, step_filepath: str):
        super(AdvancedCadViewer, self).__init__()
        self.shape_tool: XCAFDoc_DocumentTool.ShapeTool = None
        self.shape_labels = None
        self.shapes = []
        self.display = None
        self.shape = None
        self.filepath = step_filepath
        self.splitter = QSplitter()

        # Initialize qtDisplay and the canvas
        self.cadViewerCanvas = qtDisplay.qtViewer3d()
        self.display = self.cadViewerCanvas._display

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
        #self.populate_component_tree()

        self.component_tree.itemDoubleClicked.connect(self.on_treeItem_clicked)
        for shape in self.shapes[1:]:
            self.display_shape(shape[1])

    def closeEvent(self, QCloseEvent):
        super(AdvancedCadViewer, self).closeEvent(QCloseEvent)
        self.wglDeleteContext(self.context().handle())
        QCloseEvent.accept()

    def read_stepFile(self, step_filepath):
        doc = TDocStd_Document("pythonocc-doc-step-import")
        self.shape_tool = XCAFDoc_DocumentTool.ShapeTool(doc.Main())
        color_tool = XCAFDoc_DocumentTool.ColorTool(doc.Main())
        print(f"cadViewWidget_SCRIPT | AdvancedCadViewer, func: read_step: Reading STEP file: {step_filepath}")
        self.step_reader = STEPCAFControl_Reader()
        #self.step_reader.SetColorMode(True)
        #self.step_reader.SetLayerMode(True)
        self.step_reader.SetNameMode(True)
        #self.step_reader.SetMatMode(True)
        #self.step_reader.SetGDTMode(True)

        status = self.step_reader.ReadFile(step_filepath)
        if status == IFSelect_RetDone:  # RetDone : normal execution with a result
            self.step_reader.Transfer(doc)

            labels = TDF_LabelSequence()
            self.shape_tool.GetFreeShapes(labels)
            for i in range(labels.Length()):
                root_shape_label: TDF_Label = labels.Value(i + 1)    # Typically there will be only 1 shape
                self.add_shape(root_shape_label)
                self.get_subShapes(root_shape_label, self.shapes[-1][-1])
            print("cadViewWidget_SCRIPT | CadViewer, func: read_step: STEP file read successfully.")
        else:
            print("cadViewWidget_SCRIPT | CadViewer, func: read_step: Error: can't read file.")
            sys.exit(0)

    def get_subShapes(self, shape_label, TreeItem_parent):
        subCompounds_labels = TDF_LabelSequence()
        self.shape_tool.GetComponents(shape_label, subCompounds_labels)
        for i in range(subCompounds_labels.Length()):   # Iterate over the shapes found in passed shape_label
            subCompound_label = subCompounds_labels.Value(i + 1)    # take the TDF_Label of an object in list
            if self.shape_tool.IsReference(subCompound_label):      # filter to reject all potential names not related to shapes
                topo_shape = self.add_shape(subCompound_label, TreeItem_parent) # add shape to class memory
                if topo_shape.ShapeType() == self.shape_enum_dict['TopAbs_COMPOUND'] and topo_shape.NbChildren() > 1:   # if shape is Assembly go through its subassmblies
                    parent_treeItem = self.shapes[-1][-1]
                    iterator = TopoDS_Iterator(topo_shape)
                    print(f"shape -> {subCompound_label.GetLabelName()} - {subCompound_label.NbChildren()}")
                    while iterator.More():
                        child_topoShape = iterator.Value()
                        child_label = self.shape_tool.FindShape(child_topoShape)
                        print(f"is null? {child_label.IsNull()}")
                        topo_shape = self.add_shape(child_label, parent_treeItem)
                        if child_topoShape.ShapeType() is self.shape_enum_dict['TopAbs_COMPOUND']:
                            self.get_subShapes(child_label, self.shapes[-1][-1])
                        iterator.Next()
        return 1

    def add_shape(self, shapeLabel: TDF_Label, itemParent=None):
        if not shapeLabel.IsNull():
            if itemParent is None:
                component_item = QTreeWidgetItem(self.component_tree)
            else:
                component_item = QTreeWidgetItem(itemParent)
            try:
                shape_name = shapeLabel.GetLabelName()
                shape = self.shape_tool.GetShape(shapeLabel)
                shape_location = self.shape_tool.GetLocation(shapeLabel)
                shape_type = self.translate_shape(shape.ShapeType())
                component_item.setText(0, shape_name)
                component_item.setText(1, shape_type)
                new_shape = (shape_name, AIS_Shape(shape), shape_location, shape_type, component_item)
                self.shapes.append(new_shape)
                print(f"adViewWidget_SCRIPT | AdvancedCadViewer, func: add_shape: New Shape added - {new_shape}")
                return shape
            except Exception as exc:
                print(f"Couldnt add new item -> {shapeLabel.HasAttribute()}")

    def display_shape(self, ais_shape):
        """Convert TopoDS_Shape to AIS_Shape and display it."""
        self.display.Context.Display(ais_shape, True)
        self.display.FitAll()
        return ais_shape

    def populate_component_tree(self):
        # Pobierz listę komponentów z pliku STEP
        shapes = read_step_file_with_names_colors(self.filepath)
        print(shapes)

        component_item = QTreeWidgetItem()
        for shape in list(shapes.items()):
            ais_shape = self.display_shape(shape[0])
            print(f"TopoDS shape -> {type(shape[0])} - AIS shape -> {ais_shape.Type()}")
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
            if item == shape_info[-1]:
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
    #nwg = fr"C:\Users\Młody\Desktop\[Srv] Deki\Projekty\NWG\Sciana 58We\58WE-POM_031100-2-00#Sciana_prawa.stp"
    nw = AdvancedCadViewer("../DekiResources/Zbiornik LNG assembly.stp")
    #nw = AdvancedCadViewer(nwg)

    # nw.start_display()
    mw.setCentralWidget(nw)
    mw.show()
    mw.resize(1200, 900)

    try:
        sys.exit(app.exec_())
    except:
        print("Exiting the App")
