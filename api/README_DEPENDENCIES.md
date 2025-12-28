# Dependency Conflicts Resolution

## Issue

When installing requirements, you may see dependency conflicts with packages in your base conda environment (like `numba`, `jupyter-server`, `spyder`, etc.). These are not directly related to this project.

## Solution

### Option 1: Use a Virtual Environment (Recommended)

Create an isolated environment for this project:

```bash
# Create a new virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install requirements
pip install -r api/requirements.txt
```

### Option 2: Adjust Base Environment

If you need to use the base environment, the main conflicts are:

1. **numpy**: Changed to `>=1.21,<1.25` to be compatible with `numba`
2. **anyio**: Set to `>=3.1.0,<5.0.0` to work with both FastAPI and jupyter-server
3. **pydantic**: Set to `>=2.0.0` to allow newer versions

### Option 3: Ignore Warnings (Not Recommended)

The dependency resolver warnings are informational. If the packages work at runtime, you can proceed, but this may cause issues later.

## Key Dependencies for CV Service

- **ultralytics**: YOLOv8 model framework
- **opencv-python**: Image processing
- **numpy**: Numerical operations (constrained to <1.25 for numba compatibility)

## Testing

After installation, test that everything works:

```python
from api.cv_service import ChipCVService
import cv2
import numpy as np

# Should import without errors
service = ChipCVService()
print("CV service initialized successfully!")
```

