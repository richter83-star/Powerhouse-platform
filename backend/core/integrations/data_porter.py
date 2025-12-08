
"""
Data Import/Export System
Handles bulk data operations with various formats
"""

import csv
import io
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class DataFormat(str, Enum):
    """Supported data formats"""
    JSON = "json"
    CSV = "csv"
    JSONL = "jsonl"  # JSON Lines
    XML = "xml"


class ExportConfig(BaseModel):
    """Export configuration"""
    format: DataFormat = DataFormat.JSON
    include_metadata: bool = True
    compression: Optional[str] = None  # "gzip", "zip"
    batch_size: int = 1000


class ImportConfig(BaseModel):
    """Import configuration"""
    format: DataFormat
    validate: bool = True
    skip_errors: bool = False
    batch_size: int = 1000
    upsert: bool = False  # Update if exists, insert if not


class ImportResult(BaseModel):
    """Import operation result"""
    total_records: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]] = []
    duration_seconds: float


class ExportResult(BaseModel):
    """Export operation result"""
    total_records: int
    file_size_bytes: int
    format: DataFormat
    duration_seconds: float


class DataPorter:
    """Handles data import and export operations"""
    
    def __init__(self):
        self.import_history: List[ImportResult] = []
        self.export_history: List[ExportResult] = []
    
    async def export_data(
        self,
        data: List[Dict[str, Any]],
        config: ExportConfig
    ) -> tuple[bytes, ExportResult]:
        """Export data to specified format"""
        start_time = datetime.utcnow()
        
        if config.format == DataFormat.JSON:
            output = self._export_json(data, config)
        elif config.format == DataFormat.CSV:
            output = self._export_csv(data)
        elif config.format == DataFormat.JSONL:
            output = self._export_jsonl(data)
        else:
            raise ValueError(f"Unsupported format: {config.format}")
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        result = ExportResult(
            total_records=len(data),
            file_size_bytes=len(output),
            format=config.format,
            duration_seconds=duration
        )
        
        self.export_history.append(result)
        return output, result
    
    async def import_data(
        self,
        content: Union[str, bytes],
        config: ImportConfig,
        validator: Optional[callable] = None
    ) -> tuple[List[Dict[str, Any]], ImportResult]:
        """Import data from specified format"""
        start_time = datetime.utcnow()
        
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        
        if config.format == DataFormat.JSON:
            records = self._import_json(content)
        elif config.format == DataFormat.CSV:
            records = self._import_csv(content)
        elif config.format == DataFormat.JSONL:
            records = self._import_jsonl(content)
        else:
            raise ValueError(f"Unsupported format: {config.format}")
        
        # Validation
        successful_records = []
        errors = []
        
        for idx, record in enumerate(records):
            try:
                if config.validate and validator:
                    validator(record)
                successful_records.append(record)
            except Exception as e:
                error = {
                    "record_index": idx,
                    "error": str(e),
                    "record": record
                }
                errors.append(error)
                
                if not config.skip_errors:
                    break
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        result = ImportResult(
            total_records=len(records),
            successful=len(successful_records),
            failed=len(errors),
            errors=errors,
            duration_seconds=duration
        )
        
        self.import_history.append(result)
        return successful_records, result
    
    def _export_json(
        self,
        data: List[Dict[str, Any]],
        config: ExportConfig
    ) -> bytes:
        """Export to JSON format"""
        output = {"data": data}
        
        if config.include_metadata:
            output["metadata"] = {
                "exported_at": datetime.utcnow().isoformat(),
                "record_count": len(data),
                "format": "json"
            }
        
        return json.dumps(output, indent=2, default=str).encode('utf-8')
    
    def _export_csv(self, data: List[Dict[str, Any]]) -> bytes:
        """Export to CSV format"""
        if not data:
            return b""
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue().encode('utf-8')
    
    def _export_jsonl(self, data: List[Dict[str, Any]]) -> bytes:
        """Export to JSON Lines format"""
        lines = [json.dumps(record, default=str) for record in data]
        return "\n".join(lines).encode('utf-8')
    
    def _import_json(self, content: str) -> List[Dict[str, Any]]:
        """Import from JSON format"""
        parsed = json.loads(content)
        
        # Handle both {"data": [...]} and direct array
        if isinstance(parsed, dict) and "data" in parsed:
            return parsed["data"]
        elif isinstance(parsed, list):
            return parsed
        else:
            raise ValueError("Invalid JSON structure")
    
    def _import_csv(self, content: str) -> List[Dict[str, Any]]:
        """Import from CSV format"""
        reader = csv.DictReader(io.StringIO(content))
        return list(reader)
    
    def _import_jsonl(self, content: str) -> List[Dict[str, Any]]:
        """Import from JSON Lines format"""
        lines = content.strip().split('\n')
        return [json.loads(line) for line in lines if line.strip()]
    
    def get_import_history(self) -> List[ImportResult]:
        """Get import history"""
        return self.import_history
    
    def get_export_history(self) -> List[ExportResult]:
        """Get export history"""
        return self.export_history


# Global instance
data_porter = DataPorter()
