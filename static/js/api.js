const API = {
    fetchCurrentTraffic: async () => {
        const res = await fetch('/api/traffic/current');
        return await res.json();
    },

    fetchLatestPrediction: async () => {
        const res = await fetch('/api/predictions/latest');
        return await res.json();
    },

    fetchSessionHistory: async () => {
        const res = await fetch('/api/traffic/session-history');
        return await res.json();
    },

    fetchSensorStatus: async () => {
        const res = await fetch('/api/sensors/status');
        return await res.json();
    },

    getCameraStatus: async () => {
        const res = await fetch('/api/camera/status');
        return await res.json();
    },

    listVideos: async () => {
        const res = await fetch('/api/videos');
        return await res.json();
    },

    startCamera: async (videoFile, modelName = 'yolo26s.pt', conf = 0.25, imgsz = 960) => {
        const res = await fetch('/api/camera/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                video: videoFile,
                model: modelName,
                conf: parseFloat(conf),
                imgsz: parseInt(imgsz)
            })
        });
        return await res.json();
    },

    pauseCamera: async () => {
        const res = await fetch('/api/camera/pause', { method: 'POST' });
        return await res.json();
    },

    stopCamera: async () => {
        const res = await fetch('/api/camera/stop', { method: 'POST' });
        return await res.json();
    },

    configureLine: async (options) => {
        const res = await fetch('/api/camera/configure-line', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(options)
        });
        return await res.json();
    },

    uploadVideo: async (file) => {
        const formData = new FormData();
        formData.append('video', file);
        const res = await fetch('/api/upload-video', {
            method: 'POST',
            body: formData
        });
        return await res.json();
    },

    fetchBenchmark: async () => {
        const res = await fetch('/api/benchmark');
        return await res.json();
    }
};
