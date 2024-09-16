import logging
import math

from OCC.Core.AIS import AIS_Shape, AIS_InteractiveContext, AIS_InteractiveObject
from OCC.Core.Aspect import Aspect_TOL_SOLID
from OCC.Core.BRep import BRep_Tool_Surface, BRep_Tool
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Section
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeVertex, BRepBuilderAPI_Transform, \
    BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
from OCC.Core.BRepGProp import brepgprop_SurfaceProperties, brepgprop
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakePipe
from OCC.Core.BRepTools import breptools_UVBounds
from OCC.Core.GProp import GProp_GProps
from OCC.Core.Geom import Geom_Surface, Geom_Plane
from OCC.Core.GeomAPI import GeomAPI_IntSS
from OCC.Core.GeomAbs import GeomAbs_Plane
from OCC.Core.Graphic3d import Graphic3d_MaterialAspect
from OCC.Core.Prs3d import Prs3d_Drawer

from OCC.Core.STEPCAFControl import STEPCAFControl_Reader
from OCC.Core.TCollection import TCollection_ExtendedString
from OCC.Core.TDF import TDF_LabelSequence, TDF_Label, TDF_Attribute, TDF_Data
from OCC.Core.TDataStd import TDataStd_Name
from OCC.Core.TDocStd import TDocStd_Document
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.XCAFDoc import XCAFDoc_DocumentTool
from OCC.Core._Graphic3d import Graphic3d_NOM_STEEL

from OCC.Core._Quantity import Quantity_TOC_RGB
from OCC.Core.gp import gp_Trsf, gp_Vec, gp_Ax2, gp_Pnt, gp_Dir, gp_Ax3
from OCP.Graphic3d import Graphic3d_ZLayerId_Top
from PyQt5.uic import loadUi
from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QColor

import resources_rc

# Reads STEP files, checks them and translates their contents into Open CASCADE models
from OCC.Display.backend import load_backend
from OCC.Extend.DataExchange import read_step_file_with_names_colors, read_step_file

import sys
import ctypes
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.TopoDS import TopoDS_Compound, TopoDS_Solid, TopoDS_Iterator, TopoDS_Shape, topods_Face, topods, \
    TopoDS_Edge, TopoDS_Face

from OCC.Core.IFSelect import IFSelect_RetDone
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QMainWindow, QTreeWidget, QTreeWidgetItem, QHBoxLayout, \
    QSplitter, QSizePolicy, QFrame
