import cv2
import numpy as np
from log import setup_logger

logger = setup_logger()

def open_camera(camera_index=0):
    """
    Function to open and capture video from USB camera
    Args:
        camera_index (int): Index of the USB camera (default is 0)
    Returns:
        cap: Video capture object if successful, None if failed
    """
    try:
        # Initialize video capture
        cap = cv2.VideoCapture(camera_index)
        
        # Check if camera opened successfully
        if not cap.isOpened():
            print("Error: Could not open camera")
            return None
            
        # Set frame dimensions (optional)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        return cap
        
    except Exception as e:
        logger.warning("Error initializing camera")
        return None

def capture_frame(cap):
    """
    Function to capture a single frame from the camera
    Args:
        cap: Video capture object
    Returns:
        frame: Captured frame if successful, None if failed
    """
    if cap is None:
        return None
        
    ret, frame = cap.read()
    if ret:
        return frame
    return None

def close_camera(cap):
    """
    Function to release the camera
    Args:
        cap: Video capture object
    """
    if cap is not None:
        cap.release()

# Example usage
if __name__ == "__main__":
    # Open camera
    camera = open_camera()
    
    if camera is not None:
        try:
            while True:
                # Capture frame
                frame = capture_frame(camera)
                
                if frame is not None:
                    # Display frame
                    cv2.imshow('Camera Feed', frame)
                    
                    # Break loop on 'q' press
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                        
        finally:
            # Clean up
            close_camera(camera)
            cv2.destroyAllWindows()