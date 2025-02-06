import os

from PyQt5 import QtCore, QtGui, QtWidgets

from ...model.project import Project
from ...model.event import PLANNING_EVENT_TYPE_ID, AS_BUILT_EVENT_TYPE_ID, DESIGN_EVENT_TYPE_ID, PLANNING_MACHINE_CODE, AS_BUILT_MACHINE_CODE, DESIGN_MACHINE_CODE
from ...model.layer import Layer

from ...QRiS.settings import Settings
from ...QRiS.protocol_parser import load_protocols

from ..frm_event_picker import FrmEventPicker

DATA_CAPTURE_EVENT_TYPE_ID = 1

class LayerTreeWidget(QtWidgets.QWidget):
    def __init__(self, parent, qris_project:Project, event_type_id: int, mandatory_layers=None):
        super(LayerTreeWidget, self).__init__(parent)
        
        self.qris_project = qris_project
        self.event_type_id = event_type_id
        self.mandatory_layers = mandatory_layers
        
        settings = Settings()
        protocol_directory = settings.getValue('protocolsDir')
        qris_protoccols = load_protocols(protocol_directory)
        project_directory = os.path.dirname(self.qris_project.project_file)
        local_protocols = load_protocols(project_directory)

        self.protocols = local_protocols + qris_protoccols

        self.setupUi()

        self.tree_model = None
        self.load_protocol_layer_tree()

        self.layers_model = QtGui.QStandardItemModel()
        self.layer_list.setModel(self.layers_model)


    def add_selected_layers(self, item: QtGui.QStandardItem) -> None:

        if item is None:
            item = self.tree_model.invisibleRootItem()

        if item.hasChildren():
            for i in range(item.rowCount()):
                self.add_selected_layers(item.child(i))
        else:
            tree_layer = item.data(QtCore.Qt.UserRole)
            tree_name = item.text()
            # check if in list already
            for i in range(self.layers_model.rowCount()):
                list_layer = self.layers_model.item(i).data(QtCore.Qt.UserRole)

                if tree_layer == list_layer:
                    return
            # If got to here then the layer selected in the tree is not in use
            layer_item = QtGui.QStandardItem(tree_name)
            layer_item.setData(tree_layer, QtCore.Qt.UserRole)
            layer_item.setEditable(False)
            self.layers_model.appendRow(layer_item)


    def load_protocol_layer_tree(self):

        layer_names = [layer.label for protocol in self.protocols for layer in protocol.layers]
        duplicate_layers = [item for item in set(layer_names) if layer_names.count(item) > 1]

        # Rebuild the tree
        self.tree_model = QtGui.QStandardItemModel(self)
        for protocol in self.protocols:
            protocol_si = QtGui.QStandardItem(protocol.label)
            if self.event_type_id == DATA_CAPTURE_EVENT_TYPE_ID:
                if protocol.machine_code.lower() in [PLANNING_MACHINE_CODE.lower(), AS_BUILT_MACHINE_CODE.lower(), DESIGN_MACHINE_CODE.lower()]:
                    continue
            if self.event_type_id == PLANNING_EVENT_TYPE_ID:
                if protocol.machine_code.lower() != PLANNING_MACHINE_CODE.lower():
                    continue
            if self.event_type_id == AS_BUILT_EVENT_TYPE_ID:
                if protocol.machine_code.lower() != AS_BUILT_MACHINE_CODE.lower():
                    continue
            if self.event_type_id == DESIGN_EVENT_TYPE_ID:
                if protocol.machine_code.lower() != DESIGN_MACHINE_CODE.lower():
                    continue

            protocol_si.setData(protocol, QtCore.Qt.UserRole)
            protocol_si.setEditable(False)

            for layer in protocol.layers:
                # TODO temporarlily Turn off Brat layers
                if layer.label in ["BRAT CIS", "BRAT CIS Reaches"]:
                    continue

                layer_name = layer.label if layer.label not in duplicate_layers else f'{layer.label} ({layer.geom_type})'
                layer_si = QtGui.QStandardItem(layer_name)
                layer_si.setEditable(False)
                layer_si.setData(layer, QtCore.Qt.UserRole)
                protocol_si.appendRow(layer_si)

            if protocol_si.hasChildren():
                self.tree_model.appendRow(protocol_si)

        self.layer_tree.setModel(self.tree_model)
        self.layer_tree.expandAll()

        self.layer_tree.doubleClicked.connect(self.on_double_click_tree)

    def on_double_click_tree(self, index):

        item = self.layer_tree.model().itemFromIndex(index)
        layer = item.data(QtCore.Qt.UserRole)
        if isinstance(layer, Layer):
            self.add_selected_layers(item)

    def on_add_layer_clicked(self):

        for index in self.layer_tree.selectedIndexes():
            modelItem = self.tree_model.itemFromIndex(index)
            self.add_selected_layers(modelItem)

    def on_add_from_dce_clicked(self):

        frm = FrmEventPicker(self, self.qris_project, self.event_type_id)
        frm.exec_()
        if frm.result() == QtWidgets.QDialog.Accepted:
            for layer in frm.layers:
                layer_item = QtGui.QStandardItem(layer.name)
                layer_item.setData(layer, QtCore.Qt.UserRole)
                self.add_selected_layers(layer_item)

    def on_remove_layer(self):
        for index in self.layer_list.selectedIndexes():
            if self.mandatory_layers is not None:
                layer = self.layers_model.itemFromIndex(index).data(QtCore.Qt.UserRole)
                if layer.fc_name in self.mandatory_layers:
                    continue
            self.layers_model.removeRow(index.row())

    def setupUi(self):
        
        self.horiz_layers = QtWidgets.QHBoxLayout(self)
        self.setLayout(self.horiz_layers)

        # layer tree
        self.vert_layer_tree = QtWidgets.QVBoxLayout(self)
        self.horiz_layers.addLayout(self.vert_layer_tree)
        self.lblAllLayers = QtWidgets.QLabel('Available Layers')
        self.vert_layer_tree.addWidget(self.lblAllLayers)

        self.layer_tree = QtWidgets.QTreeView(self)
        self.layer_tree.setHeaderHidden(True)
        # self.layer_tree.clicked.connect(self.on_check_children)
        self.vert_layer_tree.addWidget(self.layer_tree)

        # Add Remove Buttons
        self.vert_buttons = QtWidgets.QVBoxLayout(self)
        self.horiz_layers.addLayout(self.vert_buttons)
        self.vert_add = QtWidgets.QVBoxLayout(self)
        self.vert_buttons.addLayout(self.vert_add)
        self.cmdAddLayer = QtWidgets.QPushButton('Add >>', self)
        self.cmdAddLayer.clicked.connect(self.on_add_layer_clicked)
        self.vert_add.addWidget(self.cmdAddLayer)
        self.cmdAddFromDCE = QtWidgets.QPushButton('Add From DCE >>', self)
        self.cmdAddFromDCE.clicked.connect(self.on_add_from_dce_clicked)
        self.vert_add.addWidget(self.cmdAddFromDCE)
        self.vert_remove = QtWidgets.QVBoxLayout(self)
        self.vert_buttons.addLayout(self.vert_remove)
        self.cmdRemoveLayer = QtWidgets.QPushButton('<< Remove', self)
        self.cmdRemoveLayer.clicked.connect(self.on_remove_layer)
        self.vert_remove.addWidget(self.cmdRemoveLayer)
        self.cmdRemoveAllLayers = QtWidgets.QPushButton('<< Remove All', self)
        self.cmdRemoveAllLayers.clicked.connect(lambda: self.layers_model.removeRows(0, self.layers_model.rowCount()))
        self.vert_remove.addWidget(self.cmdRemoveAllLayers)

        # Layers list
        self.vert_layers = QtWidgets.QVBoxLayout(self)
        self.horiz_layers.addLayout(self.vert_layers)

        self.lblLayersInUse = QtWidgets.QLabel('Layers In Use')
        self.vert_layers.addWidget(self.lblLayersInUse)

        self.layer_list = QtWidgets.QListView(self)
        self.vert_layers.addWidget(self.layer_list)




