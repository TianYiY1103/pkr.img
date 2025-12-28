"""
CV Service for Poker Chip Detection and Counting

Uses YOLOv8-seg to detect chips, identify seams between stacked chips,
and classify by denomination based on color.
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
import numpy as np
import cv2
from ultralytics import YOLO
from collections import defaultdict


class ChipCVService:
    """Service for detecting and counting poker chips from images."""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        denomination_config: Optional[Dict[str, int]] = None,
        confidence_threshold: float = 0.25,
    ):
        """
        Initialize the CV service.
        
        Args:
            model_path: Path to custom YOLOv8-seg model. If None, uses pretrained.
            denomination_config: Dict mapping color names to cent values.
                                Default: {"red": 500, "blue": 1000, "green": 2500, "black": 5000}
            confidence_threshold: Minimum confidence for detections.
        """
        # Load YOLOv8-seg model
        if model_path and Path(model_path).exists():
            self.model = YOLO(model_path)
        else:
            # Use pretrained YOLOv8-seg model (will download on first use)
            # For production, you'd train a custom model on chip data
            self.model = YOLO("yolov8n-seg.pt")
        
        self.confidence_threshold = confidence_threshold
        
        # Default denomination mapping (cents per chip)
        self.denomination_config = denomination_config or {
            "red": 500,
            "blue": 1000,
            "green": 2500,
            "black": 5000,
        }
        
        # Color detection thresholds (HSV ranges for common chip colors)
        # These will need calibration based on your actual chip colors
        self.color_ranges = {
            "red": [
                (np.array([0, 50, 50]), np.array([10, 255, 255])),
                (np.array([170, 50, 50]), np.array([180, 255, 255])),
            ],
            "blue": [(np.array([100, 50, 50]), np.array([130, 255, 255]))],
            "green": [(np.array([40, 50, 50]), np.array([80, 255, 255]))],
            "black": [(np.array([0, 0, 0]), np.array([180, 255, 50]))],
        }
    
    def detect_chips(self, image_path: str) -> Dict:
        """
        Main entry point: detect and count chips in an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict with total_cents, breakdown, and meta fields
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Read image
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Run YOLOv8-seg detection
        # NOTE: The pretrained YOLOv8 model won't detect poker chips.
        # For production use, train a custom YOLOv8-seg model on poker chip data.
        # You can pass model_path to ChipCVService() to use a custom model.
        results = self.model(str(image_path), conf=self.confidence_threshold)
        
        result = results[0] if len(results) > 0 else None
        masks = result.masks.data.cpu().numpy() if result and result.masks is not None else None
        
        # Fallback to traditional CV if YOLOv8 doesn't detect anything
        if masks is None or len(masks) == 0:
            return self._fallback_detection(img, image_path)
        
        # Process each detected chip region
        chip_regions = []
        for i, mask in enumerate(masks):
            # Get bounding box and mask
            box = result.boxes.xyxy[i].cpu().numpy()
            conf = float(result.boxes.conf[i].cpu().numpy())
            
            # Resize mask to image size
            h, w = img.shape[:2]
            mask_resized = cv2.resize(mask.astype(np.uint8), (w, h))
            mask_binary = (mask_resized > 0.5).astype(np.uint8)
            
            # Extract chip region
            x1, y1, x2, y2 = map(int, box)
            chip_region = img[y1:y2, x1:x2]
            mask_region = mask_binary[y1:y2, x1:x2]
            
            if chip_region.size == 0:
                continue
            
            chip_regions.append({
                "box": (x1, y1, x2, y2),
                "mask": mask_binary,
                "region": chip_region,
                "mask_region": mask_region,
                "confidence": conf,
            })
        
        # Cluster chips into stacks and count
        stacks = self._cluster_into_stacks(chip_regions, img.shape)
        
        # Count chips per stack by analyzing seams
        stack_counts = []
        for stack in stacks:
            count = self._count_chips_in_stack(stack, img)
            stack_counts.append({
                "count": count,
                "stack": stack,
            })
        
        # Classify chips by color
        breakdown = defaultdict(int)
        total_cents = 0
        
        for stack_info in stack_counts:
            count = stack_info["count"]
            stack = stack_info["stack"]
            
            # Classify the stack by dominant color
            color = self._classify_chip_color(stack, img)
            denomination = self.denomination_config.get(color, 0)
            
            chip_key = f"denom_{denomination}" if denomination > 0 else f"color_{color}"
            breakdown[chip_key] += count
            total_cents += count * denomination
        
        # Calculate average confidence
        avg_confidence = np.mean([r["confidence"] for r in chip_regions]) if chip_regions else 0.0
        
        return {
            "total_cents": int(total_cents),
            "breakdown": dict(breakdown),
            "meta": {
                "model": "yolov8-seg",
                "confidence": float(avg_confidence),
                "notes": f"Detected {len(chip_regions)} chip regions, {len(stacks)} stacks",
            },
        }
    
    def _cluster_into_stacks(
        self, chip_regions: List[Dict], image_shape: Tuple[int, int]
    ) -> List[List[Dict]]:
        """
        Cluster detected chips into stacks based on spatial proximity.
        
        Args:
            chip_regions: List of chip detection dicts
            image_shape: (height, width) of the image
            
        Returns:
            List of stacks, where each stack is a list of chip regions
        """
        if not chip_regions:
            return []
        
        # Simple clustering: chips with overlapping or nearby bounding boxes
        stacks = []
        used = set()
        
        for i, chip in enumerate(chip_regions):
            if i in used:
                continue
            
            stack = [chip]
            used.add(i)
            x1, y1, x2, y2 = chip["box"]
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            
            # Find nearby chips (within threshold distance)
            threshold = max(x2 - x1, y2 - y1) * 1.5
            
            for j, other_chip in enumerate(chip_regions):
                if j in used or j == i:
                    continue
                
                ox1, oy1, ox2, oy2 = other_chip["box"]
                other_center_x = (ox1 + ox2) / 2
                other_center_y = (oy1 + oy2) / 2
                
                distance = np.sqrt(
                    (center_x - other_center_x) ** 2 + (center_y - other_center_y) ** 2
                )
                
                # Check if boxes overlap or are very close
                overlap = not (
                    x2 < ox1 or ox2 < x1 or y2 < oy1 or oy2 < y1
                )
                
                if overlap or distance < threshold:
                    stack.append(other_chip)
                    used.add(j)
            
            stacks.append(stack)
        
        return stacks
    
    def _count_chips_in_stack(self, stack: List[Dict], img: np.ndarray) -> int:
        """
        Count chips in a stack by detecting seams between stacked chips.
        
        Strategy:
        1. Get the combined mask/region for the stack
        2. Analyze vertical edges (seams) in the stack region
        3. Count distinct horizontal bands separated by seams
        
        Args:
            stack: List of chip regions in the stack
            img: Full image array
            
        Returns:
            Estimated number of chips in the stack
        """
        if not stack:
            return 0
        
        # Combine all masks in the stack
        combined_mask = np.zeros(img.shape[:2], dtype=np.uint8)
        stack_boxes = []
        
        for chip in stack:
            mask = chip["mask"]
            combined_mask = cv2.bitwise_or(combined_mask, mask)
            stack_boxes.append(chip["box"])
        
        # Get bounding box of entire stack
        all_x = [b[0] for b in stack_boxes] + [b[2] for b in stack_boxes]
        all_y = [b[1] for b in stack_boxes] + [b[3] for b in stack_boxes]
        stack_x1, stack_y1 = int(min(all_x)), int(min(all_y))
        stack_x2, stack_y2 = int(max(all_x)), int(max(all_y))
        
        # Extract stack region
        stack_region = img[stack_y1:stack_y2, stack_x1:stack_x2]
        stack_mask = combined_mask[stack_y1:stack_y2, stack_x1:stack_x2]
        
        if stack_region.size == 0:
            return len(stack)  # Fallback: one chip per detection
        
        # Convert to grayscale for edge detection
        gray = cv2.cvtColor(stack_region, cv2.COLOR_BGR2GRAY)
        
        # Apply mask to focus on chip area
        gray_masked = cv2.bitwise_and(gray, gray, mask=stack_mask)
        
        # Detect horizontal edges (seams between stacked chips)
        # Use Sobel to find horizontal edges
        sobel_x = cv2.Sobel(gray_masked, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray_masked, cv2.CV_64F, 0, 1, ksize=3)
        
        # Focus on horizontal edges (strong vertical gradients)
        # Horizontal seams have vertical gradients, so use sobel_y
        horizontal_edges = np.abs(sobel_y)
        
        # Project horizontal edges vertically to find seam locations
        # Sum horizontal edges across columns (axis=1) to get vertical projection
        # This gives us edge strength per row, indicating where seams are located vertically
        edge_projection = np.sum(horizontal_edges, axis=1)
        
        # Find peaks in the projection (indicating seams)
        # Use a threshold relative to the max
        if edge_projection.max() > 0:
            threshold = edge_projection.max() * 0.3
            peaks = edge_projection > threshold
        else:
            peaks = np.zeros_like(edge_projection, dtype=bool)
        
        # Count distinct bands (regions between seams)
        # Simple approach: count transitions
        peak_count = np.sum(peaks)
        
        # Estimate chip count: typically seams = chips - 1
        # But we also consider the height of the stack
        stack_height = stack_y2 - stack_y1
        
        # If we have strong seam detection, use that
        if peak_count > 0:
            # Number of chips ≈ number of distinct bands
            # Bands are separated by peaks, so chips ≈ peaks + 1 (roughly)
            estimated_count = max(1, int(peak_count * 0.5) + 1)
        else:
            # Fallback: estimate based on stack height
            # Assume average chip thickness ~15-20 pixels (calibrate based on your images)
            avg_chip_thickness = 18
            estimated_count = max(1, int(stack_height / avg_chip_thickness))
        
        # Clamp to reasonable range (at least 1, at most reasonable max)
        estimated_count = max(1, min(estimated_count, 50))
        
        return estimated_count
    
    def _classify_chip_color(self, stack: List[Dict], img: np.ndarray) -> str:
        """
        Classify chip color by analyzing the dominant color in the stack region.
        
        Args:
            stack: List of chip regions in the stack
            img: Full image array
            
        Returns:
            Color name string (e.g., "red", "blue", "green", "black")
        """
        if not stack:
            return "unknown"
        
        # Get the first chip's region as representative
        chip = stack[0]
        x1, y1, x2, y2 = chip["box"]
        mask_region = chip["mask_region"]
        chip_region = chip["region"]
        
        if chip_region.size == 0:
            return "unknown"
        
        # Convert to HSV for color analysis
        hsv = cv2.cvtColor(chip_region, cv2.COLOR_BGR2HSV)
        
        # Apply mask to focus on chip pixels
        masked_hsv = cv2.bitwise_and(hsv, hsv, mask=mask_region)
        
        # Get non-zero pixels (chip pixels)
        mask_bool = mask_region > 0
        if not np.any(mask_bool):
            return "unknown"
        
        hsv_pixels = masked_hsv[mask_bool]
        
        # Calculate mean HSV values
        mean_h = np.mean(hsv_pixels[:, 0])
        mean_s = np.mean(hsv_pixels[:, 1])
        mean_v = np.mean(hsv_pixels[:, 2])
        
        # Classify based on HSV ranges
        best_match = "unknown"
        best_score = 0
        
        for color_name, ranges in self.color_ranges.items():
            score = 0
            for (lower, upper) in ranges:
                # Check if mean HSV falls within range
                if (
                    (lower[0] <= mean_h <= upper[0] or 
                     (lower[0] > upper[0] and (mean_h >= lower[0] or mean_h <= upper[0])))
                    and lower[1] <= mean_s <= upper[1]
                    and lower[2] <= mean_v <= upper[2]
                ):
                    score = 1.0
                    break
                else:
                    # Calculate distance from range (closer = better)
                    h_dist = min(
                        abs(mean_h - lower[0]),
                        abs(mean_h - upper[0]),
                        abs(mean_h - (lower[0] + 180) % 180),
                        abs(mean_h - (upper[0] + 180) % 180),
                    )
                    s_dist = min(abs(mean_s - lower[1]), abs(mean_s - upper[1]))
                    v_dist = min(abs(mean_v - lower[2]), abs(mean_v - upper[2]))
                    
                    # Normalize distances (rough heuristic)
                    normalized_score = 1.0 / (1.0 + (h_dist / 10.0) + (s_dist / 50.0) + (v_dist / 50.0))
                    score = max(score, normalized_score)
            
            if score > best_score:
                best_score = score
                best_match = color_name
        
        return best_match
    
    def _fallback_detection(self, img: np.ndarray, image_path: Path) -> Dict:
        """
        Fallback detection method using traditional CV when YOLOv8 doesn't detect chips.
        Uses HoughCircles and contour detection to find circular chip-like objects.
        
        This is a basic fallback - for best results, train a custom YOLOv8-seg model.
        """
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # Detect circles using HoughCircles
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=30,
            param1=50,
            param2=30,
            minRadius=20,
            maxRadius=100,
        )
        
        if circles is None:
            return {
                "total_cents": 0,
                "breakdown": {},
                "meta": {
                    "model": "fallback-cv",
                    "confidence": 0.0,
                    "notes": "No chips detected with fallback method. Consider training a custom YOLOv8-seg model.",
                },
            }
        
        circles = np.uint16(np.around(circles))
        
        # Convert circles to chip regions format
        chip_regions = []
        for i, (x, y, r) in enumerate(circles[0, :]):
            # Create bounding box
            x1, y1 = max(0, int(x - r)), max(0, int(y - r))
            x2, y2 = min(img.shape[1], int(x + r)), min(img.shape[0], int(y + r))
            
            # Create circular mask
            mask = np.zeros(img.shape[:2], dtype=np.uint8)
            cv2.circle(mask, (int(x), int(y)), int(r), 255, -1)
            
            chip_region = img[y1:y2, x1:x2]
            mask_region = mask[y1:y2, x1:x2]
            
            chip_regions.append({
                "box": (x1, y1, x2, y2),
                "mask": mask,
                "region": chip_region,
                "mask_region": mask_region,
                "confidence": 0.5,  # Lower confidence for fallback
            })
        
        # Cluster into stacks
        stacks = self._cluster_into_stacks(chip_regions, img.shape)
        
        # Count chips per stack
        stack_counts = []
        for stack in stacks:
            count = self._count_chips_in_stack(stack, img)
            stack_counts.append({
                "count": count,
                "stack": stack,
            })
        
        # Classify by color
        breakdown = defaultdict(int)
        total_cents = 0
        
        for stack_info in stack_counts:
            count = stack_info["count"]
            stack = stack_info["stack"]
            
            color = self._classify_chip_color(stack, img)
            denomination = self.denomination_config.get(color, 0)
            
            chip_key = f"denom_{denomination}" if denomination > 0 else f"color_{color}"
            breakdown[chip_key] += count
            total_cents += count * denomination
        
        return {
            "total_cents": int(total_cents),
            "breakdown": dict(breakdown),
            "meta": {
                "model": "fallback-cv",
                "confidence": 0.5,
                "notes": f"Fallback detection: {len(chip_regions)} chip regions, {len(stacks)} stacks. For better results, train a custom YOLOv8-seg model.",
            },
        }


# Global service instance (lazy-loaded)
_service_instance: Optional[ChipCVService] = None


def get_cv_service() -> ChipCVService:
    """Get or create the global CV service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ChipCVService()
    return _service_instance


def process_chip_image(image_path: str) -> Dict:
    """
    Convenience function to process a chip image.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dict with total_cents, breakdown, and meta fields
    """
    service = get_cv_service()
    return service.detect_chips(image_path)

