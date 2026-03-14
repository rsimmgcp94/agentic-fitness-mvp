from typing import Any
from functools import lru_cache


@lru_cache(maxsize=1)
def get_pose_model():
    """
    Initializes and returns a cached MediaPipe Pose instance.
    Caching the model instance avoids repeated initialization overhead.
    """
    # Lazy import to prevent startup crashes/timeouts
    from mediapipe.python.solutions import pose as mp_pose

    return mp_pose.Pose(
        static_image_mode=True,
        model_complexity=2,
        enable_segmentation=True,
        min_detection_confidence=0.5
    )


def analyze_pose(image_path: str) -> dict:
    """
    Runs MediaPipe Pose detection on a local image file.
    Returns a dictionary containing detection status and landmarks.
    """
    import cv2

    pose = get_pose_model()
    image = cv2.imread(image_path)
    if image is None:
        return {"error": "Could not read image"}

    # Convert BGR to RGB (MediaPipe expects RGB)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # We do NOT use 'with pose' here because the Pose instance
    # is cached and should not be closed.
    results: Any = pose.process(image_rgb)

    if not results.pose_landmarks:
        return {"detected": False}

    # Extract landmarks
    landmarks = []
    for lm in results.pose_landmarks.landmark:
        landmarks.append({
            "x": lm.x,
            "y": lm.y,
            "z": lm.z,
            "visibility": lm.visibility
        })
        
    return {
        "detected": True,
        "landmarks": landmarks
    }
