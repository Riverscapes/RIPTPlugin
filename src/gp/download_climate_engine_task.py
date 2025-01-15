import json
import sqlite3
import requests

import pandas as pd
from osgeo import ogr

from qgis.core import Qgis, QgsTask, QgsMessageLog, QgsFeature, QgsGeometry
from qgis.PyQt.QtCore import pyqtSignal

from ..lib.climate_engine import CLIMATE_ENGINE_API, get_api_key
from ..model.project import Project

from typing import List

MESSAGE_CATEGORY = 'DownloadClimateEngineTask'


class DownloadClimateEngineTimeseriesTask(QgsTask):
    """
    Task to download data from Climate Engine.
    """

    # Signal to notify when done
    download_complete = pyqtSignal(bool)

    def __init__(self, qris_project: Project, name: str, dataset: str, variables: List[str], start_date: str, end_date: str, features: ogr.Feature, area_reducer: str='mean', temporal_statistic: str='mean'):
        super().__init__('Download Climate Engine Task', QgsTask.CanCancel)

        self.qris_project = qris_project
        self.name = name
        self.dataset = dataset
        self.variables = [variables] if isinstance(variables, str) else variables
        self.variables = variables
        self.start_date = start_date
        self.end_date = end_date
        self.features = features
        self.area_reducer = area_reducer
        self.temporal_statistic = temporal_statistic

    def run(self):
        """
        Run the task.
        """

        self.setProgress(0)

        try:
            api_key = get_api_key()
            if api_key is None:
                return None
            
            time_series_ids = {}

            steps = len(self.features)
            current_step = 0
            
            for feature in self.features:
                coordinates = []    
                if isinstance(feature, QgsFeature):
                    geometry: QgsGeometry = feature.geometry()
                    feature_id = feature.id()
                    if geometry.isMultipart():
                        part_coordinates = []
                        for part in geometry.asMultiPolygon():
                            for pt in part[0]:
                                part_coordinates.append([pt.x(), pt.y()])
                        coordinates.append(part_coordinates)
                    else:
                        for pt in geometry.asPolygon()[0]:
                            coordinates.append([pt.x(), pt.y()])
                else:
                    feature: ogr.Feature
                    geometry: ogr.Geometry = feature.GetGeometryRef()
                    feature_id = feature.GetFID()
                    if geometry.GetGeometryName() == 'POLYGON':
                        for i in range(geometry.GetPointCount()):
                            pt = geometry.GetPoint(i)
                            coordinates.append([pt[0], pt[1]])
                    else:
                        for i in range(geometry.GetGeometryCount()):
                            part: ogr.Geometry = geometry.GetGeometryRef(i)
                            part_coordinates = []
                            for j in range(part.GetPointCount()):
                                pt = part.GetPoint(j)
                                part_coordinates.append([pt[0], pt[1]])
                            coordinates.append(part_coordinates)

                params = {'dataset': self.dataset,
                        'variable': self.variables,
                        # 'temporal_statistic': self.temporal_statistic,
                        'area_reducer': self.area_reducer,
                        'start_date': self.start_date,
                        'end_date': self.end_date,
                        'coordinates': f'[{coordinates}]'}

                url = f'{CLIMATE_ENGINE_API}/timeseries/native/coordinates'
                headers = {'accept': 'application/json',
                        'Authorization': api_key}
                response = requests.get(url, params=params, headers=headers)
                response.raise_for_status()
                response_data = response.json()

                # if response_data is None:
                #     return False

                [timeseries] = response_data
                data = timeseries.get('Data', None)

                if data is None:
                    QgsMessageLog.logMessage(f'No Timeseries data for feature {feature_id} for one or more {self.variables} in {self.dataset}', MESSAGE_CATEGORY, Qgis.Warning)
                    continue

                df = pd.DataFrame(data)

                with sqlite3.connect(self.qris_project.project_file) as conn:
                    cursor = conn.cursor()
                    
                    for column in df.columns:
                        if column == 'Date':
                            continue
                        splits = column.split(' (')
                        if len(splits) == 1:
                            variable = column
                            units = ''                    
                        else:    
                            variable, units = splits 
                            units = units.replace(')', '')
                        df_values = df[['Date', column]]
                        df_values = df_values.set_index('Date')
                        values = list(df_values.itertuples(name=None))
                        machine_name = f'{self.dataset} {variable}'
                        if machine_name in time_series_ids:
                            time_series_id = time_series_ids[machine_name]
                        else:   
                            metadata = {
                                'units': units,
                                'start_date': self.start_date.strftime('%Y-%m-%d'), 
                                'end_date': self.end_date.strftime('%Y-%m-%d'), 
                                'description': self.variables[variable],
                                'dataset': self.dataset,
                                'variable': variable,
                                'area_reducer': self.area_reducer,
                                # 'temporal_statistic': self.temporal_statistic
                                }
                            cursor.execute('INSERT INTO time_series (name, source, url, metadata) VALUES (?, ?, ?, ?)', (self.name, 'Climate Engine', 'https://www.climateengine.org/', json.dumps(metadata)))
                            time_series_id = cursor.lastrowid
                            time_series_ids[machine_name] = time_series_id
                        cursor.executemany('INSERT INTO sample_frame_time_series (sample_frame_fid, time_series_id, time_value, value) VALUES (?, ?, ?, ?)', [(feature_id, time_series_id, date, value) for date, value in values])

                current_step += 1
                self.setProgress(100 * current_step / steps)

            return True
        
        except requests.exceptions.HTTPError as e:
            QgsMessageLog.logMessage(f'HTTP error occurred: {e}', MESSAGE_CATEGORY, Qgis.Critical)
            return False
        except Exception as e:
            QgsMessageLog.logMessage(f'Error downloading data: {e}', MESSAGE_CATEGORY, Qgis.Critical)
            return False

    def finished(self, result):
        """
        This function is automatically called when the task has completed (successfully or not).
        """
        if result:
            QgsMessageLog.logMessage('Download completed successfully.', MESSAGE_CATEGORY, Qgis.Info)
        else:
            QgsMessageLog.logMessage('Download failed.', MESSAGE_CATEGORY, Qgis.Critical)
            
        self.download_complete.emit(result)


    def cancel(self):
        """
        This function is automatically called when the task is canceled.
        """
        QgsMessageLog.logMessage('Download canceled.', MESSAGE_CATEGORY, Qgis.Warning)
        super().cancel()

        QgsMessageLog.logMessage(
            'Create New QRIS Project was canceled'.format(name=self.description()), MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
