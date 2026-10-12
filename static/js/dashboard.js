document.addEventListener('DOMContentLoaded', () => {
    initCharts();

    // DOM Elements - Navigation & Status
    const navStatus = document.getElementById('nav-status');
    const navDevice = document.getElementById('nav-device');
    const navModel = document.getElementById('nav-model');
    const navFps = document.getElementById('nav-fps');

    // Video Controls
    const btnStart = document.getElementById('btn-start');
    const btnPause = document.getElementById('btn-pause');
    const btnStop = document.getElementById('btn-stop');
    const btnUpload = document.getElementById('btn-upload');
    const btnQuickStart = document.getElementById('btn-quick-start');
    const fileInput = document.getElementById('video-upload');
    const selectVideo = document.getElementById('video-select');
    const selectModel = document.getElementById('model-select');
    const selectImgsz = document.getElementById('imgsz-select');

    // Video Display Elements
    const aiVideo = document.getElementById('ai-video');
    const videoPlaceholder = document.getElementById('video-placeholder');
    const videoErrorBox = document.getElementById('video-error-box');
    const videoErrorText = document.getElementById('video-error-text');

    // Line Controls
    const selectLinePreset = document.getElementById('line-preset-select');
    const sliderLineY = document.getElementById('line-y-slider');
    const sliderVal = document.getElementById('slider-val');
    const btnReverseDir = document.getElementById('btn-reverse-dir');
    const activeLineInfo = document.getElementById('active-line-info');
    const lblDirA = document.getElementById('lbl-dir-a');
    const lblDirB = document.getElementById('lbl-dir-b');

    // Counters & Progress
    const videoName = document.getElementById('video-name');
    const frameCounter = document.getElementById('frame-counter');
    const videoTime = document.getElementById('video-time');
    const aiProgress = document.getElementById('ai-progress');

    // Detection KPIs
    const kpiVisible = document.getElementById('kpi-visible');
    const kpiTracked = document.getElementById('kpi-tracked');
    const kpiLatency = document.getElementById('kpi-latency');
    const kpiTotalCrossings = document.getElementById('kpi-total-crossings');

    // Counts Direction A
    const dirATotal = document.getElementById('dir_a_total');
    const dirACar = document.getElementById('dir_a_car');
    const dirAMotorcycle = document.getElementById('dir_a_motorcycle');
    const dirABus = document.getElementById('dir_a_bus');
    const dirATruck = document.getElementById('dir_a_truck');
    const dirABicycle = document.getElementById('dir_a_bicycle');
    const dirAFlow = document.getElementById('dir_a_flow');

    // Counts Direction B
    const dirBTotal = document.getElementById('dir_b_total');
    const dirBCar = document.getElementById('dir_b_car');
    const dirBMotorcycle = document.getElementById('dir_b_motorcycle');
    const dirBBus = document.getElementById('dir_b_bus');
    const dirBTruck = document.getElementById('dir_b_truck');
    const dirBBicycle = document.getElementById('dir_b_bicycle');
    const dirBFlow = document.getElementById('dir_b_flow');

    // Forecasting UI
    const fc1min = document.getElementById('fc-1min');
    const fc5min = document.getElementById('fc-5min');
    const fc10min = document.getElementById('fc-10min');
    const fc1minSplit = document.getElementById('fc-1min-split');
    const fc5minSplit = document.getElementById('fc-5min-split');
    const fc10minSplit = document.getElementById('fc-10min-split');
    const fcTrend = document.getElementById('fc-trend');
    const fcConfidence = document.getElementById('fc-confidence');
    const fcStatusBadge = document.getElementById('forecast-status-badge');
    const fcMae = document.getElementById('fc-mae');
    const fcExplanation = document.getElementById('fc-explanation');

    // Congestion & Occupancy
    const kpiCongestion = document.getElementById('kpi-congestion');
    const kpiOccupancy = document.getElementById('kpi-occupancy');
    const kpiSpeed = document.getElementById('kpi-speed');

    // Simulated Sensor
    const simSensorName = document.getElementById('sim-sensor-name');
    const simSensorCount = document.getElementById('sim-sensor-count');
    const simSensorSpeed = document.getElementById('sim-sensor-speed');
    const simSensorDensity = document.getElementById('sim-sensor-density');

    let pollInterval = null;

    // Load available video files on startup
    async function refreshVideoList() {
        try {
            const data = await API.listVideos();
            if (data && data.videos && data.videos.length > 0) {
                const currentVal = selectVideo.value;
                selectVideo.innerHTML = '';
                data.videos.forEach(v => {
                    const opt = document.createElement('option');
                    opt.value = v;
                    opt.textContent = v;
                    if (v === 'highway.mp4') opt.selected = true;
                    selectVideo.appendChild(opt);
                });
                if (currentVal && data.videos.includes(currentVal)) {
                    selectVideo.value = currentVal;
                }
            }
        } catch (e) {
            console.error("Failed to load video list:", e);
        }
    }

    function updateDashboardUI(st) {
        if (!st) return;

        // Navigation badges
        navStatus.textContent = "● " + st.status;
        if (st.status === 'PROCESSING') {
            navStatus.className = "badge bg-success ms-2 fs-6";
        } else if (st.status === 'PAUSED') {
            navStatus.className = "badge bg-warning text-dark ms-2 fs-6";
        } else if (st.status === 'VIDEO ERROR') {
            navStatus.className = "badge bg-danger ms-2 fs-6";
        } else if (st.status === 'COMPLETED') {
            navStatus.className = "badge bg-info text-dark ms-2 fs-6";
        } else {
            navStatus.className = "badge bg-secondary ms-2 fs-6";
        }

        const devStr = st.device || "CPU";
        navDevice.innerHTML = `<i class="bi bi-gpu-card me-1"></i> Device: ${devStr}`;
        if (devStr === "CUDA") {
            navDevice.className = "badge bg-dark border border-success text-success px-3 py-2 fs-6";
        } else {
            navDevice.className = "badge bg-dark border border-warning text-warning px-3 py-2 fs-6";
        }

        navModel.innerHTML = `<i class="bi bi-cpu me-1"></i> Model: ${st.model_name} (${st.imgsz}px)`;
        navFps.innerHTML = `<i class="bi bi-speedometer2 me-1"></i> FPS: ${st.fps ? st.fps.toFixed(1) : '0.0'}`;

        // Video Progress
        videoName.textContent = st.filename || selectVideo.value;
        frameCounter.textContent = `${st.frame || 0} / ${st.total_frames || 0}`;
        videoTime.textContent = `${st.video_time_sec ? st.video_time_sec.toFixed(1) : '0.0'}s`;
        aiProgress.textContent = `${st.progress ? st.progress.toFixed(1) : '0.0'}%`;

        // Handle Video Error View
        if (st.status === 'VIDEO ERROR') {
            videoErrorBox.classList.remove('d-none');
            videoErrorText.textContent = st.error_message || "Video file could not be read.";
            aiVideo.classList.add('d-none');
            videoPlaceholder.classList.remove('d-none');
        } else {
            videoErrorBox.classList.add('d-none');
            if (st.status === 'PROCESSING' || st.status === 'PAUSED' || st.status === 'COMPLETED') {
                videoPlaceholder.classList.add('d-none');
                aiVideo.classList.remove('d-none');
            }
        }

        // Detection KPIs
        kpiVisible.textContent = st.vehicles_on_screen || 0;
        kpiTracked.textContent = st.active_tracked || 0;
        kpiLatency.innerHTML = `${st.inference_ms ? st.inference_ms.toFixed(1) : '0.0'}<span class="fs-6">ms</span>`;
        kpiTotalCrossings.textContent = `${st.total_crossings || 0} Crossings`;

        // Direction labels
        const isReversed = st.line_config && st.line_config.reverse_directions;
        lblDirA.textContent = isReversed ? "DIRECTION B ↓" : "DIRECTION A ↑";
        lblDirB.textContent = isReversed ? "DIRECTION A ↑" : "DIRECTION B ↓";

        // Counts Direction A
        const a = st.dir_a || {};
        dirATotal.textContent = a.total || 0;
        dirACar.textContent = a.car || 0;
        dirAMotorcycle.textContent = a.motorcycle || 0;
        dirABus.textContent = a.bus || 0;
        dirATruck.textContent = a.truck || 0;
        dirABicycle.textContent = a.bicycle || 0;
        dirAFlow.textContent = `${st.forecast && st.forecast.dir_a_flow_per_min ? st.forecast.dir_a_flow_per_min : 0.0} /min`;

        // Counts Direction B
        const b = st.dir_b || {};
        dirBTotal.textContent = b.total || 0;
        dirBCar.textContent = b.car || 0;
        dirBMotorcycle.textContent = b.motorcycle || 0;
        dirBBus.textContent = b.bus || 0;
        dirBTruck.textContent = b.truck || 0;
        dirBBicycle.textContent = b.bicycle || 0;
        dirBFlow.textContent = `${st.forecast && st.forecast.dir_b_flow_per_min ? st.forecast.dir_b_flow_per_min : 0.0} /min`;

        // Forecasting UI
        const fc = st.forecast || {};
        fc1min.textContent = fc.forecast_1min !== undefined ? fc.forecast_1min : 0;
        fc5min.textContent = fc.forecast_5min !== undefined ? fc.forecast_5min : 0;
        fc10min.textContent = fc.forecast_10min !== undefined ? fc.forecast_10min : 0;

        fc1minSplit.textContent = `A:${fc.forecast_1min_dir_a || 0} | B:${fc.forecast_1min_dir_b || 0}`;
        fc5minSplit.textContent = `A:${fc.forecast_5min_dir_a || 0} | B:${fc.forecast_5min_dir_b || 0}`;
        fc10minSplit.textContent = `A:${fc.forecast_10min_dir_a || 0} | B:${fc.forecast_10min_dir_b || 0}`;

        fcTrend.textContent = fc.trend || "Stable →";
        fcConfidence.textContent = fc.confidence ? `${fc.confidence} (${fc.status || ''})` : "Low";
        fcStatusBadge.textContent = fc.status || "Preliminary";
        if (fc.is_preliminary) {
            fcStatusBadge.className = "badge bg-warning text-dark";
        } else {
            fcStatusBadge.className = "badge bg-success";
        }

        fcMae.textContent = (fc.baseline_mae !== undefined && fc.baseline_mae !== "N/A") ? `${fc.baseline_mae} crossings (RMSE: ${fc.baseline_rmse})` : "Collecting history...";
        if (fc.explanation) {
            fcExplanation.textContent = fc.explanation;
        }

        // Congestion & Occupancy
        const cong = st.congestion_level || "LOW";
        kpiCongestion.textContent = cong;
        if (cong === 'HIGH') {
            kpiCongestion.className = "badge bg-danger fs-5 px-3 py-1 mt-1";
        } else if (cong === 'MEDIUM') {
            kpiCongestion.className = "badge bg-warning text-dark fs-5 px-3 py-1 mt-1";
        } else {
            kpiCongestion.className = "badge bg-success fs-5 px-3 py-1 mt-1";
        }

        kpiOccupancy.textContent = `${st.occupancy_proxy ? st.occupancy_proxy.toFixed(1) : '0.0'}%`;
        kpiSpeed.textContent = `${st.estimated_speed ? st.estimated_speed.toFixed(1) : '0.0'} px/s`;

        // Update Class Distribution Chart
        updateClassDistChart(a, b);
    }

    async function pollStatus() {
        try {
            const st = await API.getCameraStatus();
            updateDashboardUI(st);

            // Fetch session time-series history for chart
            const history = await API.fetchSessionHistory();
            if (history && history.length > 0) {
                updateTimeSeriesChart(history);
            }

            // Fetch simulated sensor data independently
            const sensor = await API.fetchSensorStatus();
            if (sensor && sensor.data) {
                simSensorName.textContent = sensor.data.sensor_name || 'sim_sensor_1';
                simSensorCount.textContent = sensor.data.vehicle_count || 0;
                simSensorSpeed.textContent = `${sensor.data.average_speed || 0.0} km/h`;
                simSensorDensity.textContent = `${sensor.data.traffic_density || 0.0}%`;
            }
        } catch (e) {
            console.error("Poll error:", e);
        }
    }

    async function startProcessing() {
        const video = selectVideo.value;
        const model = selectModel.value;
        const imgsz = selectImgsz.value;

        videoPlaceholder.classList.add('d-none');
        videoErrorBox.classList.add('d-none');
        aiVideo.classList.remove('d-none');

        // Start backend worker
        const res = await API.startCamera(video, model, 0.25, imgsz);
        if (res.error) {
            videoErrorBox.classList.remove('d-none');
            videoErrorText.textContent = res.error;
            return;
        }

        // Attach live stream with cache-busting timestamp
        aiVideo.src = "/video_feed?" + new Date().getTime();

        clearInterval(pollInterval);
        pollInterval = setInterval(pollStatus, 900);
        pollStatus();
    }

    // Playback Button Listeners
    btnStart.addEventListener('click', startProcessing);
    btnQuickStart.addEventListener('click', () => {
        selectVideo.value = 'highway.mp4';
        startProcessing();
    });

    btnPause.addEventListener('click', async () => {
        await API.pauseCamera();
        pollStatus();
    });

    btnStop.addEventListener('click', async () => {
        await API.stopCamera();
        aiVideo.src = "";
        aiVideo.classList.add('d-none');
        videoPlaceholder.classList.remove('d-none');
        pollStatus();
    });

    // Upload Listener
    btnUpload.addEventListener('click', async () => {
        if (!fileInput.files.length) {
            alert("Please choose a video file first (.mp4, .avi, .mov, .mkv).");
            return;
        }
        btnUpload.disabled = true;
        btnUpload.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Uploading...`;

        const res = await API.uploadVideo(fileInput.files[0]);
        btnUpload.disabled = false;
        btnUpload.innerHTML = `<i class="bi bi-upload"></i> Upload`;

        if (res.error) {
            alert("Upload failed: " + res.error);
        } else {
            await refreshVideoList();
            selectVideo.value = res.filename;
            alert(`Upload successful! '${res.filename}' is ready to process.`);
        }
    });

    // Counting Line Controls
    selectLinePreset.addEventListener('change', async () => {
        const preset = selectLinePreset.value;
        const res = await API.configureLine({ preset: preset });
        if (res && res.line_config) {
            activeLineInfo.textContent = `Preset: ${preset}`;
        }
    });

    sliderLineY.addEventListener('input', async () => {
        const val = parseInt(sliderLineY.value);
        sliderVal.textContent = `${val}%`;
        const yNorm = val / 100.0;
        await API.configureLine({
            norm_pt1: [0.02, yNorm],
            norm_pt2: [0.98, yNorm]
        });
        activeLineInfo.textContent = `Custom Line (Y: ${val}%)`;
    });

    btnReverseDir.addEventListener('click', async () => {
        const st = await API.getCameraStatus();
        const currentRev = st.line_config ? st.line_config.reverse_directions : false;
        const newRev = !currentRev;
        await API.configureLine({ reverse: newRev });
        btnReverseDir.classList.toggle('btn-warning', newRev);
        btnReverseDir.classList.toggle('btn-outline-warning', !newRev);
        pollStatus();
    });

    // Initialization
    refreshVideoList();
    pollStatus();
});
