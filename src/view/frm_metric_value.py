from re import T
from PyQt5 import QtCore, QtGui, QtWidgets
from ..model.project import Project
from ..model.metric_value import MetricValue
from ..model.metric import Metric
from .utilities import add_standard_form_buttons


class FrmMetricValue(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, metrics, metric_value: MetricValue):
        super().__init__(parent)
        self.setupUi()

        self.setWindowTitle('Analysis Metric Value')

        self.metric_value = metric_value
        self.project = project
        self.metrics = metrics

        self.txtMetric.setText(metric_value.metric.name)

        if metric_value.manual_value is not None:
            self.valManual.setValue(metric_value.manual_value)

        self.rdoManual.setChecked(metric_value.is_manual)
        self.valManual.setEnabled(self.rdoManual.isChecked())

        if metric_value.automated_value is not None:
            self.txtAutomated.setText(metric_value.automated_value)
        self.rdoAutomated.setEnabled(metric_value.automated_value is not None)

        self.rdoAutomated.setChecked(not metric_value.is_manual)

        self.txtDescription.setPlainText(metric_value.description)

    def rdoManual_checkchanged(self):
        self.valManual.setEnabled(self.rdoManual.isChecked())

    def accept(self):

        self.metric_value.manual_value = self.valManual.value
        self.metric_value.automated_value = float(self.txtAutomated.text())
        self.metric_value.is_manual = self.rdoManual.isChecked()
        self.metric_value.description = self.txtDescription.toPlainText()
        try:
            self.metric_value.save(self.project.project_file, self.analysis, self.event, self.mask_feature_id)
        except Exception as ex:
            QtWidgets.QMessageBox.warning('Error Saving Metric Value', str(ex))
            return

        super().accept()

    def cmd_previous_metric_clicked(self):

        print('TODO')

    def cmd_next_metric_clicked(self):
        print('TODO')

    def setupUi(self):

        self.resize(400, 200)

        self.vert = QtWidgets.QVBoxLayout()
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblMetric = QtWidgets.QLabel()
        self.lblMetric.setText('Metric')
        self.grid.addWidget(self.lblMetric, 0, 0, 1, 1)

        self.txtMetric = QtWidgets.QLineEdit()
        self.txtMetric.setReadOnly(True)
        self.grid.addWidget(self.txtMetric, 0, 1, 1, 1)

        self.horizMetric = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horizMetric, 0, 2, 1, 1)

        self.cmdPrevious = QtWidgets.QPushButton()
        # self.cmdPrevious.setText('Previous Metric')
        self.cmdPrevious.setIcon(QtGui.QIcon(f':plugins/qris_toolbar/arrow_up'))
        self.cmdPrevious.clicked.connect(self.cmd_previous_metric_clicked)
        self.cmdPrevious.setToolTip('Previous Metric')
        self.horizMetric.addWidget(self.cmdPrevious)

        self.cmdNext = QtWidgets.QPushButton()
        # self.cmdNext.setText('Next Metric')
        self.cmdNext.setIcon(QtGui.QIcon(f':plugins/qris_toolbar/arrow_down'))
        self.cmdNext.setToolTip('Next Metric')
        self.cmdNext.clicked.connect(self.cmd_next_metric_clicked)
        self.horizMetric.addWidget(self.cmdNext)

        self.rdoManual = QtWidgets.QRadioButton()
        self.rdoManual.setChecked(True)
        self.rdoManual.setText('Manual Value')
        self.rdoManual.toggled.connect(self.rdoManual_checkchanged)
        self.grid.addWidget(self.rdoManual, 1, 0, 1, 1)

        self.valManual = QtWidgets.QDoubleSpinBox()
        self.grid.addWidget(self.valManual, 1, 1, 1, 1)

        self.rdoAutomated = QtWidgets.QRadioButton()
        self.rdoAutomated.setText('Automated Value')
        self.grid.addWidget(self.rdoAutomated, 2, 0, 1, 1)

        self.txtAutomated = QtWidgets.QLineEdit()
        self.txtAutomated.setReadOnly(True)
        self.grid.addWidget(self.txtAutomated, 2, 1, 1, 1)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)

        self.cmdCalculate = QtWidgets.QPushButton()
        # self.cmdCalculate.setText('Calculate')
        self.cmdCalculate.setIcon(QtGui.QIcon(f':plugins/qris_toolbar/gis'))
        self.cmdCalculate.setToolTip('Calculate Metric From GIS')
        self.cmdCalculate.setSizePolicy(sizePolicy)
        self.grid.addWidget(self.cmdCalculate, 2, 2, 1, 1)

        self.lblUncertainty = QtWidgets.QLabel()
        self.lblUncertainty.setText('Uncertainty')
        self.grid.addWidget(self.lblUncertainty, 3, 0, 1, 1)

        self.valUncertainty = QtWidgets.QDoubleSpinBox()
        self.grid.addWidget(self.valUncertainty, 3, 1, 1, 1)

        self.tab = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tab)

        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.tab.addTab(self.txtDescription, 'Description')

        self.metadata = QtWidgets.QTableWidget()
        self.tab.addTab(self.metadata, 'Metadata')

        self.vert.addLayout(add_standard_form_buttons(self, 'metric_Value'))
