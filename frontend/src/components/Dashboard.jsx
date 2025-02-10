// frontend/components/dashboard.jsx
import React, { useState, useEffect } from 'react';
import { Bar, Doughnut } from 'react-chartjs-2';
import Chart from 'chart.js/auto';
import '/frontend/static/style.css'
const Dashboard = () => {
  const [analyticsData, setAnalyticsData] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/segments');
        const data = await response.json();
        setAnalyticsData(data);
      } catch (error) {
        console.error('Error loading analytics:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 300000);
    return () => clearInterval(interval);
  }, []);

  if (!analyticsData) return <div>Loading analytics...</div>;

  return (
    <div className="dashboard-container">
      {/* Key Metrics */}
      <div className="metric-card">
        <h2>Total Customers</h2>
        <div className="metric-value">{analyticsData.participants}</div>
      </div>

      <div className="metric-card">
        <h2>Average Budget</h2>
        <div className="metric-value">
          ${analyticsData.stats.average_budget.toFixed(2)}
        </div>
      </div>

      {/* Segments Chart */}
      <div className="chart-card">
        <h3>Customer Segments</h3>
        <Bar
          data={{
            labels: analyticsData.segments.map((_, i) => `Group ${i + 1}`),
            datasets: [{
              label: 'Customers per Segment',
              data: analyticsData.segments.reduce((acc, seg) => {
                acc[seg] = (acc[seg] || 0) + 1;
                return acc;
              }, []),
              backgroundColor: ['#3498db', '#2ecc71', '#9b59b6', '#f1c40f', '#e74c3c']
            }]
          }}
        />
      </div>

      {/* Interests Chart */}
      <div className="chart-card">
        <h3>Interest Distribution</h3>
        <Doughnut
          data={{
            labels: ['Tech', 'Finance', 'Sports', 'Health', 'Education'],
            datasets: [{
              data: [
                analyticsData.stats.common_interests === 1 ? 40 : 0,
                analyticsData.stats.common_interests === 2 ? 40 : 0,
                // Add other interests...
              ],
              backgroundColor: ['#3498db', '#2ecc71', '#9b59b6', '#f1c40f', '#e74c3c']
            }]
          }}
        />
      </div>
    </div>
  );
};

export default Dashboard;