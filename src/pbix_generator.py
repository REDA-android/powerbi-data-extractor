"""
Power BI Template (.pbit / .pbix) Programmatic Generator.
Packages extracted tabular records into a native Power BI file container
including DataModelSchema, Visual Layouts, Themes, and embedded Data Queries.
"""

import io
import json
import zipfile
from typing import List, Dict, Any


class PBIXGenerator:
    """Generates official Power BI Template (.pbit) archives recognized by Power BI Desktop."""

    @staticmethod
    def generate_pbix_bytes(records: List[Dict[str, Any]], report_title: str = "PowerBI Extracted Report") -> bytes:
        """
        Creates a valid Power BI archive containing:
        - DataModelSchema (TMSL)
        - Report/Layout (JSON)
        - [Content_Types].xml
        - Version & Settings
        """
        if not records:
            records = [{"Item": "Aucune donnee", "Valeur": 0}]

        columns = list(records[0].keys())

        # 1. Build DataModelSchema (TMSL - Tabular Model Schema JSON)
        data_model_schema = PBIXGenerator._build_data_model_schema(records, columns)

        # 2. Build Visual Layout (JSON)
        layout = PBIXGenerator._build_report_layout(report_title, columns)

        # 3. Build Content Types XML
        content_types = PBIXGenerator._build_content_types()

        # 4. Build Version & Settings
        version = "1.28"
        settings = json.dumps({"reportProperties": {"hideVisualContainerHeader": False}})

        # Package into ZIP container (.pbit is a zip container with UTF-16LE DataModelSchema and UTF-16LE Layout)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # DataModelSchema must be UTF-16LE encoded in Power BI specifications
            zf.writestr("DataModelSchema", json.dumps(data_model_schema, indent=2).encode("utf-16-le"))
            # Layout is UTF-16LE encoded in Power BI specifications
            zf.writestr("Report/Layout", json.dumps(layout, indent=2).encode("utf-16-le"))
            # Content Types XML
            zf.writestr("[Content_Types].xml", content_types.encode("utf-8"))
            # Version
            zf.writestr("Version", version.encode("utf-16-le"))
            # Settings
            zf.writestr("Settings", settings.encode("utf-16-le"))

        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def _build_data_model_schema(records: List[Dict[str, Any]], columns: List[str]) -> Dict[str, Any]:
        """Constructs Tabular Model Schema Language (TMSL) representation."""
        tmsl_columns = []
        for col in columns:
            sample_val = records[0].get(col)
            data_type = "string"
            if isinstance(sample_val, (int, float)):
                data_type = "double"
            elif isinstance(sample_val, bool):
                data_type = "boolean"

            tmsl_columns.append({
                "name": col,
                "dataType": data_type,
                "sourceColumn": col,
                "summarizeBy": "none" if data_type == "string" else "sum",
            })

        # M Query to embed records as Table.FromRecords
        records_json = json.dumps(records)
        m_expression = f"""let
    Source = Json.Document('{records_json}'),
    #"Converted to Table" = Table.FromRecords(Source)
in
    #"Converted to Table" """

        return {
            "name": "PowerBIModel",
            "compatibilityLevel": 1550,
            "model": {
                "culture": "fr-FR",
                "tables": [
                    {
                        "name": "DonneesExtraites",
                        "columns": tmsl_columns,
                        "partitions": [
                            {
                                "name": "DonneesExtraites-Partition",
                                "mode": "import",
                                "source": {
                                    "type": "m",
                                    "expression": m_expression,
                                }
                            }
                        ]
                    }
                ]
            }
        }

    @staticmethod
    def _build_report_layout(title: str, columns: List[str]) -> Dict[str, Any]:
        """Constructs visual container layout in Power BI Layout JSON format."""
        return {
            "id": 0,
            "name": "Page1",
            "displayName": "Rapport Extrait",
            "filters": "[]",
            "ordinal": 0,
            "visualContainers": [
                {
                    "x": 20,
                    "y": 20,
                    "z": 0,
                    "width": 1240,
                    "height": 680,
                    "config": json.dumps({
                        "name": "VisualTable1",
                        "layouts": [{"id": 0, "position": {"x": 20, "y": 20, "width": 1240, "height": 680}}],
                        "singleVisual": {
                            "visualType": "tableEx",
                            "projections": {
                                "Values": [{"queryRef": f"DonneesExtraites.{col}"} for col in columns]
                            }
                        }
                    })
                }
            ],
            "config": json.dumps({
                "version": "5.50",
                "themeCollection": {"baseTheme": {"name": "CY24SU08", "version": "5.50"}}
            })
        }

    @staticmethod
    def _build_content_types() -> str:
        return """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json" />
  <Default Extension="xml" ContentType="application/xml" />
  <Override PartName="/DataModelSchema" ContentType="application/json" />
  <Override PartName="/Report/Layout" ContentType="application/json" />
  <Override PartName="/Settings" ContentType="application/json" />
  <Override PartName="/Version" ContentType="application/json" />
</Types>"""
