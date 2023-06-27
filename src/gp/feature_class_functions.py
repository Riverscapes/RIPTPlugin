import os

from osgeo import ogr
from osgeo import osr
from shapely.wkb import loads as wkbload, dumps as wkbdumps
from osgeo.gdal import Warp, WarpOptions
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsVectorLayer, QgsGeometry

from qgis.gui import QgsDataSourceSelectDialog
from qgis.core import QgsMapLayer, QgsWkbTypes
from qgis.utils import iface

from ..model.db_item import DBItem
from ..model.profile import Profile
from ..model.project import Project
from ..model.mask import REGULAR_MASK_TYPE_ID, AOI_MASK_TYPE_ID


def check_geometry_type(path) -> int:

    ds = ogr.Open(path)
    layer = ds.GetLayer(0)
    return layer.GetGeomType()


def flip_line_geometry(project: Project, profile: Profile):

    if profile.profile_type_id == Profile.ProfileTypes.CENTERLINE_PROFILE_TYPE:
        layer_name = 'profile_centerlines'
    else:
        layer_name = 'profile_features'

    feature_layer = QgsVectorLayer(f'{project.project_file}|layername={layer_name}')
    feature_layer.setSubsetString(f'profile_id = {profile.id}')
    feature_layer.startEditing()
    feats = feature_layer.getFeatures()
    for feat in feats:
        fid = feat.id()
        pts = feat.geometry().asPolyline()
        pts.reverse()
        out_geom = QgsGeometry.fromPolylineXY(pts)
        feature_layer.changeGeometry(fid, out_geom)
    feature_layer.commitChanges()


def import_mask(source_path: str, dest_path: str, mask_id: int, attributes: dict = {}, mask_type=REGULAR_MASK_TYPE_ID, clip_mask_id: int = None) -> None:
    """
    Copy the features from a source feature class to a destination mask feature class.
    The mask record must already exist. The attributes is a dictionary of source column
    names keyed to destination column names. If not None then these attributes will be copied in
    """

    ogr.UseExceptions()

    mask_layer_name = 'aoi_features' if mask_type.id == AOI_MASK_TYPE_ID else 'mask_features'
    if os.path.splitext(source_path)[1].lower() == ".shp":
        src_path = source_path
        src_layer_name = None
    else:
        src_path, src_layer_name = source_path.split('|layername=')
    src_dataset = ogr.Open(src_path)
    src_layer = src_dataset.GetLayer(src_layer_name if src_layer_name is not None else 0)
    src_srs = src_layer.GetSpatialRef()
    fid_field_name = src_layer.GetFIDColumn()

    gpkg_driver = ogr.GetDriverByName('GPKG')
    dst_dataset = gpkg_driver.Open(dest_path, 1)
    dst_layer = dst_dataset.GetLayerByName(mask_layer_name)
    dst_srs = dst_layer.GetSpatialRef()
    dst_layer_def = dst_layer.GetLayerDefn()

    clip_geom = None
    if clip_mask_id is not None:
        clip_layer = dst_dataset.GetLayer('aoi_features')
        clip_layer.SetAttributeFilter(f'mask_id = {clip_mask_id}')
        clip_feat = clip_layer.GetNextFeature()
        clip_geom = clip_feat.GetGeometryRef()

    transform = osr.CoordinateTransformation(src_srs, dst_srs)

    feats = 0
    for src_feature in src_layer:
        geom = src_feature.GetGeometryRef()
        geom.Transform(transform)
        if clip_geom is not None:
            geom = clip_geom.Intersection(geom)
            if geom.IsEmpty() or geom.GetArea() == 0.0:
                continue
            #     raise Exception("Clipping mask has produced an empty geometry.")

        dst_feature = ogr.Feature(dst_layer_def)
        dst_feature.SetGeometry(geom)
        dst_feature.SetField('mask_id', mask_id)
        for src_field, dst_field in attributes.items():
            # Retrieve the field value differently if the feature ID is being used
            value = str(src_feature.GetFID()) if src_field == fid_field_name else src_feature.GetField(src_field)
            dst_feature.SetField(dst_field, value)

        err = dst_layer.CreateFeature(dst_feature)
        dst_feature = None
        feats += 1

    src_dataset = None
    dst_dataset = None

    if feats == 0:
        raise Exception("No features were imported. Check that the source and destination coordinate systems are the same and that the source and aoi mask geometries intersect.")


