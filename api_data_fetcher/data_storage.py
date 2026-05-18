"""
Data storage utilities for saving API responses
"""
import json
# import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd

try:
    from .logger import log_warning, log_info
except ImportError:
    from logger import log_warning, log_info


class DataStorage:
    """Handles saving fetched data to various formats"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def save_json(self, data: Any, filename: str = None) -> str:
        """
        Save data as JSON file
        
        Args:
            data: Data to save
            filename: Optional custom filename
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_{timestamp}.json"

        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf_8') as f:
            json.dump(data, f, indent=2, default=str)

        log_info(f"Saved JSON data to {filepath}")
        return str(filepath)

    def save_csv(self, data: List[Dict], filename: str = None) -> str:
        """
        Save list of dictionaries as CSV
        
        Args:
            data: List of dictionaries
            filename: Optional custom filename
            
        Returns:
            Path to saved file
        """
        if not data:
            log_warning("No data to save")
            return ""

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_{timestamp}.csv"

        filepath = self.output_dir / filename

        # Flatten nested dictionaries if needed
        flat_data = [self._flatten_dict(item) for item in data]

        df = pd.DataFrame(flat_data)
        df.to_csv(filepath, index=False)

        log_info(f"Saved CSV data to {filepath} ({len(data)} rows)")
        return str(filepath)

    def save_parquet(self, data: List[Dict], filename: str = None) -> str:
        """
        Save data as Parquet (efficient for large datasets)
        
        Args:
            data: List of dictionaries
            filename: Optional custom filename
            
        Returns:
            Path to saved file
        """
        if not data:
            log_warning("No data to save")
            return ""

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_{timestamp}.parquet"

        filepath = self.output_dir / filename

        df = pd.DataFrame(data)
        df.to_parquet(filepath, index=False)

        log_info(f"Saved Parquet data to {filepath}")
        return str(filepath)

    @staticmethod
    def _flatten_dict(data: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """
        Flatten nested dictionary for CSV export
        
        Args:
            data: Dictionary to flatten
            parent_key: Key from parent level
            sep: Separator for nested keys
            
        Returns:
            Flattened dictionary
        """
        items = []
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k

            if isinstance(v, dict):
                items.extend(DataStorage._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert list to string for CSV
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, v))

        return dict(items)
    