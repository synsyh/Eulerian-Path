import numpy as np
import cv2
from skimage.morphology import skeletonize
from skimage.util import invert

class ImageProcessor:
    def __init__(self, image_path=None, image_array=None, max_dimension=1024):
        if image_path:
            self.original_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if self.original_image is None:
                raise ValueError(f"Could not load image from {image_path}")
        elif image_array is not None:
            self.original_image = image_array
        else:
            raise ValueError("Must provide either image_path or image_array")
            
        # Optional: Resize if too large to prevent crashes
        self.resize_if_large(max_dimension)

    def resize_if_large(self, max_dimension=1024):
        """
        Resizes the image if either dimension exceeds max_dimension.
        Maintains aspect ratio.
        """
        h, w = self.original_image.shape[:2]
        if h > max_dimension or w > max_dimension:
            scaling_factor = max_dimension / float(max(h, w))
            new_size = (int(w * scaling_factor), int(h * scaling_factor))
            print(f"Resizing image from ({w}, {h}) to {new_size} for performance.")
            self.original_image = cv2.resize(self.original_image, new_size, interpolation=cv2.INTER_AREA)

    def preprocess(self):
        """
        Binarize the image. Assumes dark curve on light background by default.
        """
        # Thresholding (Otsu's method)
        _, binary = cv2.threshold(self.original_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # If the image was already white-on-black, we might not need INVERT.
        # But robustly, we assume we want the 'path' to be True/1/255.
        
        self.binary_image = binary
        return self.binary_image

    def get_skeleton(self):
        """
        Skeletonize the binary image to 1-pixel width.
        """
        # skimage skeletonize expects boolean where True is the foreground object
        bool_image = self.binary_image > 0
        self.skeleton = skeletonize(bool_image)
        return self.skeleton

    def get_skeleton_pixels(self):
        """
        Return coordinates of all True pixels in the skeleton.
        """
        y_indices, x_indices = np.where(self.skeleton)
        return list(zip(y_indices, x_indices))
