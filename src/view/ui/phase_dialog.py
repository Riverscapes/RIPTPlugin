# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/experimental/phase_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_design_dialog(object):
    def setupUi(self, design_dialog):
        design_dialog.setObjectName("design_dialog")
        design_dialog.resize(474, 387)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("/Users/philip/code/riverscapes/QRiS/src/view/ui/experimental/../../icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        design_dialog.setWindowIcon(icon)
        self.formLayout = QtWidgets.QFormLayout(design_dialog)
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(design_dialog)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.lineEdit_phase_name = QtWidgets.QLineEdit(design_dialog)
        self.lineEdit_phase_name.setObjectName("lineEdit_phase_name")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.lineEdit_phase_name)
        self.label_4 = QtWidgets.QLabel(design_dialog)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_4)
        self.comboBox_primary_action = QtWidgets.QComboBox(design_dialog)
        self.comboBox_primary_action.setObjectName("comboBox_primary_action")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.comboBox_primary_action)
        self.label_6 = QtWidgets.QLabel(design_dialog)
        self.label_6.setObjectName("label_6")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_6)
        self.dateEdit_implementation_date = QtWidgets.QDateEdit(design_dialog)
        self.dateEdit_implementation_date.setCalendarPopup(True)
        self.dateEdit_implementation_date.setDate(QtCore.QDate(2021, 12, 21))
        self.dateEdit_implementation_date.setObjectName("dateEdit_implementation_date")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.dateEdit_implementation_date)
        self.plainTextEdit_phase_description = QtWidgets.QPlainTextEdit(design_dialog)
        self.plainTextEdit_phase_description.setObjectName("plainTextEdit_phase_description")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.plainTextEdit_phase_description)
        self.label_5 = QtWidgets.QLabel(design_dialog)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_5)
        self.buttonBox = QtWidgets.QDialogButtonBox(design_dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.buttonBox)

        self.retranslateUi(design_dialog)
        QtCore.QMetaObject.connectSlotsByName(design_dialog)

    def retranslateUi(self, design_dialog):
        _translate = QtCore.QCoreApplication.translate
        design_dialog.setWindowTitle(_translate("design_dialog", "Implementation Phase"))
        self.label.setText(_translate("design_dialog", "Phase Name"))
        self.label_4.setText(_translate("design_dialog", "Dominate Action"))
        self.label_6.setText(_translate("design_dialog", "Implementation Date"))
        self.dateEdit_implementation_date.setDisplayFormat(_translate("design_dialog", "MM/dd/yyyy"))
        self.label_5.setText(_translate("design_dialog", "Phase Description"))
