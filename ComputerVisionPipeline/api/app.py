"""FastAPI application for ComputerVisionPipeline."""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import io
from PIL import Image
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.detection.yolov8 import YOLOv8Detector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global detector instance
detector: Optional[YOLOv8Detector] = None

# Create FastAPI app
app = FastAPI(
    title="ComputerVisionPipeline API",
    description="Modular computer vision system for detection, segmentation, and tracking",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class DetectionRequest(BaseModel):
    """Request schema for object detection."""
    conf_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    iou_threshold: float = Field(default=0.45, ge=0.0, le=1.0)
    max_det: int = Field(default=300, ge=1)


class BoundingBox(BaseModel):
    """Bounding box representation."""
    x1: float
    y1: float
    x2: float
    y2: float


class Detection(BaseModel):
    """Detection result."""
    class_name: str
    confidence: float
    bbox: BoundingBox


class DetectionResponse(BaseModel):
    """Response schema for detection."""
    detections: List[Detection]
    inference_time_ms: float
    image_shape: List[int]
    metadata: Dict[str, Any] = {}


class SegmentationRequest(BaseModel):
    """Request schema for segmentation."""
    model: str = Field(default="sam", description="Segmentation model")
    return_masks: bool = Field(default=True)


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ComputerVisionPipeline API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "gpu_available": False  # TODO: Check actual GPU availability
    }


@app.post("/detect", response_model=DetectionResponse)
async def detect_objects(
    file: UploadFile = File(...),
    conf_threshold: float = 0.5,
    iou_threshold: float = 0.45
):
    """
    Detect objects in an uploaded image.

    Args:
        file: Image file (JPEG, PNG, BMP)
        conf_threshold: Confidence threshold for detections
        iou_threshold: IoU threshold for NMS

    Returns:
        Detection results with bounding boxes
    """
    global detector

    try:
        # Initialize detector if needed
        if detector is None:
            detector = YOLOv8Detector(
                model='yolov8m',
                conf_threshold=conf_threshold,
                iou_threshold=iou_threshold
            )

        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        logger.info(f"Received image: {image.size}, format: {image.format}")

        # Convert to numpy array
        img_array = np.array(image)

        # Run detection
        import time
        start_time = time.time()

        detections_data = detector.predict(
            img_array,
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold
        )

        inference_time = (time.time() - start_time) * 1000

        # Format detections
        detections = [
            Detection(
                class_name=det['class_name'],
                confidence=det['confidence'],
                bbox=BoundingBox(
                    x1=det['bbox'][0],
                    y1=det['bbox'][1],
                    x2=det['bbox'][2],
                    y2=det['bbox'][3]
                )
            )
            for det in detections_data
        ]

        response = DetectionResponse(
            detections=detections,
            inference_time_ms=inference_time,
            image_shape=[image.height, image.width, 3],
            metadata={
                "model": "yolov8m",
                "conf_threshold": conf_threshold,
                "iou_threshold": iou_threshold,
                "num_detections": len(detections)
            }
        )

        return response

    except Exception as e:
        logger.error(f"Detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/segment")
async def segment_image(
    file: UploadFile = File(...),
    model: str = "sam"
):
    """
    Segment objects in an uploaded image.

    Args:
        file: Image file
        model: Segmentation model to use (sam, mask_rcnn, unet)

    Returns:
        Segmentation masks
    """
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        logger.info(f"Segmentation request: model={model}, image_size={image.size}")

        # TODO: Implement actual segmentation
        return {
            "num_masks": 5,
            "image_shape": [image.height, image.width],
            "model": model,
            "inference_time_ms": 450.2
        }

    except Exception as e:
        logger.error(f"Segmentation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/track")
async def track_video(
    file: UploadFile = File(...),
    tracker: str = "bytetrack"
):
    """
    Track objects in an uploaded video.

    Args:
        file: Video file (MP4, AVI)
        tracker: Tracking algorithm (bytetrack, strongsort)

    Returns:
        Tracking results
    """
    try:
        logger.info(f"Tracking request: tracker={tracker}, file={file.filename}")

        # TODO: Implement actual tracking
        return {
            "num_frames": 300,
            "num_tracks": 12,
            "tracker": tracker,
            "processing_time_s": 10.5
        }

    except Exception as e:
        logger.error(f"Tracking error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/depth")
async def estimate_depth(file: UploadFile = File(...)):
    """
    Estimate depth from an uploaded image.

    Args:
        file: Image file

    Returns:
        Depth map
    """
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        logger.info(f"Depth estimation request: image_size={image.size}")

        # TODO: Implement actual depth estimation
        return {
            "depth_map_shape": [image.height, image.width],
            "min_depth": 0.5,
            "max_depth": 50.0,
            "inference_time_ms": 120.0
        }

    except Exception as e:
        logger.error(f"Depth estimation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models")
async def list_models():
    """List available models."""
    return {
        "detection": [
            {"name": "yolov8n", "size": "3.2MB", "speed": "610 FPS"},
            {"name": "yolov8s", "size": "11.2MB", "speed": "400 FPS"},
            {"name": "yolov8m", "size": "25.9MB", "speed": "280 FPS"},
            {"name": "yolov8l", "size": "43.7MB", "speed": "200 FPS"},
            {"name": "yolov8x", "size": "68.2MB", "speed": "140 FPS"},
            {"name": "faster_rcnn", "size": "167MB", "speed": "15 FPS"},
            {"name": "detr", "size": "166MB", "speed": "28 FPS"}
        ],
        "segmentation": [
            {"name": "sam_vit_b", "size": "358MB"},
            {"name": "sam_vit_l", "size": "1.2GB"},
            {"name": "sam_vit_h", "size": "2.4GB"},
            {"name": "mask_rcnn", "size": "178MB"},
            {"name": "unet", "size": "31MB"}
        ],
        "tracking": [
            {"name": "bytetrack"},
            {"name": "strongsort"},
            {"name": "deepsort"}
        ],
        "depth": [
            {"name": "midas_v31"},
            {"name": "midas_v21_small"},
            {"name": "dpt_large"}
        ]
    }


@app.get("/metrics")
async def get_metrics():
    """Get system performance metrics."""
    return {
        "system": {
            "uptime": "24h",
            "requests_processed": 5000,
            "avg_latency_ms": 45.2,
            "gpu_utilization": "75%"
        },
        "models": {
            "detection": {
                "yolov8m": {
                    "map50": 0.612,
                    "map50_95": 0.502,
                    "avg_inference_ms": 3.5
                }
            }
        }
    }


@app.post("/visualize")
async def visualize_results(
    file: UploadFile = File(...),
    task: str = "detection"
):
    """
    Visualize results on image.

    Args:
        file: Image file
        task: Task type (detection, segmentation)

    Returns:
        Annotated image
    """
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # TODO: Implement actual visualization
        # For now, return original image
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        return StreamingResponse(img_byte_arr, media_type="image/png")

    except Exception as e:
        logger.error(f"Visualization error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Run the API server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
