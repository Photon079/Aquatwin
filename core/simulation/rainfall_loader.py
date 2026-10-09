import pandas as pd
import logging
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class RainfallLoader:
    """Loads rainfall timeseries data for the simulation."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.data: pd.DataFrame = None
        
    def load(self) -> None:
        """Load rainfall CSV into a DataFrame."""
        try:
            logger.info(f"Loading rainfall data from {self.filepath}")
            self.data = pd.read_csv(self.filepath, parse_dates=['timestamp'])
            self.data.set_index('timestamp', inplace=True)
        except Exception as e:
            logger.error(f"Failed to load rainfall data: {e}")
            raise
            
    def get_rainfall_for_time(self, current_time: datetime) -> Dict[str, float]:
        """Get rainfall rate per catchment for a specific time."""
        if self.data is None:
            return {}
            
        try:
            nearest_idx = self.data.index.get_indexer([current_time], method='nearest')[0]
            row = self.data.iloc[nearest_idx]
            return row.to_dict()
        except Exception as e:
            logger.warning(f"Error fetching rainfall for time {current_time}: {e}")
            return {}
