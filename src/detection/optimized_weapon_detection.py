#!/usr/bin/env python3

from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path
import json
import time

class ImprovedWeaponDetector:
    def __init__(self, model_path="../../data/models/best.pt"):
        self.model_path = model_path
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load the YOLO model"""
        try:
            self.model = YOLO(self.model_path)
            print(f"✅ Model loaded: {self.model_path}")
            return True
        except Exception as e:
            print(f"❌ Error loading model {self.model_path}: {e}. Trying fallback 'yolov8n.pt'...")
            try:
                self.model = YOLO("yolov8n.pt")
                print("✅ Fallback model 'yolov8n.pt' loaded successfully")
                return True
            except Exception as ex:
                print(f"❌ Failed to load fallback model: {ex}")
                return False
    
    def detect_weapons_optimized(self, image_path, 
                               confidence=0.3,      # Lower threshold from analysis
                               iou_threshold=0.5,   # NMS threshold
                               max_detections=10):  # Limit detections
        """
        Detect weapons with optimized parameters for better accuracy
        
        Args:
            image_path: Path to image
            confidence: Confidence threshold (0.3 recommended vs 0.5 default)
            iou_threshold: IoU threshold for Non-Maximum Suppression
            max_detections: Maximum number of detections per image
        """
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"❌ Could not load image: {image_path}")
            return []
        
        # Run detection with optimized parameters
        results = self.model(
            image,
            conf=confidence,
            iou=iou_threshold,
            max_det=max_detections,
            verbose=False
        )
        
        detections = []
        if results[0].boxes is not None:
            for box in results[0].boxes:
                detection = {
                    'class_id': int(box.cls[0]),
                    'class_name': self.model.names[int(box.cls[0])],
                    'confidence': float(box.conf[0]),
                    'bbox': box.xyxy[0].tolist(),  # [x1, y1, x2, y2]
                    'area': self.calculate_box_area(box.xyxy[0].tolist())
                }
                detections.append(detection)
        
        # Apply post-processing filters
        filtered_detections = self.apply_smart_filtering(detections, image.shape)
        
        return filtered_detections
    
    def calculate_box_area(self, bbox):
        """Calculate bounding box area"""
        x1, y1, x2, y2 = bbox
        return (x2 - x1) * (y2 - y1)
    
    def apply_smart_filtering(self, detections, image_shape):
        """Apply intelligent filtering to reduce false positives"""
        
        if not detections:
            return detections
        
        h, w = image_shape[:2]
        image_area = h * w
        
        filtered = []
        
        for det in detections:
            # Filter 1: Remove detections that are too large (likely false positives)
            box_area = det['area']
            area_ratio = box_area / image_area
            
            if area_ratio > 0.8:  # Skip if detection covers >80% of image
                continue
            
            # Filter 2: Remove very small detections (likely noise)
            if area_ratio < 0.001:  # Skip if detection is <0.1% of image
                continue
            
            # Filter 3: Confidence-based filtering per class
            min_confidence = {
                'gun': 0.25,
                'heavy-weapon': 0.3,
                'knife': 0.2,
                'handgun': 0.25,
                'rifle': 0.3,
                'sword': 0.2
            }
            
            class_name = det['class_name'].lower()
            required_conf = min_confidence.get(class_name, 0.3)
            
            if det['confidence'] < required_conf:
                continue
            
            filtered.append(det)
        
        # Sort by confidence (highest first)
        filtered.sort(key=lambda x: x['confidence'], reverse=True)
        
        return filtered
    
    def batch_test_optimized(self, test_dir, max_images=50):
        """Test the optimized detection on multiple images"""
        
        print(f"🧪 Testing optimized detection on {max_images} images...")
        
        image_files = list(Path(test_dir).glob("*.jpg"))[:max_images]
        
        total_detections = 0
        images_with_detections = 0
        detection_confidence_scores = []
        
        start_time = time.time()
        
        for i, img_path in enumerate(image_files, 1):
            if i % 10 == 0:
                print(f"   Processed {i}/{len(image_files)} images...")
            
            detections = self.detect_weapons_optimized(str(img_path))
            
            if detections:
                images_with_detections += 1
                total_detections += len(detections)
                
                # Collect confidence scores
                for det in detections:
                    detection_confidence_scores.append(det['confidence'])
        
        end_time = time.time()
        
        # Calculate metrics
        detection_rate = (images_with_detections / len(image_files)) * 100
        avg_detections_per_image = total_detections / len(image_files)
        avg_confidence = np.mean(detection_confidence_scores) if detection_confidence_scores else 0
        processing_time = (end_time - start_time) / len(image_files)
        
        print(f"\n📊 Optimized Detection Results:")
        print(f"   Images with detections: {images_with_detections}/{len(image_files)} ({detection_rate:.1f}%)")
        print(f"   Total detections: {total_detections}")
        print(f"   Avg detections per image: {avg_detections_per_image:.2f}")
        print(f"   Avg confidence score: {avg_confidence:.3f}")
        print(f"   Avg processing time: {processing_time:.3f}s per image")
        
        return {
            'detection_rate': detection_rate,
            'total_detections': total_detections,
            'avg_confidence': avg_confidence,
            'avg_processing_time': processing_time
        }
    
    def create_detection_sample(self, image_path, output_path=None):
        """Create a visual sample of optimized detection"""
        
        # Detect weapons
        detections = self.detect_weapons_optimized(image_path)
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            return None
        
        # Draw detections
        for det in detections:
            x1, y1, x2, y2 = [int(coord) for coord in det['bbox']]
            confidence = det['confidence']
            class_name = det['class_name']
            
            # Color based on class
            colors = {
                'gun': (0, 0, 255),        # Red
                'heavy-weapon': (0, 0, 255), # Red
                'knife': (0, 255, 255),    # Yellow
                'handgun': (0, 0, 255),    # Red
                'rifle': (0, 0, 255),      # Red
                'sword': (255, 0, 255)     # Magenta
            }
            
            color = colors.get(class_name.lower(), (0, 255, 0))  # Default green
            
            # Draw bounding box
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            
            # Draw label with confidence
            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(image, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), color, -1)
            cv2.putText(image, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Save annotated image
        if output_path is None:
            output_path = f"optimized_detection_{Path(image_path).stem}.jpg"
        
        cv2.imwrite(output_path, image)
        print(f"✅ Detection sample saved: {output_path}")
        
        return detections

def weapon_detection_process(shm_name, shape, output_queue, cam_id, lock):
    """
    Continuously reads frames from shared memory, runs optimized weapon detection,
    and outputs alerts to the output_queue when a weapon is detected.
    """
    from multiprocessing import shared_memory
    import os
    
    shm = shared_memory.SharedMemory(name=shm_name)
    frame_buffer = np.ndarray(shape, dtype=np.uint8, buffer=shm.buf)
    
    # Initialize the weapon detector. It falls back to yolov8n.pt if best.pt is not found.
    model_path = os.getenv("YOLO_MODEL_PATH", "../../data/models/best.pt")
    detector = ImprovedWeaponDetector(model_path=model_path)
    
    print(f"[INFO] Weapon detection started for Camera {cam_id}...")
    
    while True:
        time.sleep(0.05)  # Moderate delay to balance cpu usage
        
        with lock:
            frame = np.copy(frame_buffer)
            
        if frame is None or frame.size == 0 or np.all(frame == 0):
            continue
            
        # Convert color space from RGB to BGR for OpenCV
        try:
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"[ERROR] Weapon detection: Failed to convert color space: {e}")
            continue
            
        # Save temp image for ImprovedWeaponDetector since it expects image path
        os.makedirs("temp_frames", exist_ok=True)
        temp_img_path = f"temp_frames/weapon_detect_cam{cam_id}.jpg"
        cv2.imwrite(temp_img_path, frame_bgr)
        
        try:
            # Run detection
            detections = detector.detect_weapons_optimized(temp_img_path)
            
            if detections:
                # Map weapon detection alerts to the general object alerts format
                mapped_detections = []
                for det in detections:
                    # Weapon classes usually include knife, gun, handgun, rifle, sword, heavy-weapon
                    mapped_detections.append({
                        "label": det['class_name'],
                        "confidence": det['confidence'],
                        "bbox": [int(c) for c in det['bbox']]
                    })
                
                # Push detection alert
                output_queue.put({
                    "cam_id": cam_id,
                    "detections": mapped_detections,
                    "severity": "critical",
                    "detection_type": "weapon"
                })
                
                # Save threat frame
                threat_dir = os.path.join("data", "alerts", "weapon_alerts")
                os.makedirs(threat_dir, exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"weapon_cam{cam_id}_{timestamp}.jpg"
                save_path = os.path.join(threat_dir, filename)
                
                # Draw boxes for the local saved frame
                for det in detections:
                    x1, y1, x2, y2 = [int(c) for c in det['bbox']]
                    cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame_bgr, f"WEAPON: {det['class_name']} ({det['confidence']:.2f})", 
                                (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                                
                cv2.imwrite(save_path, frame_bgr)
                print(f"[ALERT] Weapon detected on Camera {cam_id}! Snapshot saved to {save_path}")
                
        except Exception as e:
            print(f"[ERROR] Weapon detection failed on Camera {cam_id}: {e}")
            
        finally:
            if os.path.exists(temp_img_path):
                try:
                    os.remove(temp_img_path)
                except OSError:
                    pass

def main():
    """Main function to demonstrate optimized weapon detection"""
    
    print("🎯 OPTIMIZED WEAPON DETECTION")
    print("="*40)
    print("Using improved parameters for better accuracy")
    print()
    
    # Initialize detector
    detector = ImprovedWeaponDetector("../../data/models/best.pt")
    
    # Test images directory
    test_dir = "../../data/datasets/test_images/weapon-detection.v4i.yolov5pytorch/train/images"
    
    if not Path(test_dir).exists():
        print(f"❌ Test directory not found: {test_dir}")
        return
    
    # Run batch test
    print("1️⃣ Running batch test with optimized parameters...")
    results = detector.batch_test_optimized(test_dir, max_images=30)
    
    # Create sample detections
    print("\n2️⃣ Creating detection samples...")
    sample_images = list(Path(test_dir).glob("*.jpg"))[:5]
    
    for i, img_path in enumerate(sample_images, 1):
        output_name = f"optimized_sample_{i}.jpg"
        detections = detector.create_detection_sample(str(img_path), output_name)
        print(f"   Sample {i}: {len(detections)} weapons detected")
    
    # Provide improvement summary
    print(f"\n🎉 ACCURACY IMPROVEMENTS APPLIED:")
    print("="*40)
    print("✅ Lowered confidence threshold: 0.5 → 0.3")
    print("✅ Added smart filtering for false positives")
    print("✅ Class-specific confidence thresholds")
    print("✅ Area-based filtering")
    print("✅ Improved post-processing")
    
    print(f"\n📈 Expected Results:")
    print(f"   Detection rate: {results['detection_rate']:.1f}% (vs previous lower rate)")
    print(f"   Avg confidence: {results['avg_confidence']:.3f}")
    print(f"   Processing speed: {results['avg_processing_time']:.3f}s per image")
    
  
    
    print(f"\n📁 Files created:")
    print("   - optimized_sample_*.jpg (detection examples)")
    print("   - This script can be integrated into your main system")

if __name__ == "__main__":
    main()
