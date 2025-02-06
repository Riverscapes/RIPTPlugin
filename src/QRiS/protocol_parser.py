import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FieldDefinition:
    id: str
    type: str
    label: str
    description: Optional[str] = None

@dataclass
class LayerDefinition:
    id: str
    version: str
    geom_type: str
    label: str
    symbology: str
    description: Optional[str] = None
    hierarchy: Optional[str] = None
    fields: List[FieldDefinition] = field(default_factory=list)

@dataclass
class MetricDefinition:
    id: str
    version: str
    calculation_machine_code: str
    label: str
    default_level: str
    description: Optional[str] = None
    definition_url: Optional[str] = None
    minimum_value: Optional[float] = None
    maximum_value: Optional[float] = None
    precision: Optional[int] = None

@dataclass
class ProtocolDefinition:
    machine_code: str
    version: str
    status: str
    label: str
    description: str
    url: str
    citation: str
    author: str
    creation_date: str
    updated_date: str
    layers: List[LayerDefinition] = field(default_factory=list)
    metrics: List[MetricDefinition] = field(default_factory=list)

def load_protocols(protocol_directory):
    """Load protocol from xml"""

    protocols = list()

    for filename in os.listdir(protocol_directory):
        if filename.endswith('.xml'):
            file_path = os.path.join(protocol_directory, filename)
            tree = ET.parse(file_path)
            root = tree.getroot()

            if root.tag != 'Protocol':
                continue

            protocol = ProtocolDefinition(
                machine_code=root.attrib.get('machine_code'),
                version=root.attrib.get('version'),
                status=root.attrib.get('status'),
                label=root.find('Label').text,
                description=root.find('Description').text,
                url=root.find('URL').text,
                citation=root.find('Citation').text,
                author=root.find('Author').text,
                creation_date=root.find('CreationDate').text,
                updated_date=root.find('UpdatedDate').text,
            )

            for layer_elem in root.findall('Layers/Layer'):
                
                fields = []
                for field_elem in layer_elem.findall('Fields/'):
                    
                    fieldtype = field_elem.tag
                    field = FieldDefinition(
                            id=field_elem.attrib.get('id'),
                            type=fieldtype,
                            label=field_elem.find('Label').text,
                            description=field_elem.find('Description').text if field_elem.find('Description') is not None else None
                        )
                    fields.append(field)

                layer = LayerDefinition(
                    id=layer_elem.attrib.get('id'),
                    version=layer_elem.attrib.get('version'),
                    geom_type=layer_elem.attrib.get('geom_type'),
                    label=layer_elem.find('Label').text,
                    symbology=layer_elem.find('Symbology').text,
                    description=layer_elem.find('Description').text if layer_elem.find('Description') is not None else None,
                    hierarchy=layer_elem.find('Hierarchy').text if layer_elem.find('Hierarchy') is not None else None,
                    fields=fields
                )
                protocol.layers.append(layer)

            for metric_elem in root.findall('Metrics/Metric'):
                metric = MetricDefinition(
                    id=metric_elem.attrib.get('id'),
                    version=metric_elem.attrib.get('version'),
                    calculation_machine_code=metric_elem.attrib.get('calculation_machine_code'),
                    label=metric_elem.find('Label').text,
                    default_level=metric_elem.find('DefaultLevel').text,
                    description=metric_elem.find('Description').text if metric_elem.find('Description') is not None else None,
                    definition_url=metric_elem.find('DefinitionURL').text if metric_elem.find('DefinitionURL') is not None else None,
                    minimum_value=float(metric_elem.find('MinimumValue').text) if metric_elem.find('MinimumValue') is not None else None,
                    maximum_value=float(metric_elem.find('MaximumValue').text) if metric_elem.find('MaximumValue') is not None else None,
                    precision=int(metric_elem.find('Precision').text) if metric_elem.find('Precision') is not None else None
                )
                protocol.metrics.append(metric)

            protocols.append(protocol)

    return protocols