from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """에이전트의 핵심 처리 로직"""
        pass
    
    def log_info(self, message: str):
        """정보 로그 출력"""
        self.logger.info(f"[{self.name}] {message}")
        print(f"[{self.name}] {message}")
    
    def log_error(self, message: str):
        """에러 로그 출력"""
        self.logger.error(f"[{self.name}] ERROR: {message}")
        print(f"[{self.name}] ERROR: {message}")
    
    def validate_input(self, input_data: Dict[str, Any], required_keys: List[str]) -> bool:
        """입력 데이터 검증"""
        for key in required_keys:
            if key not in input_data:
                self.log_error(f"Required key '{key}' not found in input data")
                return False
        return True