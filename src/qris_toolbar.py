# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QRiS
                                 A QGIS plugin
 QGIS Riverscapes Studio (QRiS)
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-05-06
        git sha              : $Format:%H$
        copyright            : (C) 2021 by North Arrow Research
        email                : info@northarrowresearch.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os.path
import requests
from PyQt5.QtCore import pyqtSlot
from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.PyQt.QtCore import QSettings
from qgis.core import QgsApplication, QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsProject, Qgis, QgsRasterLayer, QgsMessageLog, QgsRectangle
from qgis.gui import QgsMapToolEmitPoint

# TODO fix this
from .gp.provider import Provider
from .QRiS.settings import Settings
from .QRiS.settings import CONSTANTS

# Initialize Qt resources from file resources.py
from . import resources

# Import the code for the DockWidget
from .view.frm_dockwidget import QRiSDockWidget
from .view.frm_new_project import FrmNewProject
from .view.frm_about import FrmAboutDialog

from .model.project import apply_db_migrations
from .QRiS.qrave_integration import QRaveIntegration
from .QRiS.path_utilities import safe_make_abspath, safe_make_relpath, parse_posix_path

from .gp.watershed_attributes import WatershedAttributes

ORGANIZATION = 'Riverscapes'
APPNAME = 'QRiS'
LAST_PROJECT_FOLDER = 'last_project_folder'
RECENT_PROJECT_LIST = 'recent_projects'


