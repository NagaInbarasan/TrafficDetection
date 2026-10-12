import math
from collections import deque

class TrafficForecastingService:
    """
    Dedicated forecasting service that processes real time-series windows
    extracted from the video's observed vehicle crossing events.
    Does not use fake or synthetic data.
    """
    def __init__(self, window_sec=10.0):
        self.window_sec = float(window_sec) # aggregation window in source-video seconds
        self.windows = [] # list of aggregated window dictionaries
        self.current_window = None
        self.current_window_idx = 0
        self.session_id = None

        # Rolling tracking for persistence vs damped-trend evaluation
        self.past_evaluations = [] # stores (actual, forecast_persistence, forecast_damped)

    def reset(self, session_id=None):
        self.session_id = session_id
        self.windows = []
        self.current_window = None
        self.current_window_idx = 0
        self.past_evaluations.clear()

    def process_frame_state(self, video_time_sec, new_crossings, visible_count, occupancy_proxy, avg_speed):
        """
        Aggregates frame events into time windows based on source-video seconds.
        """
        win_idx = int(video_time_sec // self.window_sec)

        if self.current_window is None:
            self.current_window_idx = win_idx
            self.current_window = self._new_window(win_idx, win_idx * self.window_sec)

        # If we crossed into a new window
        if win_idx > self.current_window_idx:
            # Finalize previous window
            self._finalize_window(self.current_window)
            self.windows.append(self.current_window)

            # In case multiple windows were skipped (e.g. video jump)
            for gap_idx in range(self.current_window_idx + 1, win_idx):
                gap_win = self._new_window(gap_idx, gap_idx * self.window_sec)
                self._finalize_window(gap_win)
                self.windows.append(gap_win)

            self.current_window_idx = win_idx
            self.current_window = self._new_window(win_idx, win_idx * self.window_sec)

        # Accumulate into current window
        for event in new_crossings:
            d = event.get("direction", "A")
            cls = event.get("class_name", "car")
            if d == "A":
                self.current_window["dir_a"] += 1
                self.current_window["dir_a_classes"][cls] = self.current_window["dir_a_classes"].get(cls, 0) + 1
            else:
                self.current_window["dir_b"] += 1
                self.current_window["dir_b_classes"][cls] = self.current_window["dir_b_classes"].get(cls, 0) + 1
            self.current_window["total"] += 1

        self.current_window["samples"] += 1
        self.current_window["sum_occupancy"] += occupancy_proxy
        self.current_window["sum_speed"] += avg_speed
        self.current_window["end_time_sec"] = video_time_sec

    def _new_window(self, idx, start_sec):
        return {
            "window_idx": idx,
            "start_time_sec": round(start_sec, 2),
            "end_time_sec": round(start_sec + self.window_sec, 2),
            "dir_a": 0,
            "dir_b": 0,
            "total": 0,
            "dir_a_classes": {},
            "dir_b_classes": {},
            "samples": 0,
            "sum_occupancy": 0.0,
            "sum_speed": 0.0,
            "flow_rate_per_min": 0.0,
            "avg_occupancy": 0.0,
            "avg_speed": 0.0
        }

    def _finalize_window(self, win):
        s = max(1, win["samples"])
        win["avg_occupancy"] = round(win["sum_occupancy"] / s, 2)
        win["avg_speed"] = round(win["sum_speed"] / s, 1)
        # Flow rate scaled to crossings per minute
        multiplier = 60.0 / self.window_sec
        win["flow_rate_per_min"] = round(win["total"] * multiplier, 1)
        win["dir_a_flow_per_min"] = round(win["dir_a"] * multiplier, 1)
        win["dir_b_flow_per_min"] = round(win["dir_b"] * multiplier, 1)

    def generate_forecast(self, current_video_time_sec=0.0, video_time_sec=None):
        """
        Generates empirical future traffic forecast using observed video time-series.
        Returns forecasts for 1, 5, and 10 minutes, directional flow, trend, and confidence metadata.
        """
        if video_time_sec is not None:
            current_video_time_sec = video_time_sec
        all_completed = list(self.windows)
        # Include current partial window if it has data
        active_series = [w["total"] for w in all_completed]
        active_dir_a = [w["dir_a"] for w in all_completed]
        active_dir_b = [w["dir_b"] for w in all_completed]

        if self.current_window and self.current_window["samples"] > 0:
            active_series.append(self.current_window["total"])
            active_dir_a.append(self.current_window["dir_a"])
            active_dir_b.append(self.current_window["dir_b"])

        total_observed_sec = max(current_video_time_sec, len(active_series) * self.window_sec)
        n_windows = len(active_series)

        # Baseline 1: Persistence / Rolling Average
        if n_windows == 0:
            recent_rate_per_min = 0.0
            dir_a_rate_per_min = 0.0
            dir_b_rate_per_min = 0.0
        else:
            # Average over up to last 4 windows
            recent_k = min(4, n_windows)
            recent_avg_total = sum(active_series[-recent_k:]) / recent_k
            recent_avg_a = sum(active_dir_a[-recent_k:]) / recent_k
            recent_avg_b = sum(active_dir_b[-recent_k:]) / recent_k

            multiplier = 60.0 / self.window_sec
            recent_rate_per_min = round(recent_avg_total * multiplier, 1)
            dir_a_rate_per_min = round(recent_avg_a * multiplier, 1)
            dir_b_rate_per_min = round(recent_avg_b * multiplier, 1)

        # Damped Trend Time-Series Model (Holt's Damped Linear)
        # When enough windows exist (>= 3), estimate level and trend
        damped_rate_per_min = recent_rate_per_min
        trend_status = "Stable"
        trend_slope_per_min = 0.0

        if n_windows >= 3:
            # Fit Holt's damped trend
            alpha = 0.4
            beta = 0.3
            phi = 0.85 # Damping factor to prevent runaway growth
            level = active_series[0]
            trend = active_series[1] - active_series[0]

            for val in active_series[1:]:
                prev_level = level
                level = alpha * val + (1.0 - alpha) * (level + phi * trend)
                trend = beta * (level - prev_level) + (1.0 - beta) * (phi * trend)

            # Trend direction determination
            trend_per_win = phi * trend
            trend_slope_per_min = round(trend_per_win * (60.0 / self.window_sec), 2)

            if trend_slope_per_min > 1.5:
                trend_status = "Increasing ↑"
            elif trend_slope_per_min < -1.5:
                trend_status = "Decreasing ↓"
            else:
                trend_status = "Stable →"

            # Project flow rate per min with damping
            damped_rate_per_min = max(0.0, round((level + trend_per_win) * (60.0 / self.window_sec), 1))

        # Projected cumulative counts for 1 min, 5 min, 10 min
        # For horizon H minutes:
        # Expected crossings = rate_per_min * H
        flow_base = damped_rate_per_min if n_windows >= 3 else recent_rate_per_min

        pred_1min = int(round(flow_base * 1.0))
        pred_5min = int(round(flow_base * 5.0))
        pred_10min = int(round(flow_base * 10.0))

        # Directional forecast split
        total_rate = max(0.1, dir_a_rate_per_min + dir_b_rate_per_min)
        ratio_a = dir_a_rate_per_min / total_rate
        ratio_b = dir_b_rate_per_min / total_rate

        pred_1m_a = int(round(pred_1min * ratio_a))
        pred_1m_b = int(round(pred_1min * ratio_b))
        pred_5m_a = int(round(pred_5min * ratio_a))
        pred_5m_b = int(round(pred_5min * ratio_b))
        pred_10m_a = int(round(pred_10min * ratio_a))
        pred_10m_b = int(round(pred_10min * ratio_b))

        # Video duration & Confidence classification (Section 9)
        if total_observed_sec < 30.0:
            confidence = "Low"
            status = "Preliminary"
            message = "Preliminary Forecast — Short observation window (<30s). Trend stability requires longer footage."
            is_preliminary = True
        elif total_observed_sec < 120.0:
            confidence = "Moderate"
            status = "Observed Trend"
            message = f"Observed Trend Forecast — Based on {int(total_observed_sec)}s of source-video traffic history."
            is_preliminary = False
        else:
            confidence = "High"
            status = "Active Time-Series"
            message = f"Active Time-Series Forecast — Stable trend fitted over {int(total_observed_sec)}s."
            is_preliminary = False

        # Evaluation metrics against baseline on observed windows (MAE/RMSE)
        eval_metrics = self._calculate_evaluation_metrics()

        return {
            "current_flow_rate_per_min": recent_rate_per_min,
            "dir_a_flow_per_min": dir_a_rate_per_min,
            "dir_b_flow_per_min": dir_b_rate_per_min,
            "forecast_1min": pred_1min,
            "forecast_5min": pred_5min,
            "forecast_10min": pred_10min,
            "forecast_1min_dir_a": pred_1m_a,
            "forecast_1min_dir_b": pred_1m_b,
            "forecast_5min_dir_a": pred_5m_a,
            "forecast_5min_dir_b": pred_5m_b,
            "forecast_10min_dir_a": pred_10m_a,
            "forecast_10min_dir_b": pred_10m_b,
            "trend": trend_status,
            "trend_slope": trend_slope_per_min,
            "confidence": confidence,
            "status": status,
            "is_preliminary": is_preliminary,
            "explanation": message,
            "observed_duration_sec": round(total_observed_sec, 1),
            "observed_windows_count": n_windows,
            "baseline_mae": eval_metrics.get("mae", "N/A"),
            "baseline_rmse": eval_metrics.get("rmse", "N/A"),
            "method": "Holt's Damped Trend (phi=0.85) + Window Persistence"
        }

    def _calculate_evaluation_metrics(self):
        """
        Calculates MAE and RMSE of 1-step ahead persistence baseline
        on observed historical windows.
        """
        if len(self.windows) < 3:
            return {"mae": "Collecting history...", "rmse": "Collecting history..."}

        errors = []
        for i in range(1, len(self.windows)):
            actual = self.windows[i]["total"]
            predicted = self.windows[i-1]["total"] # 1-step persistence baseline
            errors.append(actual - predicted)

        if not errors:
            return {"mae": "N/A", "rmse": "N/A"}

        mae = round(sum(abs(e) for e in errors) / len(errors), 2)
        rmse = round(math.sqrt(sum(e * e for e in errors) / len(errors)), 2)
        return {"mae": mae, "rmse": rmse}

    def get_history_series(self):
        """
        Returns clean time-series data for charting:
        Source-video timestamps, Direction A crossings, Direction B crossings, flow rate.
        """
        history = []
        for w in self.windows:
            history.append({
                "video_time_sec": w["end_time_sec"],
                "dir_a": w["dir_a"],
                "dir_b": w["dir_b"],
                "total": w["total"],
                "flow_rate_per_min": w.get("flow_rate_per_min", 0.0),
                "dir_a_flow_per_min": w.get("dir_a_flow_per_min", 0.0),
                "dir_b_flow_per_min": w.get("dir_b_flow_per_min", 0.0),
                "avg_occupancy": w.get("avg_occupancy", 0.0),
                "avg_speed": w.get("avg_speed", 0.0)
            })
        return history
