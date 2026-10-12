let trafficFlowChart = null;
let classDistChart = null;

function initCharts() {
    // 1. Direction A vs Direction B Time Series Chart
    const ctxFlow = document.getElementById('trafficFlowChart').getContext('2d');
    trafficFlowChart = new Chart(ctxFlow, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Direction A Crossings',
                    data: [],
                    borderColor: '#00d26a', // Bright Green
                    backgroundColor: 'rgba(0, 210, 106, 0.15)',
                    tension: 0.25,
                    borderWidth: 2,
                    fill: true
                },
                {
                    label: 'Direction B Crossings',
                    data: [],
                    borderColor: '#0dcaf0', // Bright Cyan
                    backgroundColor: 'rgba(13, 202, 240, 0.15)',
                    tension: 0.25,
                    borderWidth: 2,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: 'Source-Video Elapsed Time (seconds)', color: '#888' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#aaa', maxTicksLimit: 10 }
                },
                y: {
                    title: { display: true, text: 'Crossings / Window', color: '#888' },
                    beginAtZero: true,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#aaa', stepSize: 1 }
                }
            },
            plugins: {
                legend: {
                    labels: { color: '#ddd', font: { size: 11 } }
                }
            }
        }
    });

    // 2. Vehicle Class Distribution Doughnut Chart
    const ctxDist = document.getElementById('classDistChart').getContext('2d');
    classDistChart = new Chart(ctxDist, {
        type: 'doughnut',
        data: {
            labels: ['Cars', 'Motorcycles', 'Buses', 'Trucks', 'Bicycles'],
            datasets: [{
                data: [0, 0, 0, 0, 0],
                backgroundColor: [
                    '#3a86ff', // Car
                    '#ffbe0b', // Motorcycle
                    '#ff006e', // Bus
                    '#8338ec', // Truck
                    '#06d6a0'  // Bicycle
                ],
                borderWidth: 1,
                borderColor: '#111'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#ccc', font: { size: 10 }, boxWidth: 12 }
                }
            }
        }
    });
}

function updateTimeSeriesChart(historyWindows) {
    if (!trafficFlowChart || !historyWindows || historyWindows.length === 0) return;

    const labels = historyWindows.map(w => `${w.video_time_sec}s`);
    const dataA = historyWindows.map(w => w.dir_a);
    const dataB = historyWindows.map(w => w.dir_b);

    trafficFlowChart.data.labels = labels;
    trafficFlowChart.data.datasets[0].data = dataA;
    trafficFlowChart.data.datasets[1].data = dataB;
    trafficFlowChart.update('none'); // Update smoothly without full animation stutter
}

function updateClassDistChart(dirA, dirB) {
    if (!classDistChart) return;

    const totalCars = (dirA.car || 0) + (dirB.car || 0);
    const totalBikes = (dirA.motorcycle || 0) + (dirB.motorcycle || 0);
    const totalBuses = (dirA.bus || 0) + (dirB.bus || 0);
    const totalTrucks = (dirA.truck || 0) + (dirB.truck || 0);
    const totalBicycles = (dirA.bicycle || 0) + (dirB.bicycle || 0);

    classDistChart.data.datasets[0].data = [
        totalCars,
        totalBikes,
        totalBuses,
        totalTrucks,
        totalBicycles
    ];
    classDistChart.update('none');
}
