import math

class VehicleCounter:
    def __init__(self):
        # Line points in normalized coordinates [0.0 to 1.0] (default horizontal center)
        self.norm_pt1 = [0.02, 0.50]
        self.norm_pt2 = [0.98, 0.50]
        self.line_pt1 = (0, 360)
        self.line_pt2 = (1280, 360)
        self.current_preset = "horizontal"

        # Reverse Direction A and B toggle
        self.reverse_directions = False

        # State tracking
        self.counted_tracks = {} # track_id -> dict with details
        self.crossing_events = [] # list of crossing events for time-series extraction

        self.direction_a_counts = {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0, "bicycle": 0, "total": 0}
        self.direction_b_counts = {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0, "bicycle": 0, "total": 0}

    def set_line_normalized(self, norm_pt1, norm_pt2, frame_width=1280, frame_height=720, preset="custom"):
        self.norm_pt1 = [float(norm_pt1[0]), float(norm_pt1[1])]
        self.norm_pt2 = [float(norm_pt2[0]), float(norm_pt2[1])]
        self.current_preset = preset
        self.update_pixel_coords(frame_width, frame_height)

    def set_preset(self, preset_name, frame_width=1280, frame_height=720):
        presets = {
            "horizontal": ([0.02, 0.50], [0.98, 0.50]),
            "horizontal_high": ([0.02, 0.35], [0.98, 0.35]),
            "horizontal_low": ([0.02, 0.65], [0.98, 0.65]),
            "angled_down": ([0.05, 0.30], [0.95, 0.70]),
            "angled_up": ([0.05, 0.70], [0.95, 0.30]),
            "vertical": ([0.50, 0.05], [0.50, 0.95])
        }
        if preset_name in presets:
            pt1, pt2 = presets[preset_name]
            self.set_line_normalized(pt1, pt2, frame_width, frame_height, preset=preset_name)

    def update_pixel_coords(self, frame_width, frame_height):
        self.line_pt1 = (int(self.norm_pt1[0] * frame_width), int(self.norm_pt1[1] * frame_height))
        self.line_pt2 = (int(self.norm_pt2[0] * frame_width), int(self.norm_pt2[1] * frame_height))

    def toggle_reverse_directions(self):
        self.reverse_directions = not self.reverse_directions
        return self.reverse_directions

    def reset(self):
        self.counted_tracks.clear()
        self.crossing_events.clear()
        self.direction_a_counts = {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0, "bicycle": 0, "total": 0}
        self.direction_b_counts = {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0, "bicycle": 0, "total": 0}

    def _cross_product(self, p1, p2, p3):
        """
        2D cross product of vector (p1 -> p2) and vector (p1 -> p3).
        Determines which side of directed line segment p1-p2 point p3 lies on.
        Positive: Left side of line vector.
        Negative: Right side of line vector.
        """
        return (p2[0] - p1[0]) * (p3[1] - p1[1]) - (p2[1] - p1[1]) * (p3[0] - p1[0])

    def update_counts(self, detections, frame_idx=0, video_time_sec=0.0):
        """
        Evaluates active detections for counting line crossings.
        Detects direction geometrically using line normal and centroid history.
        Enforces strict single-count per vehicle ID.
        """
        new_crossings = []

        for det in detections:
            track_id = det["track_id"]
            if track_id in self.counted_tracks:
                continue

            history = det["history"]
            if len(history) < 2:
                continue

            prev_pos = history[-2]
            curr_pos = history[-1]

            cp_prev = self._cross_product(self.line_pt1, self.line_pt2, prev_pos)
            cp_curr = self._cross_product(self.line_pt1, self.line_pt2, curr_pos)

            # Check if sign changed (i.e. crossed the line)
            if (cp_prev * cp_curr) < 0:
                # Crossed the line!
                # Positive to negative or negative to positive:
                if cp_prev > 0 and cp_curr < 0:
                    raw_dir = "A"
                else:
                    raw_dir = "B"

                # Apply reversal toggle if requested
                final_dir = raw_dir
                if self.reverse_directions:
                    final_dir = "B" if raw_dir == "A" else "A"

                v_class = det["class_name"]
                # Standardize class name
                if v_class not in ["car", "motorcycle", "bus", "truck", "bicycle"]:
                    v_class = "car"

                # Record crossing
                if final_dir == "A":
                    self.direction_a_counts["total"] += 1
                    self.direction_a_counts[v_class] = self.direction_a_counts.get(v_class, 0) + 1
                else:
                    self.direction_b_counts["total"] += 1
                    self.direction_b_counts[v_class] = self.direction_b_counts.get(v_class, 0) + 1

                event = {
                    "track_id": track_id,
                    "direction": final_dir,
                    "class_name": v_class,
                    "frame_idx": frame_idx,
                    "video_time_sec": round(video_time_sec, 2)
                }
                self.counted_tracks[track_id] = event
                self.crossing_events.append(event)
                new_crossings.append(event)

        return {
            "dir_a": dict(self.direction_a_counts),
            "dir_b": dict(self.direction_b_counts),
            "total_crossings": self.direction_a_counts["total"] + self.direction_b_counts["total"],
            "new_crossings": new_crossings,
            "reverse_directions": self.reverse_directions,
            "line_pt1": self.line_pt1,
            "line_pt2": self.line_pt2,
            "preset": self.current_preset
        }
