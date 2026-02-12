"""
Iris Image Processing Service

Analyzes iris images to extract features for iridology analysis.
Uses OpenCV for image processing and feature detection.
"""

import cv2
import numpy as np
from PIL import Image
from typing import Dict, List, Tuple, Optional
import io
import base64


class IrisImageProcessor:
    """Processes iris images to extract features for iridology analysis."""

    def __init__(self):
        self.zone_angles = self._generate_zone_angles()

    def remove_glare(self, image: np.ndarray) -> np.ndarray:
        """
        Remove glare/reflections from iris image using inpainting.
        Preserves iris features while removing bright light reflections.
        """
        # Convert to different color spaces for analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect glare: very bright spots with low saturation (white reflections)
        # High value (brightness) + low saturation = glare
        _, bright_mask = cv2.threshold(hsv[:, :, 2], 220, 255, cv2.THRESH_BINARY)
        _, low_sat_mask = cv2.threshold(hsv[:, :, 1], 30, 255, cv2.THRESH_BINARY_INV)

        # Combine: glare is bright AND low saturation
        glare_mask = cv2.bitwise_and(bright_mask, low_sat_mask)

        # Also catch pure white spots in grayscale
        _, white_mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        glare_mask = cv2.bitwise_or(glare_mask, white_mask)

        # Dilate the mask slightly to cover glare edges
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        glare_mask = cv2.dilate(glare_mask, kernel, iterations=2)

        # Use inpainting to fill glare areas based on surrounding texture
        # INPAINT_TELEA uses fast marching method - good for preserving texture
        result = cv2.inpaint(image, glare_mask, inpaintRadius=7, flags=cv2.INPAINT_TELEA)

        return result

    def enhance_iris(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance iris visibility with contrast adjustment and noise reduction.
        """
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # This enhances local contrast without over-amplifying noise
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l)

        lab_enhanced = cv2.merge([l_enhanced, a, b])
        enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

        # Light denoising while preserving edges
        denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)

        return denoised

    def preprocess_iris_image(self, image: np.ndarray, remove_glare_flag: bool = True,
                               enhance_flag: bool = True) -> np.ndarray:
        """
        Full preprocessing pipeline for iris images.
        """
        result = image.copy()

        if remove_glare_flag:
            result = self.remove_glare(result)

        if enhance_flag:
            result = self.enhance_iris(result)

        return result

    def preprocess_image_bytes(self, image_data: bytes, remove_glare: bool = True,
                                enhance: bool = True) -> bytes:
        """
        Preprocess image from bytes and return preprocessed bytes.
        """
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return image_data  # Return original if decoding fails

        processed = self.preprocess_iris_image(image, remove_glare, enhance)

        # Encode back to JPEG bytes for sending to Claude
        _, buffer = cv2.imencode('.jpg', processed, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return buffer.tobytes()

    def _generate_zone_angles(self) -> Dict[str, Tuple[int, int]]:
        """Generate angle ranges for each clock position zone."""
        zones = {}
        for hour in range(12):
            # 12 o'clock is at the top (270 degrees in standard coordinates)
            # Each hour spans 30 degrees
            center_angle = (270 - hour * 30) % 360
            start_angle = (center_angle - 15) % 360
            end_angle = (center_angle + 15) % 360
            zones[f"{hour if hour != 0 else 12}:00"] = (start_angle, end_angle)
        return zones

    async def process_image(self, image_data: bytes, eye_side: str,
                            remove_glare: bool = True, enhance: bool = True) -> Dict:
        """
        Process an iris image and extract features.

        Args:
            image_data: Raw image bytes
            eye_side: "left" or "right"
            remove_glare: Whether to remove glare/reflections
            enhance: Whether to enhance contrast

        Returns:
            Dictionary containing extracted iris features
        """
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Could not decode image")

        # Preprocess: remove glare and enhance
        image = self.preprocess_iris_image(image, remove_glare, enhance)

        # Convert to different color spaces for analysis
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Detect iris and pupil
        iris_info = self._detect_iris(gray, image)

        if iris_info is None:
            # If detection fails, use image center as approximation
            h, w = gray.shape
            iris_info = {
                "center": (w // 2, h // 2),
                "iris_radius": min(w, h) // 3,
                "pupil_radius": min(w, h) // 10
            }

        # Extract features
        features = {
            "eye_side": eye_side,
            "image_dimensions": {"width": image.shape[1], "height": image.shape[0]},
            "iris_info": iris_info,
            "dominant_color": self._analyze_dominant_color(image, hsv, iris_info),
            "color_distribution": self._analyze_color_distribution(hsv, iris_info),
            "pupil_size_ratio": self._calculate_pupil_ratio(iris_info),
            "collarette_regularity": self._analyze_collarette(gray, iris_info),
            "detected_markings": self._detect_markings(gray, iris_info),
            "zone_analysis": self._analyze_zones(gray, hsv, iris_info, eye_side),
            "nerve_rings_count": self._count_nerve_rings(gray, iris_info),
            "radial_furrows": self._detect_radial_furrows(gray, iris_info),
            "overall_density": self._assess_fiber_density(gray, iris_info),
            "lymphatic_signs": self._detect_lymphatic_signs(gray, iris_info),
            "brightness_analysis": self._analyze_brightness(gray, iris_info)
        }

        return features

    def _detect_iris(self, gray: np.ndarray, color_image: np.ndarray) -> Optional[Dict]:
        """Detect iris and pupil circles using Hough Circle Transform."""
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)

        # Detect circles for pupil (smaller, darker circle)
        pupil_circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=gray.shape[0] // 4,
            param1=50,
            param2=30,
            minRadius=gray.shape[0] // 20,
            maxRadius=gray.shape[0] // 6
        )

        # Detect circles for iris (larger circle)
        iris_circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=gray.shape[0] // 2,
            param1=50,
            param2=30,
            minRadius=gray.shape[0] // 4,
            maxRadius=gray.shape[0] // 2
        )

        if iris_circles is not None:
            iris = iris_circles[0][0]
            center = (int(iris[0]), int(iris[1]))
            iris_radius = int(iris[2])

            pupil_radius = iris_radius // 3  # Default estimate
            if pupil_circles is not None:
                pupil = pupil_circles[0][0]
                pupil_radius = int(pupil[2])

            return {
                "center": center,
                "iris_radius": iris_radius,
                "pupil_radius": pupil_radius
            }

        return None

    def _analyze_dominant_color(self, bgr: np.ndarray, hsv: np.ndarray, iris_info: Dict) -> str:
        """Determine the dominant iris color (blue, brown, mixed, hazel)."""
        center = iris_info["center"]
        iris_r = iris_info["iris_radius"]
        pupil_r = iris_info["pupil_radius"]

        # Create mask for iris region (excluding pupil)
        mask = np.zeros(bgr.shape[:2], dtype=np.uint8)
        cv2.circle(mask, center, iris_r, 255, -1)
        cv2.circle(mask, center, pupil_r, 0, -1)

        # Get mean color in iris region
        mean_bgr = cv2.mean(bgr, mask=mask)[:3]
        mean_hsv = cv2.mean(hsv, mask=mask)[:3]

        # Analyze hue and saturation to determine color type
        hue = mean_hsv[0]
        saturation = mean_hsv[1]
        value = mean_hsv[2]

        blue_ratio = mean_bgr[0] / (mean_bgr[2] + 1)  # Blue / Red

        if blue_ratio > 1.2 and saturation > 30:
            return "blue (lymphatic)"
        elif mean_bgr[2] > 100 and blue_ratio < 0.8:
            return "brown (hematogenic)"
        elif hue > 15 and hue < 35:
            return "hazel"
        else:
            return "mixed (biliary)"

    def _analyze_color_distribution(self, hsv: np.ndarray, iris_info: Dict) -> Dict:
        """Analyze color distribution across iris zones."""
        center = iris_info["center"]
        iris_r = iris_info["iris_radius"]
        pupil_r = iris_info["pupil_radius"]

        # Analyze inner, middle, and outer thirds
        zones = {}
        for zone_name, (inner_ratio, outer_ratio) in [
            ("inner", (0.33, 0.5)),
            ("middle", (0.5, 0.75)),
            ("outer", (0.75, 1.0))
        ]:
            inner_r = int(pupil_r + (iris_r - pupil_r) * inner_ratio)
            outer_r = int(pupil_r + (iris_r - pupil_r) * outer_ratio)

            mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            cv2.circle(mask, center, outer_r, 255, -1)
            cv2.circle(mask, center, inner_r, 0, -1)

            mean_hsv = cv2.mean(hsv, mask=mask)[:3]
            zones[zone_name] = {
                "hue": float(mean_hsv[0]),
                "saturation": float(mean_hsv[1]),
                "brightness": float(mean_hsv[2])
            }

        return zones

    def _calculate_pupil_ratio(self, iris_info: Dict) -> float:
        """Calculate pupil to iris size ratio."""
        return iris_info["pupil_radius"] / iris_info["iris_radius"]

    def _analyze_collarette(self, gray: np.ndarray, iris_info: Dict) -> float:
        """Analyze the autonomic nerve wreath (collarette) regularity."""
        center = iris_info["center"]
        iris_r = iris_info["iris_radius"]
        pupil_r = iris_info["pupil_radius"]

        # The collarette is typically about 1/3 from pupil edge
        collarette_r = int(pupil_r + (iris_r - pupil_r) * 0.33)

        # Sample points around the collarette
        num_samples = 36
        intensities = []

        for i in range(num_samples):
            angle = 2 * np.pi * i / num_samples
            x = int(center[0] + collarette_r * np.cos(angle))
            y = int(center[1] + collarette_r * np.sin(angle))

            if 0 <= x < gray.shape[1] and 0 <= y < gray.shape[0]:
                intensities.append(gray[y, x])

        if len(intensities) > 0:
            # Calculate coefficient of variation (lower = more regular)
            mean_intensity = np.mean(intensities)
            std_intensity = np.std(intensities)
            if mean_intensity > 0:
                cv = std_intensity / mean_intensity
                # Convert to regularity score (0-1, higher = more regular)
                return max(0, min(1, 1 - cv))

        return 0.5  # Default middle value

    def _detect_markings(self, gray: np.ndarray, iris_info: Dict) -> List[Dict]:
        """Detect various iris markings (lacunae, crypts, spots, etc.)."""
        markings = []
        center = iris_info["center"]
        iris_r = iris_info["iris_radius"]
        pupil_r = iris_info["pupil_radius"]

        # Create iris mask
        mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.circle(mask, center, iris_r, 255, -1)
        cv2.circle(mask, center, pupil_r, 0, -1)

        masked_gray = cv2.bitwise_and(gray, gray, mask=mask)

        # Detect dark spots (potential lacunae/crypts)
        _, dark_thresh = cv2.threshold(masked_gray, 50, 255, cv2.THRESH_BINARY_INV)
        dark_thresh = cv2.bitwise_and(dark_thresh, mask)

        contours, _ = cv2.findContours(dark_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 20 and area < 500:  # Filter by size
                M = cv2.moments(contour)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])

                    # Calculate position relative to iris center
                    dx = cx - center[0]
                    dy = cy - center[1]
                    distance = np.sqrt(dx*dx + dy*dy)
                    angle = np.degrees(np.arctan2(-dy, dx)) % 360

                    # Determine clock position
                    clock_pos = self._angle_to_clock(angle)
                    zone = self._get_zone_from_distance(distance, iris_r, pupil_r)

                    markings.append({
                        "type": "lacuna" if area > 100 else "pigment_spot",
                        "position": {"x": cx, "y": cy},
                        "clock_position": clock_pos,
                        "zone": zone,
                        "size": "large" if area > 200 else "medium" if area > 50 else "small",
                        "intensity": "dark"
                    })

        # Detect light spots (potential healing signs or tophi)
        _, light_thresh = cv2.threshold(masked_gray, 200, 255, cv2.THRESH_BINARY)
        light_thresh = cv2.bitwise_and(light_thresh, mask)

        contours, _ = cv2.findContours(light_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 10 and area < 300:
                M = cv2.moments(contour)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])

                    dx = cx - center[0]
                    dy = cy - center[1]
                    distance = np.sqrt(dx*dx + dy*dy)
                    angle = np.degrees(np.arctan2(-dy, dx)) % 360

                    clock_pos = self._angle_to_clock(angle)
                    zone = self._get_zone_from_distance(distance, iris_r, pupil_r)

                    markings.append({
                        "type": "tophi" if zone == "lymphatic" else "healing_sign",
                        "position": {"x": cx, "y": cy},
                        "clock_position": clock_pos,
                        "zone": zone,
                        "size": "medium" if area > 50 else "small",
                        "intensity": "light"
                    })

        return markings[:20]  # Limit to top 20 markings

    def _analyze_zones(self, gray: np.ndarray, hsv: np.ndarray, iris_info: Dict, eye_side: str) -> Dict:
        """Analyze each clock position zone of the iris."""
        center = iris_info["center"]
        iris_r = iris_info["iris_radius"]
        pupil_r = iris_info["pupil_radius"]

        zone_analysis = {}

        for clock_pos, (start_angle, end_angle) in self.zone_angles.items():
            # Create mask for this zone
            mask = np.zeros(gray.shape, dtype=np.uint8)

            # Draw the zone as a pie slice
            cv2.ellipse(mask, center, (iris_r, iris_r), 0, -end_angle, -start_angle, 255, -1)
            cv2.circle(mask, center, pupil_r, 0, -1)

            # Calculate statistics for this zone
            masked_gray = cv2.bitwise_and(gray, gray, mask=mask)
            masked_hsv = cv2.bitwise_and(hsv, hsv, mask=mask)

            non_zero = masked_gray[mask > 0]
            if len(non_zero) > 0:
                mean_brightness = float(np.mean(non_zero))
                std_brightness = float(np.std(non_zero))

                # Classify the zone condition
                if mean_brightness < 80:
                    condition = "chronic/dark"
                elif mean_brightness > 180:
                    condition = "acute/inflamed"
                else:
                    condition = "normal"

                zone_analysis[clock_pos] = {
                    "mean_brightness": mean_brightness,
                    "variability": std_brightness,
                    "condition": condition,
                    "notes": self._get_zone_notes(mean_brightness, std_brightness)
                }

        return zone_analysis

    def _count_nerve_rings(self, gray: np.ndarray, iris_info: Dict) -> int:
        """Count concentric nerve rings (stress rings) in the iris."""
        center = iris_info["center"]
        iris_r = iris_info["iris_radius"]
        pupil_r = iris_info["pupil_radius"]

        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)

        # Create mask
        mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.circle(mask, center, iris_r, 255, -1)
        cv2.circle(mask, center, pupil_r, 0, -1)
        edges = cv2.bitwise_and(edges, edges, mask=mask)

        # Sample radial lines and count crossings
        num_radials = 12
        ring_counts = []

        for i in range(num_radials):
            angle = 2 * np.pi * i / num_radials
            crossings = 0
            prev_val = 0

            for r in range(pupil_r, iris_r):
                x = int(center[0] + r * np.cos(angle))
                y = int(center[1] + r * np.sin(angle))

                if 0 <= x < edges.shape[1] and 0 <= y < edges.shape[0]:
                    val = edges[y, x]
                    if val > 0 and prev_val == 0:
                        crossings += 1
                    prev_val = val

            ring_counts.append(crossings)

        # Average crossings indicates number of rings
        avg_rings = int(np.median(ring_counts))
        return max(0, min(avg_rings, 10))  # Cap at 10 rings

    def _detect_radial_furrows(self, gray: np.ndarray, iris_info: Dict) -> List[Dict]:
        """Detect radial furrows (radii solaris) emanating from pupil."""
        center = iris_info["center"]
        iris_r = iris_info["iris_radius"]
        pupil_r = iris_info["pupil_radius"]

        furrows = []

        # Apply edge detection and look for radial patterns
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 30, 100)

        # Sample multiple angles and check for radial patterns
        num_angles = 36
        for i in range(num_angles):
            angle = 2 * np.pi * i / num_angles
            intensity_profile = []

            for r in range(pupil_r, int(iris_r * 0.7)):
                x = int(center[0] + r * np.cos(angle))
                y = int(center[1] + r * np.sin(angle))

                if 0 <= x < edges.shape[1] and 0 <= y < edges.shape[0]:
                    intensity_profile.append(edges[y, x])

            if len(intensity_profile) > 10:
                # Check if this angle has consistent edge response (radial line)
                edge_count = sum(1 for v in intensity_profile if v > 0)
                if edge_count > len(intensity_profile) * 0.3:
                    clock_pos = self._angle_to_clock(np.degrees(angle))
                    furrows.append({
                        "angle": float(np.degrees(angle)),
                        "clock_position": clock_pos,
                        "strength": edge_count / len(intensity_profile)
                    })

        return furrows[:10]  # Limit to top 10 furrows

    def _assess_fiber_density(self, gray: np.ndarray, iris_info: Dict) -> str:
        """Assess the overall fiber density of the iris."""
        center = iris_info["center"]
        iris_r = iris_info["iris_radius"]
        pupil_r = iris_info["pupil_radius"]

        # Create mask
        mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.circle(mask, center, iris_r, 255, -1)
        cv2.circle(mask, center, pupil_r, 0, -1)

        masked_gray = cv2.bitwise_and(gray, gray, mask=mask)

        # Calculate texture features using Laplacian variance
        laplacian = cv2.Laplacian(masked_gray, cv2.CV_64F)
        texture_variance = laplacian.var()

        # Also look at local contrast
        non_zero = masked_gray[mask > 0]
        brightness_std = np.std(non_zero)

        # Combine metrics to determine density
        if texture_variance > 500 and brightness_std > 40:
            return "silk"  # Tight, well-defined fibers
        elif texture_variance > 300 and brightness_std > 30:
            return "linen"  # Good fiber structure
        elif texture_variance > 150:
            return "hessian"  # Looser fibers
        else:
            return "net"  # Very loose, visible gaps

    def _detect_lymphatic_signs(self, gray: np.ndarray, iris_info: Dict) -> Dict:
        """Detect lymphatic rosary and other lymphatic signs at iris periphery."""
        center = iris_info["center"]
        iris_r = iris_info["iris_radius"]

        # Focus on outer 15% of iris (lymphatic zone)
        inner_r = int(iris_r * 0.85)

        mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.circle(mask, center, iris_r, 255, -1)
        cv2.circle(mask, center, inner_r, 0, -1)

        masked = cv2.bitwise_and(gray, gray, mask=mask)

        # Look for bright spots (tophi/rosary beads)
        _, bright = cv2.threshold(masked, 200, 255, cv2.THRESH_BINARY)
        bright = cv2.bitwise_and(bright, mask)

        contours, _ = cv2.findContours(bright, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        rosary_count = len([c for c in contours if 10 < cv2.contourArea(c) < 200])

        # Check for scurf rim (dark ring at edge)
        edge_mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.circle(edge_mask, center, iris_r, 255, 3)
        edge_brightness = np.mean(gray[edge_mask > 0])

        return {
            "rosary_beads_count": int(rosary_count),
            "rosary_present": bool(rosary_count > 5),
            "scurf_rim_present": bool(edge_brightness < 80),
            "lymphatic_congestion_level": "high" if rosary_count > 15 else "moderate" if rosary_count > 5 else "low"
        }

    def _analyze_brightness(self, gray: np.ndarray, iris_info: Dict) -> Dict:
        """Analyze overall brightness distribution in the iris."""
        center = iris_info["center"]
        iris_r = iris_info["iris_radius"]
        pupil_r = iris_info["pupil_radius"]

        mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.circle(mask, center, iris_r, 255, -1)
        cv2.circle(mask, center, pupil_r, 0, -1)

        non_zero = gray[mask > 0]

        return {
            "mean": float(np.mean(non_zero)),
            "std": float(np.std(non_zero)),
            "min": float(np.min(non_zero)),
            "max": float(np.max(non_zero)),
            "overall_assessment": self._brightness_assessment(np.mean(non_zero))
        }

    def _brightness_assessment(self, mean_brightness: float) -> str:
        """Convert brightness to tissue condition assessment."""
        if mean_brightness > 170:
            return "Predominantly acute/active signs"
        elif mean_brightness > 130:
            return "Mixed acute and subacute"
        elif mean_brightness > 90:
            return "Subacute to early chronic"
        else:
            return "Chronic/degenerative conditions indicated"

    def _angle_to_clock(self, angle: float) -> str:
        """Convert angle to clock position."""
        # Normalize angle to 0-360
        angle = angle % 360
        # Convert to clock position (12 o'clock = 90 degrees / top)
        hour = int(((90 - angle) % 360) / 30 + 0.5) % 12
        if hour == 0:
            hour = 12
        return f"{hour}:00"

    def _get_zone_from_distance(self, distance: float, iris_r: int, pupil_r: int) -> str:
        """Determine which concentric zone based on distance from center."""
        relative_pos = (distance - pupil_r) / (iris_r - pupil_r)

        if relative_pos < 0.15:
            return "stomach"
        elif relative_pos < 0.33:
            return "intestinal"
        elif relative_pos < 0.4:
            return "collarette"
        elif relative_pos < 0.8:
            return "ciliary"
        else:
            return "lymphatic"

    def _get_zone_notes(self, mean_brightness: float, std: float) -> str:
        """Generate notes based on zone analysis."""
        notes = []

        if mean_brightness < 80:
            notes.append("Dark coloring suggests chronic condition or inherent weakness")
        elif mean_brightness > 180:
            notes.append("Bright coloring suggests acute inflammation or irritation")

        if std > 40:
            notes.append("High variability may indicate mixed conditions")

        return "; ".join(notes) if notes else "Within normal range"

    def crop_iris_circle(self, image_data: bytes, output_size: int = 400) -> bytes:
        """
        Detect and crop JUST the iris (colored part) from the image.
        Returns a fixed-size square image with the iris perfectly centered.
        All output images are the same size regardless of input, so left and right eyes match.
        The iris will fill the circular output for accurate chart overlay.

        Args:
            image_data: Raw image bytes
            output_size: Fixed output size in pixels (default 400x400)
        """
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return image_data

        # Preprocess for better detection
        processed = self.preprocess_iris_image(image, remove_glare_flag=True, enhance_flag=True)
        gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)

        # Detect iris
        iris_info = self._detect_iris(gray, processed)

        if iris_info is None:
            # Fallback: use center of image
            h, w = image.shape[:2]
            iris_info = {
                "center": (w // 2, h // 2),
                "iris_radius": min(w, h) // 3,
                "pupil_radius": min(w, h) // 10
            }

        center = iris_info["center"]
        radius = iris_info["iris_radius"]

        # Crop exactly to the iris radius - no extra margin
        # This ensures just the iris is captured, not eyelids
        crop_radius = radius

        # Calculate crop bounds - ensure we get a square centered on iris
        x1 = int(center[0] - crop_radius)
        y1 = int(center[1] - crop_radius)
        x2 = int(center[0] + crop_radius)
        y2 = int(center[1] + crop_radius)

        # Handle edge cases where iris is near image boundary
        # Pad with black if needed to keep iris centered
        pad_left = max(0, -x1)
        pad_top = max(0, -y1)
        pad_right = max(0, x2 - image.shape[1])
        pad_bottom = max(0, y2 - image.shape[0])

        # Adjust bounds to valid image region
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(image.shape[1], x2)
        y2 = min(image.shape[0], y2)

        # Crop the region
        cropped = processed[y1:y2, x1:x2]

        # Add padding if iris was near edge (to keep it centered)
        if pad_left > 0 or pad_top > 0 or pad_right > 0 or pad_bottom > 0:
            cropped = cv2.copyMakeBorder(
                cropped,
                pad_top, pad_bottom, pad_left, pad_right,
                cv2.BORDER_CONSTANT,
                value=[0, 0, 0]
            )

        # Resize to fixed output size - iris will fill the frame
        cropped = cv2.resize(cropped, (output_size, output_size), interpolation=cv2.INTER_LANCZOS4)

        # Create circular mask that matches the iris edge
        # The iris should fill almost the entire circle
        mask = np.zeros((output_size, output_size), dtype=np.uint8)
        circle_center = (output_size // 2, output_size // 2)
        circle_radius = int(output_size * 0.48)  # Nearly full size - iris fills the circle
        cv2.circle(mask, circle_center, circle_radius, 255, -1)

        # Create RGBA image with transparent background
        rgba = cv2.cvtColor(cropped, cv2.COLOR_BGR2BGRA)
        rgba[:, :, 3] = mask  # Set alpha channel

        # Encode as PNG to preserve transparency
        _, buffer = cv2.imencode('.png', rgba)
        return buffer.tobytes()

    def create_annotated_image(self, image_data: bytes, features: Dict) -> bytes:
        """Create an annotated version of the iris image."""
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if "iris_info" in features:
            info = features["iris_info"]
            center = tuple(info["center"])

            # Draw iris circle
            cv2.circle(image, center, info["iris_radius"], (0, 255, 0), 2)
            # Draw pupil circle
            cv2.circle(image, center, info["pupil_radius"], (255, 0, 0), 2)
            # Draw collarette
            collarette_r = int(info["pupil_radius"] + (info["iris_radius"] - info["pupil_radius"]) * 0.33)
            cv2.circle(image, center, collarette_r, (0, 255, 255), 1)

            # Draw clock positions
            for hour in range(12):
                angle = np.radians(90 - hour * 30)
                x = int(center[0] + info["iris_radius"] * 0.9 * np.cos(angle))
                y = int(center[1] - info["iris_radius"] * 0.9 * np.sin(angle))
                cv2.putText(image, f"{hour if hour else 12}", (x-10, y+5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        # Mark detected markings
        if "detected_markings" in features:
            for marking in features["detected_markings"][:10]:
                pos = (marking["position"]["x"], marking["position"]["y"])
                color = (0, 0, 255) if marking["intensity"] == "dark" else (255, 255, 0)
                cv2.circle(image, pos, 5, color, 2)

        # Encode back to bytes
        _, buffer = cv2.imencode('.png', image)
        return buffer.tobytes()