def import_existing(source_path: str, dest_path: str, dest_layer_name: str, output_id: int, output_id_field: str, fid_key: dict = {}, clip_mask_id: int = None, attributes_prefix: str = None) -> None:
    """
    Copy the features from a source feature class to a destination mask feature class.
    The mask record must already exist. The attributes is a dictionary of source column
    names keyed to destination column names. If not None then these attributes will be copied in
    """

    ogr.UseExceptions()

    if os.path.splitext(source_path)[1].lower() == ".shp":
        src_path = source_path
        src_layer_name = None
    else:
        src_path, src_layer_name = source_path.split('|layername=')
    src_dataset = ogr.Open(src_path)
    src_layer = src_dataset.GetLayer(src_layer_name if src_layer_name is not None else 0)
    src_srs = src_layer.GetSpatialRef()
    fid_field_name = src_layer.GetFIDColumn()

    gpkg_driver = ogr.GetDriverByName('GPKG')
    dst_dataset = gpkg_driver.Open(dest_path, 1)
    dst_layer = dst_dataset.GetLayerByName(dest_layer_name)
    dst_srs = dst_layer.GetSpatialRef()
    dst_layer_def = dst_layer.GetLayerDefn()

    if attributes_prefix is not None:
        attributes = {}
        for field in src_layer.schema:
            # copy field from source to destination and add prefix to the field name
            attributes[field.name] = f'{attributes_prefix}_{field.name}'
            field_defn = ogr.FieldDefn(attributes[field.name], field.type)
            dst_layer.CreateField(field_defn)

    clip_geom = None
    if clip_mask_id is not None:
        clip_layer = dst_dataset.GetLayer('aoi_features')
        clip_layer.SetAttributeFilter(f'mask_id = {clip_mask_id}')
        clip_feat = clip_layer.GetNextFeature()
        clip_geom = clip_feat.GetGeometryRef()

    transform = osr.CoordinateTransformation(src_srs, dst_srs)

    feats = 0
    for src_feature in src_layer:
        geom = src_feature.GetGeometryRef()
        geom.Transform(transform)
        if clip_geom is not None:
            geom = clip_geom.Intersection(geom)
            if geom.IsEmpty() or geom.GetArea() == 0.0:
                continue

        dst_feature = ogr.Feature(dst_layer_def)
        dst_feature.SetGeometry(geom)
        dst_feature.SetField(output_id_field, output_id)
        for src_field, dst_field in fid_key.items():
            # Retrieve the field value differently if the feature ID is being used
            value = str(src_feature.GetFID()) if src_field == fid_field_name else src_feature.GetField(src_field)
            dst_feature.SetField(dst_field, value)
        if attributes_prefix is not None:
            for src_field, dst_field in attributes.items():
                # Retrieve the field value differently if the feature ID is being used
                value = str(src_feature.GetFID()) if src_field == fid_field_name else src_feature.GetField(src_field)
                dst_feature.SetField(dst_field, value)

        err = dst_layer.CreateFeature(dst_feature)
        dst_feature = None
        feats += 1

    src_dataset = None
    dst_dataset = None

    if feats == 0 or err != 0:
        raise Exception("No features were imported. Check that the source and destination coordinate systems are the same and that the source and aoi mask geometries intersect.")


def browse_raster(parent, description: str) -> str:
    # https://qgis.org/pyqgis/master/gui/QgsDataSourceSelectDialog.html
    frm_browse = QgsDataSourceSelectDialog(parent=parent, setFilterByLayerType=True, layerType=QgsMapLayer.RasterLayer)
    frm_browse.setDescription(description)

    frm_browse.exec()
    uri = frm_browse.uri()
    if uri is not None and uri.isValid():
        return uri.uri

    return None


def browse_vector(parent, description: str, geometry_type: QgsWkbTypes.GeometryType) -> str:
    """
    https://qgis.org/pyqgis/master/gui/QgsDataSourceSelectDialog.html
    https://api.qgis.org/api/classQgsWkbTypes.html#a60e72c2f73cb07fdbcdbc2d5068b5d9c

    QgsWkbTypes.GeometryType.PointGeometry
    QgsWkbTypes.GeometryType.LineGeometry
    QgsWkbTypes.GeometryType.PolygonGeometry
    QgsWkbTypes.GeometryType.UnknownGeometry
    QgsWkbTypes.GeometryType.NullGeometry
    """

    frm_browse = QgsDataSourceSelectDialog(parent=parent, setFilterByLayerType=True, layerType=QgsMapLayer.VectorLayer)
    frm_browse.setDescription(description)

    frm_browse.exec()
    uri = frm_browse.uri()
    if uri is not None and uri.isValid():
        layer = QgsVectorLayer(uri.uri, '', 'ogr')
        if geometry_type is not None and geometry_type != layer.geometryType():
            QMessageBox.warning(parent, 'Invalid Geometry Type',
                                f'The layer is of geometry type {QgsWkbTypes.geometryDisplayString(layer.geometryType())} but must be of type {QgsWkbTypes.geometryDisplayString(geometry_type)}.')
            return None

        return uri.uri

    return None
