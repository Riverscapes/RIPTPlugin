import os
import json
import shutil
import sqlite3

from osgeo import gdal

from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.core import QgsVectorLayer, QgsGeometry, QgsPolygon

from rsxml.project_xml import Project, MetaData, Meta, ProjectBounds, Coords, BoundingBox, Realization, Geopackage, GeopackageLayer, GeoPackageDatasetTypes, Dataset

from ...__version__ import __version__ as qris_version
from ..model.event import Event
from ..model.analysis import Analysis
from ..model.mask import Mask, AOI_MASK_TYPE_ID
from ..model.project import Project as QRiSProject
from ..model.scratch_vector import scratch_gpkg_path
from ..QRiS.path_utilities import parse_posix_path
from .metadata import MetadataWidget
from .utilities import add_standard_form_buttons


class FrmExportProject(QtWidgets.QDialog):

    def __init__(self, parent, project: QRiSProject, outpath: str = None):
        super().__init__(parent)

        self.qris_project = project

        self.setWindowTitle("Export QRiS to Riverscapes Project")
        self.setupUi()

        self.set_output_path(outpath)

        # populate the AOI combo box with aoi names
        for aoi_id, aoi in self.qris_project.masks.items():
            if aoi.mask_type.id == AOI_MASK_TYPE_ID:
                self.cbo_project_bounds_aoi.addItem(aoi.name, aoi_id)

        # Layer Model
        self.export_layers_model = QtGui.QStandardItemModel()
        self.export_layers_model.itemChanged.connect(self.handle_item_changed)

        # Inputs
        inputs_node = QtGui.QStandardItem("Inputs")
        inputs_node.setCheckable(True)
        inputs_node.setCheckState(QtCore.Qt.PartiallyChecked)

        # AOIs
        aois_node = QtGui.QStandardItem("AOIs")
        aois_node.setCheckable(True)
        aois_node.setCheckState(QtCore.Qt.Checked)
        for aoi in self.qris_project.masks.values():
            if aoi.mask_type.id == AOI_MASK_TYPE_ID:
                item = QtGui.QStandardItem(aoi.name)
                item.setCheckable(True)
                item.setCheckState(QtCore.Qt.Checked)
                item.setData(aoi, QtCore.Qt.UserRole)
                aois_node.appendRow(item)
        inputs_node.appendRow(aois_node)

        # Sample Frames
        sample_frames_node = QtGui.QStandardItem("Sample Frames")
        sample_frames_node.setCheckable(True)
        sample_frames_node.setCheckState(QtCore.Qt.Checked)
        for sample_frame in self.qris_project.masks.values():
            if sample_frame.mask_type.id != AOI_MASK_TYPE_ID:
                item = QtGui.QStandardItem(sample_frame.name)
                item.setCheckable(True)
                item.setCheckState(QtCore.Qt.Checked)
                item.setData(sample_frame, QtCore.Qt.UserRole)
                sample_frames_node.appendRow(item)
        inputs_node.appendRow(sample_frames_node)

        # Profiles
        profiles_node = QtGui.QStandardItem("Profiles")
        profiles_node.setCheckable(True)
        profiles_node.setCheckState(QtCore.Qt.Checked)
        for profile in self.qris_project.profiles.values():
            item = QtGui.QStandardItem(profile.name)
            item.setCheckable(True)
            item.setCheckState(QtCore.Qt.Checked)
            item.setData(profile, QtCore.Qt.UserRole)
            profiles_node.appendRow(item)
        inputs_node.appendRow(profiles_node)

        # Cross Sections
        xsections_node = QtGui.QStandardItem("Cross Sections")
        xsections_node.setCheckable(True)
        xsections_node.setCheckState(QtCore.Qt.Checked)
        for xsection in self.qris_project.cross_sections.values():
            item = QtGui.QStandardItem(xsection.name)
            item.setCheckable(True)
            item.setCheckState(QtCore.Qt.Checked)
            item.setData(xsection, QtCore.Qt.UserRole)
            xsections_node.appendRow(item)
        inputs_node.appendRow(xsections_node)

        # Surfaces
        surfaces_node = QtGui.QStandardItem("Surfaces")
        surfaces_node.setCheckable(True)
        for surface in self.qris_project.rasters.values():
            if surface.is_context:
                continue
            item = QtGui.QStandardItem(surface.name)
            item.setCheckable(True)
            item.setData(surface, QtCore.Qt.UserRole)
            surfaces_node.appendRow(item)        
        inputs_node.appendRow(surfaces_node)
        self.export_layers_model.appendRow(inputs_node)

        # Context
        context_node = QtGui.QStandardItem("Context")
        context_node.setCheckable(True)
        for context_vector in self.qris_project.scratch_vectors.values():
            item = QtGui.QStandardItem(context_vector.name)
            item.setCheckable(True)
            item.setCheckState(QtCore.Qt.Checked)
            item.setData(context_vector, QtCore.Qt.UserRole)
            context_node.appendRow(item)
        for context in self.qris_project.rasters.values():
            if not context.is_context:
                continue
            item = QtGui.QStandardItem(context.name)
            item.setCheckable(True)
            item.setData(context, QtCore.Qt.UserRole)
            context_node.appendRow(item)

        # DCE and Designs
        events_node = QtGui.QStandardItem("Data Capture Events and Designs")
        events_node.setCheckable(True)
        events_node.setCheckState(QtCore.Qt.Checked)
        for event in self.qris_project.events.values():
            item = QtGui.QStandardItem(event.name)
            item.setCheckable(True)
            item.setCheckState(QtCore.Qt.Checked)
            item.setData(event, QtCore.Qt.UserRole)
            events_node.appendRow(item)
        self.export_layers_model.appendRow(events_node)

        # Analysis
        analyses_node = QtGui.QStandardItem("Analyses")
        analyses_node.setCheckable(True)
        analyses_node.setCheckState(QtCore.Qt.Checked)
        for analysis in self.qris_project.analyses.values():
            item = QtGui.QStandardItem(analysis.name)
            item.setCheckable(True)
            item.setCheckState(QtCore.Qt.Checked)
            item.setData(analysis, QtCore.Qt.UserRole)
            analyses_node.appendRow(item)
        self.export_layers_model.appendRow(analyses_node)

        # Layer Tree
        self.export_tree.setModel(self.export_layers_model)
        self.export_tree.setUniformRowHeights(True)
        self.export_tree.setAnimated(True)
        self.export_tree.setIndentation(20)
        self.export_tree.setSortingEnabled(False)
        self.export_tree.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.export_tree.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.export_tree.expandAll()

    def handle_item_changed(self, item):
        if item.hasChildren():
            self.export_layers_model.itemChanged.disconnect(self.handle_item_changed)
            self.update_child_check_state(item)
            self.export_layers_model.itemChanged.connect(self.handle_item_changed)
        self.update_check_state(item.parent())

    def update_child_check_state(self, item):
        for i in range(item.rowCount()):
            child = item.child(i)
            if child is not None:
                child.setCheckState(item.checkState())
                if child.hasChildren():
                    self.update_child_check_state(child)

    def update_check_state(self, item):
        if item is not None and item.hasChildren():
            check_states = [item.child(i).checkState() for i in range(item.rowCount())]
            if all(state == QtCore.Qt.Checked for state in check_states):
                self.export_layers_model.itemChanged.disconnect(self.handle_item_changed)
                item.setCheckState(QtCore.Qt.Checked)
                self.export_layers_model.itemChanged.connect(self.handle_item_changed)
            elif all(state == QtCore.Qt.Unchecked for state in check_states):
                self.export_layers_model.itemChanged.disconnect(self.handle_item_changed)
                item.setCheckState(QtCore.Qt.Unchecked)
                self.export_layers_model.itemChanged.connect(self.handle_item_changed)
            else:
                self.export_layers_model.itemChanged.disconnect(self.handle_item_changed)
                item.setCheckState(QtCore.Qt.PartiallyChecked)
                self.export_layers_model.itemChanged.connect(self.handle_item_changed)
            self.update_check_state(item.parent())

    def set_output_path(self, outpath: str):

        # outpath = parse_posix_path(os.path.join(self.basepath, project_name.replace(" ", "_")))
        self.txt_outpath.setText(outpath)

    def accept(self) -> None:

        # check if output directory is empty. If so, prompt user to overwrite or cancel
        if os.path.exists(self.txt_outpath.text()):
            if len(os.listdir(self.txt_outpath.text())) > 0:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Warning)
                msg.setText("The selected output folder is not empty. Do you want to overwrite it?")
                msg.setWindowTitle("Overwrite Output Folder?")
                msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
                msg.setDefaultButton(QtWidgets.QMessageBox.Cancel)
                msg.setEscapeButton(QtWidgets.QMessageBox.Cancel)
                ret = msg.exec_()
                if ret == QtWidgets.QMessageBox.Cancel:
                    return

        if self.opt_project_bounds_aoi.isChecked():
            # if Select AOI is selected, then warn the user to select an AOI
            if self.cbo_project_bounds_aoi.currentIndex() == 0:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Warning)
                msg.setText("Please select an AOI or select 'Use all QRiS layers'")
                msg.setWindowTitle("Select AOI")
                msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msg.setDefaultButton(QtWidgets.QMessageBox.Ok)
                msg.setEscapeButton(QtWidgets.QMessageBox.Ok)
                msg.exec_()
                return

        # create a new project folder if it doesn't exist
        if not os.path.exists(self.txt_outpath.text()):
            os.mkdir(self.txt_outpath.text())

        # copy the geopackage layers to the new project folder
        out_geopackage = os.path.abspath(os.path.join(self.txt_outpath.text(), "qris.gpkg").replace("\\", "/"))
        shutil.copy(self.qris_project.project_file, out_geopackage)

        # ds_gpkg = gdal.VectorTranslate(out_geopackage,
        #                                self.qris_project.project_file,
        #                                format="GPKG")
        # del ds_gpkg

        # copy the context geopackage to the new project folder
        context_dir = os.path.abspath(os.path.join(self.txt_outpath.text(), 'context').replace("\\", "/"))
        context_geopackage = os.path.abspath(os.path.join(context_dir, "feature_classes.gpkg").replace("\\", "/"))
        if os.path.exists(scratch_gpkg_path(self.qris_project.project_file)):
            if not os.path.exists(context_dir):
                os.mkdir(context_dir)
            shutil.copy(scratch_gpkg_path(self.qris_project.project_file), context_geopackage)
        # ds = gdal.VectorTranslate(context_geopackage,
        #                           scratch_gpkg_path(self.qris_project.project_file),
        #                           format="GPKG")
        # del ds

        # Project Bounds
        if self.opt_project_bounds_all.isChecked():
            # get the extent of all layers
            envelope = None
            for layer in ['dce_points', 'dce_lines', 'dce_polygons']:  # self.qris_project.layers.values():
                # if layer.geom_type == "NoGeometry":
                # continue
                geom = None
                # lyr = QgsVectorLayer(f'{self.qris_project.project_file}|layername={layer.fc_name}', layer.name, "ogr")
                # lyr.setSubsetString(f"event_id = {layer.event_id}")
                lyr = QgsVectorLayer(f'{self.qris_project.project_file}|layername={layer}', layer, "ogr")
                for f in lyr.getFeatures():
                    if geom is None:
                        geom = f.geometry()
                    else:
                        geom = geom.combine(f.geometry())
                if geom is None:
                    continue
                hull = geom.convexHull()
                if envelope is None:
                    envelope = hull
                else:
                    envelope = envelope.combine(hull)
        else:
            # get the extent of the selected AOI
            aoi_id = self.cbo_project_bounds_aoi.currentData()
            aoi: Mask = self.qris_project.masks[aoi_id]
            lyr = QgsVectorLayer(f'{self.qris_project.project_file}|layername=aoi_features', aoi.name, "ogr")
            lyr.setSubsetString(f"mask_id = {aoi.id}")
            envelope = lyr.getFeatures().__next__().geometry()

        extent = envelope.boundingBox()
        centroid = envelope.centroid().asPoint()
        geojson = envelope.asJson()
        # write to file
        geojson_filename = "project_bounds.geojson"
        geojson_path = os.path.abspath(os.path.join(self.txt_outpath.text(), geojson_filename).replace("\\", "/"))
        with open(geojson_path, 'w') as f:
            f.write(geojson)

        project_bounds = ProjectBounds(centroid=Coords(centroid.x(), centroid.y()),
                                       bounding_box=BoundingBox(minLat=extent.yMinimum(),
                                                                minLng=extent.xMinimum(),
                                                                maxLat=extent.yMaximum(),
                                                                maxLng=extent.xMaximum()),
                                       filepath=geojson_filename)

        path = os.path.abspath(os.path.join(self.txt_outpath.text(), "project.rs.xml").replace("\\", "/"))

        metadata_values = [Meta('QRiS Project Name', self.qris_project.name),
                           Meta('QRiS Project Description', self.qris_project.description),
                           Meta('ModelVersion', '1')]

        for key, value in self.qris_project.metadata.items():
            # if tags are empty, skip
            if key == "tags":
                continue
            if value == "":
                continue
            metadata_values.append(Meta(key, value))

        self.rs_project = Project(name=self.txt_rs_name.text(),
                                  proj_path=path,
                                  project_type='QRiS',
                                  meta_data=MetaData(values=metadata_values),
                                  description=self.txt_description.toPlainText(),
                                  bounds=project_bounds)

        date_created = QtCore.QDateTime.currentDateTime()

        raster_datasets = []
        for raster_id, raster in self.qris_project.rasters.items():
            # check if raster is surface or context
            if raster.is_context:
                raster_xml_id = f'context_{raster_id}'
            else:
                raster_xml_id = f'surface_{raster_id}'

            raster_path = os.path.abspath(os.path.join(os.path.dirname(self.qris_project.project_file), raster.path).replace("\\", "/"))
            if not os.path.exists(os.path.dirname(raster_path)):
                os.makedirs(os.path.dirname(raster_path))
            shutil.copy(raster_path, os.path.abspath(os.path.join(self.txt_outpath.text(), raster.path).replace("\\", "/")))

            raster_datasets.append(Dataset(xml_id=raster_xml_id,
                                           name=raster.name,
                                           path=raster.path,
                                           ds_type='Raster'))

        input_layers = []
        for aoi_id, aoi in self.qris_project.masks.items():

            if not aoi.mask_type.id == AOI_MASK_TYPE_ID:
                continue

            view_name = f'vw_aoi_{aoi_id}'
            self.create_spatial_view(view_name=view_name,
                                     fc_name='aoi_features',
                                     field_name='mask_id',
                                     id_value=aoi_id,
                                     out_geopackage=out_geopackage,
                                     geom_type='POLYGON')

            input_layers.append(GeopackageLayer(lyr_name=view_name,
                                                name=aoi.name,
                                                ds_type=GeoPackageDatasetTypes.VECTOR))

        for sample_frame_id, sample_frame in self.qris_project.masks.items():

            if sample_frame.mask_type.id == AOI_MASK_TYPE_ID:
                continue

            view_name = f'vw_sample_frame_{sample_frame_id}'
            self.create_spatial_view(view_name=view_name,
                                     fc_name='mask_features',
                                     field_name='mask_id',
                                     id_value=sample_frame_id,
                                     out_geopackage=out_geopackage,
                                     geom_type='POLYGON')

            input_layers.append(GeopackageLayer(lyr_name=view_name,
                                                name=sample_frame.name,
                                                ds_type=GeoPackageDatasetTypes.VECTOR))

        for profile_id, profile in self.qris_project.profiles.items():
            profile_fc = 'profile_centerlines' if profile.profile_type_id == 2 else 'profile_features'

            view_name = f'vw_profile_{profile_id}'
            self.create_spatial_view(view_name=view_name,
                                     fc_name=profile_fc,
                                     field_name='profile_id',
                                     id_value=profile_id,
                                     out_geopackage=out_geopackage,
                                     geom_type='LINESTRING')

            input_layers.append(GeopackageLayer(lyr_name=view_name,
                                                name=profile.name,
                                                ds_type=GeoPackageDatasetTypes.VECTOR))

        for xsection_id, xsection in self.qris_project.cross_sections.items():

            view_name = f'vw_cross_section_{xsection_id}'
            self.create_spatial_view(view_name=view_name,
                                     fc_name='cross_section_features',
                                     field_name='cross_section_id',
                                     id_value=xsection_id,
                                     out_geopackage=out_geopackage,
                                     geom_type='LINESTRING')

            input_layers.append(GeopackageLayer(lyr_name=view_name,
                                                name=xsection.name,
                                                ds_type=GeoPackageDatasetTypes.VECTOR))

        gpkg = Geopackage(xml_id=f'inputs_gpkg',
                          name=f'Inputs',
                          path='qris.gpkg',
                          layers=input_layers)

        # need to prepare the Watershed catchments (pour points)
        pour_point_gpkgs = []
        for pour_point_id, pour_point in self.qris_project.pour_points.items():
            pour_point_layers = []
            view_name = f'vw_pour_point_{pour_point_id}'
            self.create_spatial_view(view_name=view_name,
                                     fc_name='pour_points',
                                     field_name='fid',
                                     id_value=pour_point_id,
                                     out_geopackage=out_geopackage,
                                     geom_type='POINT')

            pour_point_layers.append(GeopackageLayer(lyr_name=view_name,
                                                     name=pour_point.name,
                                                     ds_type=GeoPackageDatasetTypes.VECTOR))

            catchment_view = f'vw_catchment_{pour_point_id}'
            self.create_spatial_view(view_name=catchment_view,
                                     fc_name='catchments',
                                     field_name='pour_point_id',
                                     id_value=pour_point_id,
                                     out_geopackage=out_geopackage,
                                     geom_type='POLYGON')

            pour_point_layers.append(GeopackageLayer(lyr_name=catchment_view,
                                                     name=pour_point.name,
                                                     ds_type=GeoPackageDatasetTypes.VECTOR))

            pour_point_gpkgs.append(Geopackage(xml_id=f'pour_points_{pour_point_id}_gpkg',
                                               name=pour_point.name,
                                               path='qris.gpkg',
                                               layers=pour_point_layers))

        # context vectors
        context_layers = []
        for scratch_vector_id, scratch_vector in self.qris_project.scratch_vectors.items():
            # get the geom type for the feature class
            geom_type: str = None
            with sqlite3.connect(scratch_gpkg_path(self.qris_project.project_file)) as conn:
                curs = conn.cursor()
                curs.execute(f"SELECT geometry_type_name FROM gpkg_geometry_columns WHERE table_name = '{scratch_vector.fc_name}'")
                geom_type = curs.fetchone()[0]

            context_layers.append(GeopackageLayer(summary=f'context_{geom_type.lower()}',
                                                  lyr_name=scratch_vector.fc_name,
                                                  name=scratch_vector.name,
                                                  ds_type=GeoPackageDatasetTypes.VECTOR))

        context_gpkg = Geopackage(xml_id=f'context_gpkg',
                                  name=f'Context',
                                  path='context/feature_classes.gpkg',
                                  layers=context_layers)

        self.rs_project.realizations.append(Realization(xml_id=f'inputs',
                                                        name='Inputs',
                                                        date_created=date_created.toPyDateTime(),
                                                        product_version=qris_version,
                                                        datasets=raster_datasets + [gpkg, context_gpkg] + pour_point_gpkgs))

        all_photo_metadata = {}
        with sqlite3.connect(out_geopackage) as conn:
            # iterate through dce_points and get metadata for each photo
            curs = conn.cursor()
            curs.execute("SELECT metadata FROM dce_points")
            rows = curs.fetchall()
            for row in rows:
                metadata = json.loads(row[0])
                if 'Photo Path' in metadata:
                    all_photo_metadata[metadata['Photo Path']] = metadata

        # find the Events node in the tree
        events_node = self.export_layers_model.findItems("Events")[0]
        # iterate through the events and add the selected ones to the project
        for i in range(events_node.rowCount()):
            event_item = events_node.child(i)
            if event_item.checkState() == QtCore.Qt.Unchecked:
                continue
            event: Event = event_item.data(QtCore.Qt.UserRole)
            event_type = "DCE" if event.event_type.id == 1 else "Design"

            # Search for photos for the dce in the photos folder
            photo_datasets = []

            source_photos_dir = os.path.abspath(os.path.join(os.path.dirname(self.qris_project.project_file), "photos", f'dce_{str(event.id).zfill(3)}').replace("\\", "/"))
            photo_dce_folder = os.path.abspath(os.path.join(self.txt_outpath.text(), "photos", f'dce_{str(event.id).zfill(3)}').replace("\\", "/"))
            if os.path.exists(source_photos_dir):
                shutil.copytree(source_photos_dir, photo_dce_folder)
                # list photos in the photos folder
                for photo in os.listdir(photo_dce_folder):
                    photo_metadata = all_photo_metadata[photo]
                    photo_id = os.path.splitext(photo)[0]
                    # get the lat long of the photo
                    photo_meta = MetaData(values=[Meta('lat', photo_metadata['latitude']),
                                                Meta('long', photo_metadata['longitude']),
                                                Meta('timestamp', photo_metadata['timestamp'])
                                                ])

                    photo_datasets.append(Dataset(xml_id=photo_id,
                                                name=photo,
                                                path=f'photos/dce_{str(event.id).zfill(3)}/{photo}',
                                                meta_data=photo_meta,
                                                ds_type='Image'))

            meta = MetaData(values=[Meta(event_type, "")])
            # prepare the datasets
            geopackage_layers = []
            for layer in event.event_layers:
                geom_type = layer.layer.geom_type
                if geom_type == "NoGeometry":
                    continue
                if geom_type == "Point":
                    fc_name = 'dce_points'
                elif geom_type == "Linestring":
                    fc_name = 'dce_lines'
                elif geom_type == "Polygon":
                    fc_name = 'dce_polygons'
                else:
                    continue
                view_name = f'vw_{layer.layer.fc_name}_{event.id}'

                layer_fields: list = layer.layer.metadata.get('fields', None)
                out_fields = '*'
                if layer_fields is not None and len(layer_fields) > 0:
                    field_names = [field['label'] for field in layer_fields]
                    out_fields = ", ".join([f'json_extract(metadata, \'$.{field}\') AS "{field}"' for field in field_names])
                sql = f"CREATE VIEW {view_name} AS SELECT fid, geom, event_id, event_layer_id, {out_fields}, metadata FROM {fc_name} WHERE event_id == {event.id} and event_layer_id == {layer.layer.id}"
                self.create_spatial_view(view_name=view_name,
                                         fc_name=fc_name,
                                         field_name='event_id',
                                         id_value=event.id,
                                         out_geopackage=out_geopackage,
                                         geom_type=geom_type.upper(),
                                         sql=sql)

                gp_lyr = GeopackageLayer(lyr_name=view_name,
                                         name=layer.name,
                                         ds_type=GeoPackageDatasetTypes.VECTOR)
                geopackage_layers.append(gp_lyr)

            gpkg = Geopackage(xml_id=f'{event.id}_gpkg',
                              name=f'{event.name}',
                              path='qris.gpkg',
                              layers=geopackage_layers)

            # # self.rs_project.common_datasets.append(gpkg)
            # ds = [RefDataset(lyr.lyr_name, lyr) for lyr in geopackage_layers]

            realization = Realization(xml_id=f'realization_qris_{event.id}',
                                      name=event.name,
                                      date_created=date_created.toPyDateTime(),
                                      product_version=qris_version,
                                      datasets=[gpkg] + photo_datasets,
                                      meta_data=meta)

            # add description if it exists
            if event.description:
                realization.description = event.description

            self.rs_project.realizations.append(realization)

        # add analyses
        analysis_node = self.export_layers_model.findItems("Analyses")[0]
        for i in range(analysis_node.rowCount()):
            analysis_item = analysis_node.child(i)
            if analysis_item.checkState() == QtCore.Qt.Unchecked:
                continue
            analysis: Analysis = analysis_item.data(QtCore.Qt.UserRole)

            geopackage_layers = []
            # analysis: Analysis = analysis
            sample_frame: Mask = analysis.mask

            # flatten the table of analysis metrics
            analysis_metrics = []
            for metric_id, metric in analysis.analysis_metrics.items():
                analysis_metrics.append([metric_id, metric.level_id])

            # create the analysis view
            analysis_view = f'vw_analysis_{analysis.id}'

            # prepare sql string for each metric
            sql_metric = ", ".join([f'CASE WHEN metric_id = {metric_id} THEN (CASE WHEN is_manual = 1 THEN manual_value ELSE automated_value END) END AS "{analysis_metric.metric.name}"' for metric_id, analysis_metric in analysis.analysis_metrics.items()])
            sql = f"""CREATE VIEW {analysis_view} AS SELECT * from mask_features JOIN (SELECT mask_feature_id, {sql_metric} FROM metric_values JOIN metrics on metric_values.metric_id == metrics.id WHERE metric_values.analysis_id = {analysis_id} Group BY mask_feature_id) AS x ON mask_features.fid = x.mask_feature_id"""
            self.create_spatial_view(view_name=analysis_view,
                                     fc_name=None,
                                     field_name=None,
                                     id_value=None,
                                     out_geopackage=out_geopackage,
                                     geom_type="POLYGON",
                                     sql=sql)

            gp_lyr = GeopackageLayer(lyr_name=analysis_view,
                                     name=analysis.name,
                                     ds_type=GeoPackageDatasetTypes.VECTOR)
            geopackage_layers.append(gp_lyr)

            gpkg = Geopackage(xml_id=f'{analysis.id}_gpkg',
                              name=f'{analysis.name}',
                              path='qris.gpkg',
                              layers=geopackage_layers)

            realization = Realization(xml_id=f'analysis_{analysis.id}',
                                      name=analysis.name,
                                      date_created=date_created.toPyDateTime(),
                                      product_version=qris_version,
                                      datasets=[gpkg])
            # meta_data=meta)

            self.rs_project.realizations.append(realization)

        self.rs_project.write()

        return super().accept()

    @staticmethod
    def create_spatial_view(view_name: str, fc_name, field_name: str, id_value: int, out_geopackage: str, geom_type: str, epsg: int = 4326, sql: str = None):
        # create spaitail view of the aoi
        sql = sql if sql is not None else f"CREATE VIEW {view_name} AS SELECT * FROM {fc_name} WHERE {field_name} == {id_value}"
        with sqlite3.connect(out_geopackage) as conn:
            curs = conn.cursor()
            curs.execute(sql)
            # add view to geopackage
            sql = "INSERT INTO gpkg_contents (table_name, data_type, identifier, description, srs_id) VALUES (?, ?, ?, ?, ?)"
            curs.execute(sql, [view_name, "features", view_name, "", epsg])
            sql = "INSERT INTO gpkg_geometry_columns (table_name, column_name, geometry_type_name, srs_id, z, m) VALUES (?, ?, ?, ?, ?, ?)"
            curs.execute(sql, [view_name, 'geom', geom_type, epsg, 0, 0])
            conn.commit()

    def browse_path(self):

        if self.txt_outpath.text() is not None and self.txt_outpath.text() != "":
            basepath = self.txt_outpath.text()
        else:
            basepath = os.path.dirname(self.qris_project.project_file)
        path = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder', basepath, QtWidgets.QFileDialog.ShowDirsOnly)
        if path:
            # check if a project.rs.xml file already exists in the selected folder
            if os.path.exists(path):
                if os.path.exists(os.path.join(path, "project.rs.xml")):
                    msg = QtWidgets.QMessageBox()
                    msg.setIcon(QtWidgets.QMessageBox.Warning)
                    msg.setText("A Riverscapes project file already exists in the selected folder. Do you want to overwrite it?")
                    msg.setWindowTitle("Overwrite Project File?")
                    msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
                    msg.setDefaultButton(QtWidgets.QMessageBox.Cancel)
                    msg.setEscapeButton(QtWidgets.QMessageBox.Cancel)
                    ret = msg.exec_()
                    if ret == QtWidgets.QMessageBox.Cancel:
                        return

        self.set_output_path(path)

    def change_project_bounds(self):

        if self.opt_project_bounds_aoi.isChecked():
            self.cbo_project_bounds_aoi.setEnabled(True)
        else:
            self.cbo_project_bounds_aoi.setEnabled(False)

    def setupUi(self):

        self.setMinimumSize(500, 300)

        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)
        self.tabs = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tabs)

        # add grid layout
        self.grid = QtWidgets.QGridLayout()
        # self.vert.addLayout(self.grid)

        # add label and txt box for project name
        self.lbl_project = QtWidgets.QLabel("Riverscapes Project Name")
        self.grid.addWidget(self.lbl_project, 0, 0, 1, 1)

        self.txt_rs_name = QtWidgets.QLineEdit()
        self.txt_rs_name.setReadOnly(False)
        self.txt_rs_name.setText(self.qris_project.name)
        self.txt_rs_name.textChanged.connect(self.set_output_path)
        self.grid.addWidget(self.txt_rs_name, 0, 1, 1, 1)

        # add label and horizontal layout with textbox and small button for output path
        self.lbl_output = QtWidgets.QLabel("Output Path")
        self.grid.addWidget(self.lbl_output, 1, 0, 1, 1)

        self.horiz_output = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horiz_output, 1, 1, 1, 1)

        self.txt_outpath = QtWidgets.QLineEdit()
        self.txt_outpath.setReadOnly(True)
        self.horiz_output.addWidget(self.txt_outpath)

        self.btn_output = QtWidgets.QPushButton("...")
        self.btn_output.setMaximumWidth(30)
        self.btn_output.clicked.connect(self.browse_path)
        self.horiz_output.addWidget(self.btn_output)

        self.lbl_project_bounds = QtWidgets.QLabel("Project Bounds")
        self.grid.addWidget(self.lbl_project_bounds, 2, 0, 1, 1, QtCore.Qt.AlignTop)

        self.vert_project_bounds = QtWidgets.QVBoxLayout()
        self.grid.addLayout(self.vert_project_bounds, 2, 1, 1, 1)

        self.opt_project_bounds_all = QtWidgets.QRadioButton("Use all QRiS layers")
        self.opt_project_bounds_all.setChecked(True)
        self.opt_project_bounds_all.clicked.connect(self.change_project_bounds)
        self.vert_project_bounds.addWidget(self.opt_project_bounds_all)

        self.horiz_project_bounds_aoi = QtWidgets.QHBoxLayout()
        self.vert_project_bounds.addLayout(self.horiz_project_bounds_aoi)

        self.opt_project_bounds_aoi = QtWidgets.QRadioButton("Use AOI")
        self.opt_project_bounds_aoi.clicked.connect(self.change_project_bounds)
        self.horiz_project_bounds_aoi.addWidget(self.opt_project_bounds_aoi)

        self.cbo_project_bounds_aoi = QtWidgets.QComboBox()
        self.cbo_project_bounds_aoi.addItem("Select AOI")
        self.cbo_project_bounds_aoi.setEnabled(False)
        self.horiz_project_bounds_aoi.addWidget(self.cbo_project_bounds_aoi)

        # add multiline box for description
        self.lbl_description = QtWidgets.QLabel("Description")
        self.grid.addWidget(self.lbl_description, 3, 0, 1, 1, QtCore.Qt.AlignTop)

        self.txt_description = QtWidgets.QTextEdit()
        self.txt_description.setReadOnly(False)
        self.txt_description.setText(self.qris_project.description)
        self.grid.addWidget(self.txt_description, 3, 1, 1, 1)

        # add vertical spacer
        self.vert.addStretch()

        self.tabProperties = QtWidgets.QWidget()
        self.tabs.addTab(self.tabProperties, 'Export Properties')
        self.tabProperties.setLayout(self.grid)

        # Export Tab
        self.export_tree = QtWidgets.QTreeView()
        self.export_tree.setHeaderHidden(True)
        self.tabs.addTab(self.export_tree, 'Export Layers')


        # add standard form buttons
        self.vert.addLayout(add_standard_form_buttons(self, "export_metrics"))
