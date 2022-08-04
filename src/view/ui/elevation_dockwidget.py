# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/experimental/elevation_dockwidget.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_elevationDockWidget(object):
    def setupUi(self, elevationDockWidget):
        elevationDockWidget.setObjectName("elevationDockWidget")
        elevationDockWidget.resize(459, 234)
        self.dockWidgetContents = QtWidgets.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.formLayout = QtWidgets.QFormLayout(self.dockWidgetContents)
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(self.dockWidgetContents)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.txtRasterName = QtWidgets.QLineEdit(self.dockWidgetContents)
        self.txtRasterName.setReadOnly(True)
        self.txtRasterName.setObjectName("txtRasterName")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.txtRasterName)
        self.label_2 = QtWidgets.QLabel(self.dockWidgetContents)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.numElevation = QtWidgets.QDoubleSpinBox(self.dockWidgetContents)
        self.numElevation.setFrame(True)
        self.numElevation.setDecimals(1)
        self.numElevation.setMaximum(100.0)
        self.numElevation.setSingleStep(0.1)
        self.numElevation.setProperty("value", 1.0)
        self.numElevation.setObjectName("numElevation")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.numElevation)
        self.elevationSlider = QtWidgets.QSlider(self.dockWidgetContents)
        self.elevationSlider.setMaximum(1000)
        self.elevationSlider.setProperty("value", 10)
        self.elevationSlider.setOrientation(QtCore.Qt.Horizontal)
        self.elevationSlider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.elevationSlider.setTickInterval(100)
        self.elevationSlider.setObjectName("elevationSlider")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.SpanningRole, self.elevationSlider)
        self.btnExport = QtWidgets.QPushButton(self.dockWidgetContents)
        self.btnExport.setObjectName("btnExport")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.btnExport)
        elevationDockWidget.setWidget(self.dockWidgetContents)

        self.retranslateUi(elevationDockWidget)
        QtCore.QMetaObject.connectSlotsByName(elevationDockWidget)

    def retranslateUi(self, elevationDockWidget):
        _translate = QtCore.QCoreApplication.translate
        elevationDockWidget.setWindowTitle(_translate("elevationDockWidget", "QRiS Elevation Slider"))
        self.label.setText(_translate("elevationDockWidget", "Detrended Raster"))
        self.label_2.setText(_translate("elevationDockWidget", "Elevation above drainage"))
        self.numElevation.setSuffix(_translate("elevationDockWidget", " m"))
        self.btnExport.setText(_translate("elevationDockWidget", "Export Elevation Polygon"))
