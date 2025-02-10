import React, { useEffect, useState } from 'react';

export default function Dashboard() {
  const [segments, setSegments] = useState(null);

  useEffect(() => {
    const fetchSegments = async () => {
      try {
        const response = await fetch('http://backend:5000/api/segments');
        const data = await response.json();
        setSegments(data);
      } catch (error) {
        console.error('Failed to load segments:', error);
      }
    };
    fetchSegments();
  }, []);

  return (
    <div className="dashboard">
      <h2>Audience Segments</h2>
      {segments ? (
        <div className="segments-list">
          {segments.map((segment, index) => (
            <div key={index} className="segment-card">
              <h3>Segment #{index + 1}</h3>
              <p>Users: {segment.count}</p>
              <p>Average Budget: ${segment.avg_budget}</p>
            </div>
          ))}
        </div>
      ) : (
        <p>Loading segments...</p>
      )}
    </div>
  );
}