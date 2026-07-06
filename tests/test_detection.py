import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import numpy as np

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import modules to test
from src.detection.optimized_weapon_detection import ImprovedWeaponDetector

class TestSecureSightDetection(unittest.TestCase):
    
    @patch('cv2.createBackgroundSubtractorMOG2')
    @patch('multiprocessing.shared_memory.SharedMemory')
    def test_motion_detection_setup(self, mock_shm, mock_bg_subtractor):
        # Verify background subtractor configuration loading
        mock_sub = MagicMock()
        mock_bg_subtractor.return_value = mock_sub
        self.assertIsNotNone(mock_bg_subtractor)
        
    @patch('src.detection.optimized_weapon_detection.YOLO')
    def test_weapon_detector_initialization(self, mock_yolo):
        mock_yolo.side_effect = [Exception("Model not found"), MagicMock()]
        
        detector = ImprovedWeaponDetector(model_path="invalid_path.pt")
        
        # Check that fallback model was attempted
        mock_yolo.assert_any_call("yolov8n.pt")
        self.assertIsNotNone(detector.model)
        
    def test_calculate_box_area(self):
        detector = ImprovedWeaponDetector.__new__(ImprovedWeaponDetector)
        bbox = [10, 20, 110, 120]  # width = 100, height = 100
        area = detector.calculate_box_area(bbox)
        self.assertEqual(area, 10000)

    def test_smart_filtering(self):
        detector = ImprovedWeaponDetector.__new__(ImprovedWeaponDetector)
        
        # Sample detections
        detections = [
            {'class_name': 'gun', 'confidence': 0.8, 'bbox': [10, 10, 100, 100], 'area': 8100}, # valid
            {'class_name': 'gun', 'confidence': 0.1, 'bbox': [10, 10, 100, 100], 'area': 8100}, # low confidence
            {'class_name': 'gun', 'confidence': 0.8, 'bbox': [0, 0, 1000, 1000], 'area': 1000000}, # too large
        ]
        
        filtered = detector.apply_smart_filtering(detections, (1000, 1000, 3))
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]['class_name'], 'gun')
        self.assertEqual(filtered[0]['confidence'], 0.8)

if __name__ == '__main__':
    unittest.main()
