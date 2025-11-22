"""Data loading utilities for computer vision tasks."""

import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Union
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ImageDataLoader:
    """
    Load and prepare image data for computer vision tasks.

    Supports multiple annotation formats including COCO, Pascal VOC, and YOLO.
    """

    def __init__(self, data_dir: Union[str, Path] = "data/raw"):
        """
        Initialize data loader.

        Args:
            data_dir: Directory containing image data
        """
        self.data_dir = Path(data_dir)
        logger.info(f"Initialized ImageDataLoader with data_dir: {self.data_dir}")

    def load_coco_annotations(
        self,
        annotation_file: str,
        image_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load COCO format annotations.

        Args:
            annotation_file: Path to COCO JSON file
            image_dir: Directory containing images

        Returns:
            COCO annotations dictionary
        """
        ann_path = Path(annotation_file)
        logger.info(f"Loading COCO annotations from {ann_path}")

        with open(ann_path, 'r') as f:
            coco_data = json.load(f)

        logger.info(f"Loaded {len(coco_data.get('images', []))} images")
        logger.info(f"Loaded {len(coco_data.get('annotations', []))} annotations")
        logger.info(f"Categories: {len(coco_data.get('categories', []))}")

        return coco_data

    def load_image(
        self,
        image_path: Union[str, Path],
        size: Optional[Tuple[int, int]] = None,
        mode: str = 'RGB'
    ) -> np.ndarray:
        """
        Load and preprocess image.

        Args:
            image_path: Path to image file
            size: Optional target size (width, height)
            mode: Color mode (RGB, L, etc.)

        Returns:
            Image as numpy array
        """
        img_path = Path(image_path)

        if not img_path.exists():
            raise FileNotFoundError(f"Image not found: {img_path}")

        # Load image
        image = Image.open(img_path).convert(mode)

        # Resize if specified
        if size is not None:
            image = image.resize(size, Image.LANCZOS)

        # Convert to numpy array
        img_array = np.array(image)

        logger.debug(f"Loaded image: {img_path.name}, shape: {img_array.shape}")

        return img_array

    def load_batch(
        self,
        image_paths: List[Union[str, Path]],
        size: Optional[Tuple[int, int]] = None,
        mode: str = 'RGB'
    ) -> np.ndarray:
        """
        Load multiple images as batch.

        Args:
            image_paths: List of image paths
            size: Optional target size
            mode: Color mode

        Returns:
            Batch of images as numpy array
        """
        logger.info(f"Loading batch of {len(image_paths)} images")

        images = []
        for img_path in image_paths:
            img = self.load_image(img_path, size=size, mode=mode)
            images.append(img)

        batch = np.stack(images, axis=0)
        logger.info(f"Batch shape: {batch.shape}")

        return batch

    def parse_yolo_annotation(
        self,
        annotation_file: str,
        image_shape: Tuple[int, int]
    ) -> List[Dict[str, Any]]:
        """
        Parse YOLO format annotation file.

        Format: class_id center_x center_y width height (normalized 0-1)

        Args:
            annotation_file: Path to YOLO txt file
            image_shape: (height, width) of image

        Returns:
            List of annotation dictionaries
        """
        ann_path = Path(annotation_file)

        if not ann_path.exists():
            return []

        annotations = []
        img_h, img_w = image_shape

        with open(ann_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 5:
                    continue

                class_id = int(parts[0])
                center_x = float(parts[1]) * img_w
                center_y = float(parts[2]) * img_h
                width = float(parts[3]) * img_w
                height = float(parts[4]) * img_h

                # Convert to x1, y1, x2, y2
                x1 = center_x - width / 2
                y1 = center_y - height / 2
                x2 = center_x + width / 2
                y2 = center_y + height / 2

                annotations.append({
                    'class_id': class_id,
                    'bbox': [x1, y1, x2, y2],
                    'center': [center_x, center_y],
                    'size': [width, height]
                })

        return annotations

    def save_coco_format(
        self,
        output_file: str,
        images: List[Dict[str, Any]],
        annotations: List[Dict[str, Any]],
        categories: List[Dict[str, Any]]
    ):
        """
        Save annotations in COCO format.

        Args:
            output_file: Output JSON file path
            images: List of image info dictionaries
            annotations: List of annotation dictionaries
            categories: List of category dictionaries
        """
        output_path = Path(output_file)
        logger.info(f"Saving COCO format to {output_path}")

        coco_data = {
            'images': images,
            'annotations': annotations,
            'categories': categories
        }

        with open(output_path, 'w') as f:
            json.dump(coco_data, f, indent=2)

        logger.info(f"Saved {len(images)} images, {len(annotations)} annotations")

    def convert_bbox_format(
        self,
        bbox: List[float],
        from_format: str,
        to_format: str,
        image_shape: Optional[Tuple[int, int]] = None
    ) -> List[float]:
        """
        Convert bbox between different formats.

        Args:
            bbox: Bounding box coordinates
            from_format: Source format (xyxy, xywh, coco, yolo)
            to_format: Target format
            image_shape: (height, width) for yolo format

        Returns:
            Converted bbox
        """
        # TODO: Implement format conversion
        # xyxy: [x1, y1, x2, y2]
        # xywh: [x, y, w, h]
        # coco: [x, y, w, h]
        # yolo: [center_x, center_y, w, h] (normalized)

        return bbox

    def get_dataset_statistics(
        self,
        coco_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute statistics for a COCO dataset.

        Args:
            coco_data: COCO format annotations

        Returns:
            Dictionary of statistics
        """
        num_images = len(coco_data.get('images', []))
        num_annotations = len(coco_data.get('annotations', []))
        num_categories = len(coco_data.get('categories', []))

        # Count annotations per category
        category_counts = {}
        for ann in coco_data.get('annotations', []):
            cat_id = ann['category_id']
            category_counts[cat_id] = category_counts.get(cat_id, 0) + 1

        stats = {
            'num_images': num_images,
            'num_annotations': num_annotations,
            'num_categories': num_categories,
            'avg_annotations_per_image': num_annotations / num_images if num_images > 0 else 0,
            'category_distribution': category_counts
        }

        logger.info(f"Dataset statistics: {stats}")

        return stats


class VideoDataLoader:
    """Load and process video data."""

    def __init__(self):
        """Initialize video data loader."""
        logger.info("Initialized VideoDataLoader")

    def load_video(
        self,
        video_path: Union[str, Path],
        start_frame: int = 0,
        end_frame: Optional[int] = None,
        skip_frames: int = 0
    ):
        """
        Load video frames.

        Args:
            video_path: Path to video file
            start_frame: Starting frame number
            end_frame: Ending frame number (None for all)
            skip_frames: Number of frames to skip

        Yields:
            Video frames as numpy arrays
        """
        # TODO: Implement video loading with opencv
        logger.info(f"Loading video from {video_path}")
        pass

    def save_video(
        self,
        frames: List[np.ndarray],
        output_path: Union[str, Path],
        fps: int = 30,
        codec: str = 'mp4v'
    ):
        """
        Save frames as video file.

        Args:
            frames: List of frames
            output_path: Output video path
            fps: Frames per second
            codec: Video codec
        """
        # TODO: Implement video saving
        logger.info(f"Saving video to {output_path}")
        pass


def main():
    """Example usage of data loaders."""
    loader = ImageDataLoader()

    # Load COCO annotations
    # coco_data = loader.load_coco_annotations('annotations.json')

    # Load single image
    # image = loader.load_image('image.jpg', size=(640, 640))

    # Get dataset statistics
    # stats = loader.get_dataset_statistics(coco_data)


if __name__ == "__main__":
    main()
