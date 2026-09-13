/**
 * RainSense Farmer - Chart.js Controllers for Rain History & Soil Moisture
 */

class RainSenseCharts {
  constructor() {
    this.rainChart = null;
    this.soilChart = null;
  }

  renderRainHistoryChart(canvasId, hourlyData = [], dailyData = []) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (this.rainChart) {
      this.rainChart.destroy();
    }

    const labels = hourlyData.map(h => {
      try {
        const d = new Date(h.time);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      } catch (e) {
        return h.time.slice(-5);
      }
    });

    const values = hourlyData.map(h => h.rainfall_mm || 0);

    // Compute cumulative sum
    let cum = 0;
    const cumulativeValues = values.map(v => {
      cum += v;
      return parseFloat(cum.toFixed(2));
    });

    this.rainChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            type: 'line',
            label: 'Cumulative Rainfall (mm)',
            data: cumulativeValues,
            borderColor: '#0284c7',
            backgroundColor: 'transparent',
            borderWidth: 2.5,
            pointRadius: 2,
            tension: 0.3,
            yAxisID: 'y1'
          },
          {
            type: 'bar',
            label: 'Hourly Rainfall (mm)',
            data: values,
            backgroundColor: '#10b981',
            borderRadius: 4,
            barPercentage: 0.6,
            yAxisID: 'y'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false
        },
        plugins: {
          legend: {
            position: 'top',
            labels: { boxWidth: 12, font: { family: 'Outfit, sans-serif', weight: '600' } }
          },
          tooltip: {
            padding: 10,
            cornerRadius: 8
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Hourly (mm)', font: { size: 11 } },
            grid: { color: '#f1f5f9' }
          },
          y1: {
            beginAtZero: true,
            position: 'right',
            title: { display: true, text: 'Cumulative (mm)', font: { size: 11 } },
            grid: { drawOnChartArea: false }
          },
          x: {
            grid: { display: false },
            ticks: { maxRotation: 45, minRotation: 0, font: { size: 10 } }
          }
        }
      }
    });
  }

  renderSoilMoistureChart(canvasId, trendData = []) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (this.soilChart) {
      this.soilChart.destroy();
    }

    const labels = trendData.map(d => {
      try {
        const dt = new Date(d.time);
        return dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      } catch (e) {
        return d.time.slice(-5);
      }
    });

    const surfaceVals = trendData.map(d => d.surface_pct || 40);
    const rootVals = trendData.map(d => d.root_pct || 45);

    this.soilChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Surface Moisture (0-3 cm) %',
            data: surfaceVals,
            borderColor: '#d97706',
            backgroundColor: 'rgba(217, 119, 6, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.35,
            pointRadius: 2
          },
          {
            label: 'Root Zone Moisture (3-9 cm) %',
            data: rootVals,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.35,
            pointRadius: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: { boxWidth: 12, font: { family: 'Outfit, sans-serif', weight: '600' } }
          }
        },
        scales: {
          y: {
            min: 0,
            max: 100,
            title: { display: true, text: 'Moisture Saturation (%)', font: { size: 11 } },
            grid: { color: '#f1f5f9' }
          },
          x: {
            grid: { display: false },
            ticks: { maxRotation: 45, font: { size: 10 } }
          }
        }
      }
    });
  }
}

window.rainCharts = new RainSenseCharts();