from OCC.Core.Quantity import Quantity_Color as qc, Quantity_Color, Quantity_NOC_BLUE1

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
        loadUi(r'cadModule.ui', self)
        self.selectedShape = None
        self.hilightedShape = None
        self.current_hovered_item = None
        self.tree_items = []
        self.shape_tool: XCAFDoc_DocumentTool.ShapeTool = None
        self.shape_labels = None
        self.shapes = []
        self.shapes_dict = dict()
        self.display = None
        self.shape = None
        self.filepath = step_filepath
        self.selected_faces = []
        self.parent_shapes = []

        # Initialize qtDisplay and the canvas
        self.cadViewerCanvas = qtDisplay.qtViewer3d()
        self.display = self.cadViewerCanvas._display
        self.drawer = self.display.Context.DefaultDrawer()
        self.display.set_bg_gradient_color(Quantity_Color(1, 1, 1, Quantity_TOC_RGB),
                                           Quantity_Color(155 / 255, 1, 190 / 255, Quantity_TOC_RGB))

        # Create the QTreeWidget to display component hierarchy
        self.component_tree = QTreeWidget()
        self.component_tree.setHeaderLabels(["Component", "Type"])
        self.component_tree.setMouseTracking(True)
        self.splitter.addWidget(self.component_tree)

        # Add canvas to the layout
        self.splitter.addWidget(self.cadViewerCanvas)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.splitter)

        self.rightFrame.setParent(None)
        self.splitter.addWidget(self.rightFrame)
        self.rightFrame.setMinimumWidth(20)

        self.buttonsBox.setParent(None)
        self.mainVLayout.addWidget(self.buttonsBox)

        self.rightFrameExpandBtn.clicked.connect(self.expandRightFrame)
        self.btn_1.clicked.connect(self.startAddingWeld)

        # Read and display the STEP file
        self.read_stepFile(self.filepath)

        self.component_tree.itemClicked.connect(self.on_treeItem_clicked)
        self.component_tree.itemEntered.connect(self.on_treeItem_enter)

        for shape in self.shapes:
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

        if parent_Shape is None:  # Means that topo_shape is root
            component_item = QTreeWidgetItem(self.component_tree)
        else:
            component_item = QTreeWidgetItem(parent_Shape.treeItem)
        shape_label: TDF_Label = self.shape_tool.FindShape(topo_shape)  # Get shape label
        if shape_label.IsNull():  # Can't find a label corresponding to shape - we need to add that one to shape_tool
            new_label = self.shape_tool.AddShape(topo_shape)  # Add shape to shape_tool, generating its label
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
        # self.set_shape_color(ais_shape, QColor(140, 140, 140))
        steel_material = Graphic3d_MaterialAspect(Graphic3d_NOM_STEEL)
        ais_shape.SetMaterial(steel_material)
        self.display.Context.Display(ais_shape, True)
        self.display.FitAll()
        return ais_shape

    def on_treeItem_clicked(self, item: QTreeWidgetItem):
        item.setSelected(True)
        if self.hilightedShape is not None:
            self.display.Context.Unhilight(self.hilightedShape, True)
            self.hilightedShape = None
        for shape in self.shapes:
            if item == shape.treeItem:
                self.display.Context.SetSelected(shape, True)
                self.selectedShape = shape
                break

    def on_treeItem_enter(self, item: QTreeWidgetItem):
        if self.hilightedShape is not None:
            self.display.Context.Unhilight(self.hilightedShape, True)
            if self.hilightedShape == self.selectedShape:
                self.display.Context.SetSelected(self.selectedShape, True)
            self.hilightedShape = None

        for shape in self.shapes:
            if item == shape.treeItem:
                self.drawer.SetColor(Quantity_Color(250 / 255, 165 / 255, 0 / 255, Quantity_TOC_RGB))
                self.display.Context.HilightWithColor(shape, self.drawer, True)
                self.hilightedShape = shape
                break

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
        occ_color = Quantity_Color(color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0,
                                   Quantity_TOC_RGB)
        ais_shape.SetColor(occ_color)
        self.display.Context.UpdateCurrentViewer()

    def expandRightFrame(self):
        if self.rightFrameExpandBtn.text() == "<":
            self.rightFrame.setFixedWidth(250)

            self.rightFrameExpandBtn.setText(">")
        else:
            self.rightFrame.setFixedWidth(30)
            self.rightFrameExpandBtn.setText("<")

    def startAddingWeld(self):
        try:
            self.expandRightFrame()
            self.display.Context.Deactivate()
            self.display.Context.Activate(TopAbs_FACE)
            self.display.register_select_callback(self.select_face)
        except Exception as exc:
            print(f"error -> {exc}")

    def select_face(self, shape, x, y):
        try:
            # Get the selected shape
            selected = shape[0]
            if selected.IsNull():
                return
            # Check if the selected shape is a face
            if selected.ShapeType() == TopAbs_FACE:
                face = topods.Face(selected)
                # Store the selected face
                self.selected_faces.append(face)
                # Get the owner AIS_Shape
                owner = self.display.Context.SelectedInteractive()
                self.parent_shapes.append(owner)
                print(f"Face selected: {face} - Face owner shaper {owner}")

                if len(self.selected_faces) == 2:
                    # We have two faces selected, proceed to create the edge
                    self.create_edge_from_faces(self.selected_faces[0], self.selected_faces[1])
                    # Clear the selection
                    self.selected_faces.clear()
                    self.parent_shapes.clear()
                    # Optionally, reset the selection
                    self.display.Context.ClearSelected(True)
        except Exception as exc:
            print(f"error -> {exc}")

    def create_edge_from_faces(self, face1, face2):
        face1 = self.create_infinite_plane(face1)
        if face1 is None:
            return 0
        # Oblicz środek geometryczny pierwszej powierzchni
        props1 = GProp_GProps()
        brepgprop.SurfaceProperties(face1, props1)
        center1 = props1.CentreOfMass().XYZ()

        # Oblicz środek geometryczny drugiej powierzchni
        props2 = GProp_GProps()
        brepgprop.SurfaceProperties(face2, props2)
        center2 = props2.CentreOfMass().XYZ()

        # Skalowanie powierzchni o 120% względem ich środków
        scale_factor = 1.0
        trsf1 = gp_Trsf()
        p1 = gp_Pnt(center1)
        p1.Translate(gp_Vec(0, 0, 1))
        trsf1.SetScale(p1, scale_factor)
        trsf2 = gp_Trsf()
        p2 = gp_Pnt(center2)
        p2.Translate(gp_Vec(0, 0, 1))
        trsf2.SetScale(p2, scale_factor)

        # Zastosowanie transformacji do powierzchni
        scaled_face1 = BRepBuilderAPI_Transform(face1, trsf1, True).Shape()
        scaled_face2 = BRepBuilderAPI_Transform(face2, trsf2, True).Shape()

        # Użycie GeomAPI_IntSS do obliczenia przecięcia między dwoma skalowanymi powierzchniami
        surface1 = BRep_Tool.Surface(scaled_face1)
        surface2 = BRep_Tool.Surface(scaled_face2)
        intersector = GeomAPI_IntSS(surface1, surface2, 1e-6)

        if intersector.NbLines() > 0:
            # Istnieje krzywa przecięcia
            geom_curve = intersector.Line(1)
            edge = BRepBuilderAPI_MakeEdge(geom_curve).Edge()
            edge = AIS_Shape(edge)
            edge.SetColor(Quantity_Color(1, 0, 0, Quantity_TOC_RGB))
            # Ustawienie grubości i stylu linii (opcjonalne)
            line_aspect = edge.Attributes().LineAspect()
            line_aspect.SetColor(Quantity_Color(1, 0, 0, Quantity_TOC_RGB))
            line_aspect.SetWidth(2.0)  # Ustaw grubość linii

            # self.display.Context.Display(edge, True)
            # self.display.FitAll()
            self.add_triangle_geometry(edge)

            print("Intersection Edge created.")
        else:
            print(f"No intersection found.")
            return 0

        return edge

    def add_triangle_geometry(self, edge_ais_shape):
        # Extract the TopoDS_Edge from the AIS_Shape
        edge: TopoDS_Edge = edge_ais_shape.Shape()

        # Get the underlying curve and its parameter range
        curve_handle, first_param, last_param = BRep_Tool.Curve(edge)
        if curve_handle is None:
            print("Error: Edge does not have an underlying curve.")
            return

        # Choose a parameter (e.g., middle of the edge)
        mid_param = (first_param + last_param) / 2.0

        # Get the point and tangent direction at the chosen parameter
        pnt = curve_handle.Value(mid_param)
        curve_adaptor = BRepAdaptor_Curve(edge)
        dir_vec = curve_adaptor.DN(mid_param, 1)  # First derivative (tangent vector)

        if dir_vec.Magnitude() == 0:
            print("Error: Zero magnitude tangent vector.")
            return

        dir_norm = gp_Dir(dir_vec)

        # Create a coordinate system (Ax2) at the point, with Z axis along the edge direction
        # Determine an appropriate X direction perpendicular to the Z axis
        # If dir_norm is parallel to (0, 0, 1), choose a different reference direction
        ref_dir = gp_Dir(0, 0, 1)
        if abs(dir_norm.Dot(ref_dir)) > 0.999:
            ref_dir = gp_Dir(1, 0, 0)
        x_dir_vec = dir_norm.Crossed(ref_dir)
        y_dir = dir_norm.Crossed(x_dir_vec)
        ax3 = gp_Ax3(pnt, dir_norm, x_dir_vec)

        # Define the equilateral triangle parameters
        height = 8.0  # Height in mm
        side_length = (2.0 / math.sqrt(3.0)) * height  # Calculate side length

        # Define the triangle vertices in local coordinates
        # Vertex at the origin (on the edge)
        p1 = gp_Pnt(0, 0, 0)
        # Base vertices
        p2 = gp_Pnt(-side_length / 2.0, -height, 0)
        p3 = gp_Pnt(side_length / 2.0, -height, 0)

        # Create edges of the triangle
        edge1 = BRepBuilderAPI_MakeEdge(p1, p2).Edge()
        edge2 = BRepBuilderAPI_MakeEdge(p2, p3).Edge()
        edge3 = BRepBuilderAPI_MakeEdge(p3, p1).Edge()

        # Create a wire from the edges
        wire_maker = BRepBuilderAPI_MakeWire()
        wire_maker.Add(edge1)
        wire_maker.Add(edge2)
        wire_maker.Add(edge3)
        triangle_wire = wire_maker.Wire()

        # Transform the triangle to the coordinate system at the point on the edge
        trsf = gp_Trsf()
        trsf.SetTransformation(ax3)
        transformed_wire = BRepBuilderAPI_Transform(triangle_wire, trsf).Shape()

        # Sweep the triangle along the edge to create the solid
        pipe_maker = BRepOffsetAPI_MakePipe(transformed_wire, edge)
        pipe_maker.Build()
        if not pipe_maker.IsDone():
            print("Error: Failed to build the pipe.")
            return
        solid = pipe_maker.Shape()

        # Display the solid
        ais_solid = AIS_Shape(solid)
        # Optional: Set the color of the solid
        ais_solid.SetColor(Quantity_Color(0, 0.8, 0, Quantity_TOC_RGB))
        self.display.Context.Display(ais_solid, True)
        self.display.FitAll()


    def create_infinite_plane(self, face: TopoDS_Face):
        # Get surface from TopoDS_Face
        surface = BRep_Tool.Surface(face)
        # Check whether surface is in fact plane
        if surface.DynamicType().Name() != 'Geom_Plane':
            print("Selected face is not a plane.")
            return None
        plane = Geom_Plane.DownCast(surface)
        gp_plane = plane.Pln()
        u_min, u_max = -1e4, 1e4
        v_min, v_max = -1e4, 1e4
        big_face = BRepBuilderAPI_MakeFace(gp_plane, u_min, u_max, v_min, v_max).Face()
        # ais_plane = AIS_Shape(big_face)
        # plane_color = Quantity_Color(0.8, 0.8, 0.8, Quantity_TOC_RGB)  # Jasnoszary kolor
        # ais_plane.SetColor(plane_color)
        # ais_plane.SetTransparency(0.7)  # Ustawienie przezroczystości
        # self.display.Context.Display(ais_plane, False)

        return big_face


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
