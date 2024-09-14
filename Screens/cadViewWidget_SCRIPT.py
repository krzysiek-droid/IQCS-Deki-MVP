import logging

from OCC.Core.AIS import AIS_Shape, AIS_InteractiveContext

from OCC.Core.STEPCAFControl import STEPCAFControl_Reader
from OCC.Core.TCollection import TCollection_ExtendedString
from OCC.Core.TDF import TDF_LabelSequence, TDF_Label, TDF_Attribute, TDF_Data
from OCC.Core.TDataStd import TDataStd_Name
from OCC.Core.TDocStd import TDocStd_Document
from OCC.Core.XCAFDoc import XCAFDoc_DocumentTool

from OCC.Core._Quantity import Quantity_TOC_RGB
from PyQt5.QtCore import QEvent
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


class CustomShapeAIS(AIS_Shape):
    def __init__(self, name, topo_shape, location, topo_type, treeItem, parent_AIS_shape):
        super(CustomShapeAIS, self).__init__(topo_shape)
        self.name = name
        self.topo_shape = topo_shape
        self.location = location
        self.topo_type = topo_type
        self.treeItem = treeItem
        self.parent_shape = parent_AIS_shape
        self.childrenShapes = []

    def __repr__(self):
        return f"CustomShapeAIS(name={self.name})"

    def add_ChildShape(self, shape):
        self.childrenShapes.append(shape)

    def isCompound(self):
        if self.topo_type == 'TopAbs_COMPOUND' or self.topo_type == 0:
            return True
        else:
            return False


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
        self.previously_highlighted = None
        self.current_hovered_item = None
        self.tree_items = []
        self.shape_tool: XCAFDoc_DocumentTool.ShapeTool = None
        self.shape_labels = None
        self.shapes = []
        self.shapes_dict = dict()
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
        self.component_tree.setMouseTracking(True)
        self.splitter.addWidget(self.component_tree)

        # Add canvas to the layout
        self.splitter.addWidget(self.cadViewerCanvas)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.splitter)

        # Read and display the STEP file
        self.read_stepFile(self.filepath)
        # self.populate_component_tree()

        self.component_tree.itemDoubleClicked.connect(self.on_treeItem_clicked)
        self.component_tree.itemEntered.connect(self.on_treeItem_enter)

        for shape in self.shapes:
            if len(shape.childrenShapes) == 0:
                self.display_shape(shape)

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
        self.step_reader.SetNameMode(True)
        status = self.step_reader.ReadFile(step_filepath)
        if status == IFSelect_RetDone:  # RetDone : normal execution with a result
            self.step_reader.Transfer(doc)
            labels = TDF_LabelSequence()
            self.shape_tool.GetFreeShapes(labels)
            for i in range(labels.Length()):
                root_shape_label: TDF_Label = labels.Value(i + 1)  # Typically there will be only 1 shape
                root_topo_shape = self.shape_tool.GetShape(root_shape_label)
                self.add_topoShape(root_topo_shape)
                self.get_subComponents(root_topo_shape, self.shapes[-1])
            print("cadViewWidget_SCRIPT | CadViewer, func: read_step: STEP file read successfully.")
        else:
            print("cadViewWidget_SCRIPT | CadViewer, func: read_step: Error: can't read file.")
            sys.exit(0)

    def get_subComponents(self, shape_topoDS, root_Shape):
        """
        Recursively iterates over the subcomponents of the provided TopoDS_Shape
        and adds them to a tree structure.
        """
        # Initialize the iterator for the given shape
        iterator = TopoDS_Iterator(shape_topoDS)
        while iterator.More():
            child_shape = iterator.Value()
            self.add_topoShape(child_shape, root_Shape)
            # Check if the child shape is a compound (or any type that could contain sub-shapes)
            if child_shape.ShapeType() == self.shape_enum_dict['TopAbs_COMPOUND']:
                parent_Shape = self.shapes[-1]  # Get the latest added item for parent-child relation
                # Recursive call to handle nested subcomponents
                self.get_subComponents(child_shape, parent_Shape)
            # Move to the next child shape
            iterator.Next()

    def add_topoShape(self, topo_shape, parent_Shape=None):

        if topo_shape.ShapeType() is self.shape_enum_dict['TopAbs_COMPOUND'] and topo_shape.NbChildren() < 1:
            print(f'Empty Assembly found. -> {self.shape_tool.FindShape(topo_shape).GetLabelName()}')
            return 0  # skip empty assemblies

        if parent_Shape is None:    # Means that topo_shape is root
            component_item = QTreeWidgetItem(self.component_tree)
        else:
            component_item = QTreeWidgetItem(parent_Shape.treeItem)


        shape_label: TDF_Label = self.shape_tool.FindShape(topo_shape)  # Get shape label
        if shape_label.IsNull():    # Can't find a label corresponding to shape - we need to add that one to shape_tool
            new_label = self.shape_tool.AddShape(topo_shape)    # Add shape to shape_tool, generating its label
            # New label for the shape
            label_name = f"{parent_Shape.name}_{len(self.shapes) - self.shapes.index(parent_Shape)}"
            # Change label corresponding to added shape
            self.change_label_name(new_label, label_name)
            shape_label = new_label

        shape_type = self.translate_shape(topo_shape.ShapeType())
        shape_name = shape_label.GetLabelName()
        shape_location = self.shape_tool.GetLocation(shape_label)
        component_item.setText(0, shape_name)
        component_item.setText(1, shape_type)
        new_shape = CustomShapeAIS(shape_name, topo_shape, shape_location, shape_type, component_item,
                                   parent_Shape)
        if parent_Shape is not None:
            parent_Shape.add_ChildShape(new_shape)
        self.shapes.append(new_shape)
        print(f"adViewWidget_SCRIPT | AdvancedCadViewer, func: add_topoShape: New Shape added - {new_shape.name}")
        return topo_shape

    def change_label_name(self, label: TDF_Label, new_name):
        """Changes the TDF_Label name"""
        name_id = TDataStd_Name.GetID()
        if label.IsAttribute(name_id):
            name_attr = TDataStd_Name.Set(label, new_name)
            print(f"Utworzono nową nazwę etykiety: {new_name}")

    def display_shape(self, ais_shape: AIS_Shape):
        """Convert TopoDS_Shape to AIS_Shape and display it."""
        self.display.Context.Display(ais_shape, True)
        self.display.FitAll()
        return ais_shape

    def on_treeItem_clicked(self, item: QTreeWidgetItem):
        item.setSelected(True)
        item.setBackground(0, QColor(144, 238, 144))

        treeItems = self.get_all_tree_items()
        for otherItem in treeItems:
            if otherItem is not item:
                otherItem.setSelected(False)
                otherItem.setBackground(0, QColor(255, 255, 255))

        # Find the 3D object of which name has been selected on TreeWidget
        for shape in self.shapes:
            if item == shape.treeItem:
                self.set_shape_color(shape, QColor(0, 255, 00))
            else:
                shape.UnsetColor()

    def on_treeItem_enter(self, item: QTreeWidgetItem, column: int):

        if self.previously_highlighted is not None:
            if type(self.previously_highlighted) is not list:
                self.display.Context.Unhilight(self.previously_highlighted, True)
            else:
                for previosuly_hilighted in self.previously_highlighted:
                    self.display.Context.Unhilight(previosuly_hilighted, True)


        for shape in self.shapes:
            if item == shape.treeItem and not shape.isCompound():
                self.display.Context.Hilight(shape, True)
                self.previously_highlighted = shape

            elif item == shape.treeItem and shape.isCompound():
                print(f"is compound -> {shape.name} -> {shape.childrenShapes}")
                self.previously_highlighted = []
                for child_shape in shape.childrenShapes:
                    self.display.Context.Hilight(child_shape, True)
                    self.previously_highlighted.append(child_shape)

    def get_all_tree_items(self, force_update=False):
        """
        Retrieves or updates all QTreeWidgetItem objects from a QTreeWidget.
        """
        if len(self.tree_items) == 0 and not force_update:
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

            self.tree_items = all_items
            return all_items
        else:
            return self.tree_items

    def set_shape_color(self, ais_shape: AIS_Shape, color: QColor):
        """Ustawienie koloru dla danego obiektu AIS_Shape."""
        # Konwersja koloru PyQt na kolor Open Cascade
        if ais_shape.DisplayStatus():
            occ_color = Quantity_Color(color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0,
                                       Quantity_TOC_RGB)
            ais_shape.SetColor(occ_color)  # Ustawienie koloru
            self.display.Context.Redisplay(ais_shape, True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = QMainWindow()
    step_sample_path = r"../DekiResources/Zbiornik LNG assembly.stp"
    # nwg = fr"C:\Users\Młody\Desktop\[Srv] Deki\Projekty\NWG\Sciana 58We\58WE-POM_031100-2-00#Sciana_prawa.stp"
    nw = AdvancedCadViewer(step_sample_path)
    # nw = AdvancedCadViewer(nwg)

    # nw.start_display()
    mw.setCentralWidget(nw)
    mw.show()
    mw.resize(1200, 900)

    try:
        sys.exit(app.exec_())
    except:
        print("Exiting the App")
