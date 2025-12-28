# CV Service Setup Guide

## Overview

The CV service uses YOLOv8-seg (segmentation) to detect and count poker chips from images. It identifies individual chips, clusters them into stacks, counts chips by detecting seams between stacked chips, and classifies them by color/denomination.

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

This will install:
- `ultralytics` - YOLOv8 model framework
- `opencv-python` - Image processing
- `numpy` - Numerical operations

## Using a Custom Trained Model

The default implementation uses a pretrained YOLOv8 model, which **will not detect poker chips** (it's trained on COCO dataset). For production use, you need to train a custom YOLOv8-seg model on poker chip data.

### Training a Custom Model

1. **Collect training data**: Take photos of poker chips in various configurations
2. **Label data**: Use tools like [Label Studio](https://labelstud.io/) or [Roboflow](https://roboflow.com/) to create segmentation masks
3. **Train model**: Use Ultralytics to train YOLOv8-seg on your labeled data
4. **Use custom model**: Pass the model path when initializing the service

Example:
```python
from api.cv_service import ChipCVService

service = ChipCVService(
    model_path="path/to/your/custom_chip_model.pt",
    denomination_config={
        "red": 500,
        "blue": 1000,
        "green": 2500,
        "black": 5000,
    }
)
```

## Configuration

### Chip Denominations

Default denominations (in cents):
- Red: 500
- Blue: 1000
- Green: 2500
- Black: 5000

You can customize these by passing a `denomination_config` dict to `ChipCVService()`.

### Color Detection

The service uses HSV color ranges to classify chips. You may need to adjust the `color_ranges` in `cv_service.py` based on your actual chip colors.

## How It Works

1. **Detection**: YOLOv8-seg detects chip regions and creates segmentation masks
2. **Clustering**: Detected chips are clustered into stacks based on spatial proximity
3. **Counting**: Seams between stacked chips are detected using edge detection to count chips per stack
4. **Classification**: Each stack is classified by dominant color using HSV color analysis
5. **Totals**: Counts are multiplied by denomination values and summed

## Fallback Detection

If YOLOv8 doesn't detect any chips, the service falls back to traditional CV methods (HoughCircles) to find circular objects. This is less accurate but provides a baseline.

## Testing

Test the service with a sample image:

```python
from api.cv_service import process_chip_image

result = process_chip_image("path/to/chip_image.jpg")
print(result)
```

Expected output:
```json
{
  "total_cents": 5000,
  "breakdown": {
    "denom_500": 10
  },
  "meta": {
    "model": "yolov8-seg",
    "confidence": 0.85,
    "notes": "Detected 10 chip regions, 2 stacks"
  }
}
```

