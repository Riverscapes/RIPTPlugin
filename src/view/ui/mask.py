# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/mask.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Mask(object):
    def setupUi(self, Mask):
        Mask.setObjectName("Mask")
        Mask.resize(500, 400)
        self.gridLayout_2 = QtWidgets.QGridLayout(Mask)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(Mask)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.chkAddToMap = QtWidgets.QCheckBox(Mask)
        self.chkAddToMap.setObjectName("chkAddToMap")
        self.gridLayout.addWidget(self.chkAddToMap, 3, 1, 1, 1)
        self.txtDescription = QtWidgets.QTextEdit(Mask)
        self.txtDescription.setObjectName("txtDescription")
        self.gridLayout.addWidget(self.txtDescription, 2, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(Mask)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)
        self.cboType = QtWidgets.QComboBox(Mask)
        self.cboType.setObjectName("cboType")
        self.gridLayout.addWidget(self.cboType, 1, 1, 1, 1)
        self.txtName = QtWidgets.QLineEdit(Mask)
        self.txtName.setMaxLength(255)
        self.txtName.setObjectName("txtName")
        self.gridLayout.addWidget(self.txtName, 0, 1, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(Mask)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 4, 1, 1, 1)
        self.label_3 = QtWidgets.QLabel(Mask)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(Mask)
        QtCore.QMetaObject.connectSlotsByName(Mask)
        Mask.setTabOrder(self.txtName, self.cboType)
        Mask.setTabOrder(self.cboType, self.txtDescription)

    def retranslateUi(self, Mask):
        _translate = QtCore.QCoreApplication.translate
        Mask.setWindowTitle(_translate("Mask", "Dialog"))
        self.label.setText(_translate("Mask", "Name"))
        self.chkAddToMap.setText(_translate("Mask", "Add to Map"))
        self.label_2.setText(_translate("Mask", "Description"))
        self.label_3.setText(_translate("Mask", "Type"))