class QRiSToolbar:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.qrave = None

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        self.qproject = QgsProject.instance()

        # initialize locale
        locale = QtCore.QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', 'qris_{}.qm'.format(locale))
        if os.path.exists(locale_path):
            self.translator = QtCore.QTranslator()
            self.translator.load(locale_path)
            QtCore.QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menus = []
        self.menu = self.tr(u'&QGIS Riverscapes Studio (QRiS)')
        self.toolbar = self.iface.addToolBar(u'QRiS')
        self.toolbar.setObjectName(u'QRiS')

        self.settings = Settings(iface=self.iface)

        # Populated on load from a URL
        self.acknowledgements = None

        self.pluginIsActive = False
        self.dockwidget = None

    # noinspection PyMethodMayBeStatic

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QtCore.QCoreApplication.translate('QRiS', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QtGui.QIcon(icon_path)
        action = QtWidgets.QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    # TODO Remove this I don't think it is needed
    # def initProcessing(self):
        # self.provider = Provider()
        # QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        # DEBUG: REMOVE ME
        # from ..test.rsxml_test import rsxml_test
        # rsxml_test()

        # Initialize the processing framework
        # self.initProcessing()

        # Listen for the signal when a project is being loaded
        # so we can try and reload the relevant QRiS project
        self.qproject.readProject.connect(self.onProjectLoad)

        # Trigger the check for relative paths on whether the homePath has changed
        self.qproject.homePathChanged.connect(self.project_homePathChanged)
        # Close project when the project is cleared
        self.qproject.cleared.connect(self.close_project)

        icon_path = ':/plugins/qris_toolbar/qris_icon'
        self.add_action(icon_path, text='QRiS', callback=self.run, parent=self.iface.mainWindow(), add_to_menu=False)

        # --- PROJECT MENU ---
        project_menu = self.add_toolbar_menu('Project')
        self.add_menu_action(project_menu, 'new', 'New QRiS Project', self.create_new_project_dialog, True, 'Create a New QRiS Project')
        self.add_menu_action(project_menu, 'folder', 'Open QRiS Project', self.open_existing_project, True, 'Open Existing QRiS Project')
        self.mru_menu = project_menu.addMenu(QtGui.QIcon(f':/plugins/qris_toolbar/folder'), 'Recent QRiS Projects')
        self.add_menu_action(project_menu, 'collapse', 'Close Project', self.close_project, True, 'Close the Current QRiS Project')
        self.load_mru_projects()

        # --- HELP MENU --
        help_menu = self.add_toolbar_menu('Help')
        self.add_menu_action(help_menu, 'help', 'QRiS Online Help', lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl('https://qris.riverscapes.net')), True, 'Launch QRiS Online Help in default browser')
        self.add_menu_action(help_menu, 'qris_icon', 'About QRiS', self.about_load, True, 'Show Information About QRiS')

        canvas = self.iface.mapCanvas()
        self.watershed_html_tool = QgsMapToolEmitPoint(canvas)
        self.watershed_html_tool.canvasClicked.connect(self.html_watershed_metrics)

        self.watershed_json_tool = QgsMapToolEmitPoint(canvas)
        self.watershed_json_tool.canvasClicked.connect(self.json_watershed_metrics)

    def add_toolbar_menu(self, label: str) -> QtWidgets.QMenu:

        tool_button = QtWidgets.QToolButton(self.toolbar)
        tool_button.setText(label)
        tool_button.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        tool_button.setMenu(QtWidgets.QMenu())
        tool_button.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
        self.toolbar.addWidget(tool_button)
        self.menus.append(tool_button)
        return tool_button.menu()

    def add_menu_action(self, menu: QtWidgets.QMenu, icon_name: str, label: str, callback, enabled: bool, status_tip: str):

        action = QtWidgets.QAction(QtGui.QIcon(f':/plugins/qris_toolbar/{icon_name}'), label, self.iface.mainWindow())
        action.triggered.connect(callback)
        action.setEnabled(enabled)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        menu.addAction(action)
        self.actions.append(action)

    def close_project(self):
        if self.dockwidget is not None:
            # self.dockwidget.destroy_docwidget()
            self.dockwidget.close()
            self.iface.removeDockWidget(self.dockwidget)
            # self.dockwidget = None

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed.
        This occurs when the user clicks the X button on the top right of
        the dockable widget."""

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)
        self.close_project()

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        # Cleanup the main dockable window
        if self.dockwidget is not None:
            self.dockwidget.destroy_docwidget()
            self.dockwidget.close()

        # Need to de-initialize the processing framework
        # QgsApplication.processingRegistry().removeProvider(self.provider)

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&QGIS Riverscapes Studio (QRiS)'),
                action)
            self.iface.removeToolBarIcon(action)

        self.dockwidget = None

        # remove the toolbar
        del self.toolbar
        del self.dockwidget

    # --------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        self.prepare_widget()

        # Only attempt to load the last used project for developers when the special text file is present.
        load_last_project_key = os.path.join(os.path.dirname(__file__), '..', 'load_last_project.txt')
        if os.path.isfile(load_last_project_key):
            settings = QtCore.QSettings(ORGANIZATION, APPNAME)
            last_project_folder = settings.value(LAST_PROJECT_FOLDER)
            if last_project_folder is not None and os.path.isdir(last_project_folder):
                project_file = os.path.join(last_project_folder, f'{os.path.basename(last_project_folder)}.gpkg')
                if os.path.isfile(project_file):
                    self.open_qris_project(project_file)

    def prepare_widget(self):
        if not self.pluginIsActive:
            self.pluginIsActive = True

        if self.dockwidget is not None:
            self.close_project()

        # Load a version of the QRave code we can use for cross-plugin integration
        # if self.qrave is None:
        self.qrave = QRaveIntegration(self.toolbar)
        if self.qrave.name is not None:
            self.settings.setValue('symbologyDir', self.qrave.symbology_folder)
        else:
            QgsMessageLog.logMessage('Unable to load Required QRave plugin. Some functions in QRiS may be disabled, including layer symbology.', 'QRiS', Qgis.Critical)
            self.iface.messageBar().pushMessage('QRiS Plugin Load Error', f'Unable to load QRave plugin.', level=Qgis.Critical, duration=5)
            self.iface.mainWindow().repaint()

        # Create the dockwidget (after translation) and keep reference
        self.dockwidget = QRiSDockWidget(self.iface)
        if self.qrave.name is not None:
            self.dockwidget.qrave = self.qrave

        # connect to provide cleanup on closing of dockwidget
        self.dockwidget.closingPlugin.connect(self.onClosePlugin)

        # show the dockwidget
        self.iface.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dockwidget)
        self.dockwidget.show()

    def toggle_widget(self, forceOn=False):

        self.prepare_widget()
        if self.dockwidget.isHidden() and forceOn is True:
            self.dockwidget.show()

    def onProjectLoad(self):
        """Slot for QGIS signal when a QGIS project (QGZ) is being loaded.
        Check if the QGIS project references a QRiS project. Load it if does."""

        qris_project_path = self.get_project_path_settings()
        if qris_project_path is not None and len(qris_project_path) > 0 and os.path.exists(qris_project_path):
            self.open_qris_project(qris_project_path)

    def project_homePathChanged(self):
        """Trigger an event before saving the project so we have an opportunity to corrent the paths
        """
        proj_path = self.get_project_path_settings()
        self.set_project_path_settings(proj_path)

    def set_project_path_settings(self, project_file: str):
        """Write the QRiS project filepath to the QgsProject file
        If the destination is a .qgz file then relative paths are used

        Args:
            project_file (str): _description_
        """
        qgs_path = self.qproject.absoluteFilePath()
        if os.path.isdir(os.path.dirname(qgs_path)):
            qgs_path_dir = os.path.dirname(qgs_path)
            # Swap all abspaths for relative ones
            project_file = safe_make_relpath(project_file, qgs_path_dir)

        self.qproject.writeEntry(CONSTANTS['settingsCategory'], CONSTANTS['qris_project_path'], project_file)

    def get_project_path_settings(self):
        """Fetch the QRiS project filepath from the QgsProject settings
        If it comes in as a relative path it is transformed and returned as an absolute path

        Returns:
            _type_: _description_
        """
        project_file = None
        try:
            project_file, type_conversion_ok = self.qproject.readEntry(
                CONSTANTS['settingsCategory'],
                CONSTANTS['qris_project_path']
            )

            if type_conversion_ok is False:
                project_file = None

        except Exception as e:
            self.settings.log('Error loading project settings: {}'.format(e), Qgis.Warning)

        qgs_project_path = self.qproject.absoluteFilePath()
        if os.path.isfile(qgs_project_path):
            qgs_path_dir = os.path.dirname(qgs_project_path)
            # Change all relative paths back to absolute ones
            project_file = safe_make_abspath(project_file, qgs_path_dir)

        return project_file

    def open_existing_project(self):
        """
        Browse for a project directory
        :return:
        """

        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        last_project_folder = settings.value(LAST_PROJECT_FOLDER)

        dialog_return = QtWidgets.QFileDialog.getOpenFileName(self.dockwidget, "Open Existing QRiS Project", last_project_folder, self.tr("QRiS Project Files (*.gpkg)"))
        if dialog_return is not None and dialog_return[0] != '' and os.path.isfile(dialog_return[0]):
            self.open_qris_project(dialog_return[0])

    def open_qris_project(self, db_path: str):

        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        settings.setValue(LAST_PROJECT_FOLDER, os.path.dirname(db_path))
        settings.sync()

        # Apply database migrations to ensure latest schema
        db_path = parse_posix_path(db_path)
        self.update_database(db_path)

        self.toggle_widget(forceOn=True)
        self.set_project_path_settings(db_path)
        self.dockwidget.build_tree_view(db_path)
        self.qrave.qrave_to_qris.connect(self.dockwidget.qris_from_qrave)
        self.add_project_to_mru_list(db_path)

        # Set the map canvas to the project SRS
        default_crs = QSettings().value('Projections/layerDefaultCrs')
        default_crs_behavior = QSettings().value('app/projections/newProjectCrsBehavior')
        project_srs = self.dockwidget.project.metadata.get('project_srs', None)
        trigger_repaint = False
        try:
            if project_srs is not None:
                QSettings().setValue('Projections/layerDefaultCrs', project_srs)
                QSettings().setValue('app/projections/newProjectCrsBehavior', 'usePresetCrs')
                # get map crs from project_srs id
                crs = QgsCoordinateReferenceSystem(project_srs)
                if crs is not None:
                    self.iface.mapCanvas().setDestinationCrs(crs)
                    self.qproject.setCrs(crs)
                    self.iface.mapCanvas().refresh()
                    self.iface.messageBar().pushMessage('QRiS', f'Map CRS set to {crs.description()}')
                    trigger_repaint = True

            # Add basemap to ToC if empty
            if len(QgsProject.instance().mapLayers().values()) == 0:
                self.dockwidget.setup_blank_map(trigger_repaint=trigger_repaint)
        finally:
            # restore default crs
            QSettings().setValue('Projections/layerDefaultCrs', default_crs)
            QSettings().setValue('app/projections/newProjectCrsBehavior', default_crs_behavior)

        # We set the project path in the project settings. This way it will be saved with the QgsProject file
        # if self.dockwidget is None or self.dockwidget.isHidden() is True:
        #     # self.toggle_widget(forceOn=True)
        #     project = QRiSProject()
        #     project.load_project_file(dialog_return[0])
        #     self.open_project(project)

    def load_mru_projects(self):

        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        mrus = settings.value(RECENT_PROJECT_LIST, [])
        self.mru_menu.clear()
        self.mru_actions = []
        for mru in mrus:
            if os.path.exists(mru):
                self.add_menu_action(self.mru_menu, 'riverscapes_icon', mru, (lambda mru: lambda: self.open_qris_project(mru))(mru), True, '')

    def add_project_to_mru_list(self, db_path):

        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        mrus = settings.value(RECENT_PROJECT_LIST, [])
        if db_path in mrus:
            mrus.remove(db_path)
        if os.path.exists(db_path):
            mrus.insert(0, db_path)
        settings.setValue(RECENT_PROJECT_LIST, mrus[:10])
        self.load_mru_projects()

    def create_new_project_dialog(self):

        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        last_parent_folder = os.path.dirname(settings.value(LAST_PROJECT_FOLDER)) if settings.value(LAST_PROJECT_FOLDER) is not None else None

        dialog_return = QtWidgets.QFileDialog.getExistingDirectory(self.dockwidget, 'Select QRiS Project Parent Folder', last_parent_folder)
        if len(dialog_return) > 0:
            self.save_folder = dialog_return
            self.frm_new_project = FrmNewProject(dialog_return, self.iface.mainWindow())
            self.frm_new_project.newProjectComplete.connect(self.on_new_project_complete)
            result = self.frm_new_project.exec_()

    def on_new_project_complete(self, project_dir: str, db_path: str):

        self.open_qris_project(db_path)

    def activate_html_watershed_attributes(self):

        canvas = self.iface.mapCanvas()
        canvas.setMapTool(self.watershed_html_tool)

    def activate_json_watershed_attributes(self):

        canvas = self.iface.mapCanvas()
        canvas.setMapTool(self.watershed_json_tool)

    def json_watershed_metrics(self, point, button):
        """
        Display the watershed attribute results based on the point that the user clicked on the map
        """

        try:
            # The point is in the map data frame display units. Transform to WGS84
            transformed_point = self.transform_geometry(point, 4326)
            long_task = WatershedAttributes(transformed_point.y(), transformed_point.x(), False)
            long_task.process_complete.connect(self.on_watershed_attributes_complete)

            # Call the run command directly during development to run the process synchronousely.
            # DO NOT DEPLOY WITH run() UNCOMMENTED
            # long_task.run()

            # Call the addTask() method to run the process asynchronously. Deploy with this method uncommented.
            QgsApplication.taskManager().addTask(long_task)

        except Exception as ex:
            QtWidgets.QMessageBox.warning(None, 'Error Retrieving Watershed Metrics', str(ex))

    def html_watershed_metrics(self, point, button):
        """
        Display the watershed attribute results based on the point that the user clicked on the map
        """

        try:
            # The point is in the map data frame display units. Transform to WGS84
            transformed_point = self.transform_geometry(point, 4326)
            long_task = WatershedAttributes(transformed_point.y(), transformed_point.x(), True)
            long_task.process_complete.connect(self.on_watershed_attributes_complete)

            # Call the run command directly during development to run the process synchronousely.
            # DO NOT DEPLOY WITH run() UNCOMMENTED
            # long_task.run()

            # Call the addTask() method to run the process asynchronously. Deploy with this method uncommented.
            QgsApplication.taskManager().addTask(long_task)

        except Exception as ex:
            QtWidgets.QMessageBox.warning(None, 'Error Retrieving Watershed Metrics', str(ex))

    @pyqtSlot(str, bool)
    def on_watershed_attributes_complete(self, output_path: str, result: bool) -> None:

        if result:
            self.iface.messageBar().pushMessage(f'Watershed Attributes Complete.', f'Outputs at {output_path}', level=Qgis.Info, duration=5)
        else:
            self.iface.messageBar().pushMessage(f'Watershed Attributes Error.', 'Check the QGIS log for details.', level=Qgis.Critical, duration=5)

    def update_database(self, db_path):
        try:
            apply_db_migrations(db_path)
        except Exception as ex:
            QtWidgets.QMessageBox.warning(None, 'QRiS Database Migration Error', 'Error Appling QRiS Database Migrations check the QGIS log for details.')
            QgsMessageLog.logMessage(f'Error Appling QRiS Database Migrations: {str(ex)}', 'QRiS', Qgis.Critical)

    def configure_watershed_attribute_menu(self):

        self.wat_button = QtWidgets.QToolButton()
        self.wat_button.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.wat_button.setIcon(QtGui.QIcon(':/plugins/qris_toolbar/watershed'))
        self.wat_button.setMenu(QtWidgets.QMenu())
        self.wat_button.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
        self.toolbar.addWidget(self.wat_button)
        self.wat_menu = self.wat_button.menu()

        self.wat_button = QtWidgets.QToolButton()
        self.wat_button.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self.wat_button.setMenu(self.wat_menu)
        self.wat_button.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)

        self.wat_html_action = QtWidgets.QAction(QtGui.QIcon(':/plugins/qris_toolbar/watershed'), self.tr('Export Attributes to HTML Report'), self.iface.mainWindow())
        self.wat_html_action.triggered.connect(self.activate_html_watershed_attributes)
        self.wat_menu.addAction(self.wat_html_action)

        self.wat_json_action = QtWidgets.QAction(QtGui.QIcon(':/plugins/qris_toolbar/json'), self.tr('Export Attributes to JSON'), self.iface.mainWindow())
        self.wat_json_action.triggered.connect(self.activate_json_watershed_attributes)
        self.wat_menu.addAction(self.wat_json_action)

        self.wat_button.setDefaultAction(self.wat_html_action)

    def about_load(self):

        self.frm_about = FrmAboutDialog(self.iface.mainWindow())
        self.frm_about.exec_()
        self.frm_about = None

    def transform_geometry(self, geometry, map_epsg: int, output_epsg: int):

        source_crs = QgsCoordinateReferenceSystem(map_epsg)
        dest_crs = QgsCoordinateReferenceSystem(output_epsg)
        transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance().transformContext())
        return transform.transform(geometry)
