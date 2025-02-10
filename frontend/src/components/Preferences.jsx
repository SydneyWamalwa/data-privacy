import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Preferences() {
  const [budget, setBudget] = useState([500, 1000]);
  const [interests, setInterests] = useState([]);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch('http://localhost:5001/api/save-preferences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': 'user_' + Math.random().toString(36).substr(2, 9)
        },
        body: JSON.stringify({
          prefs: {
            budget,
            interests
          }
        })
      });

      if (response.ok) {
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('Submission failed:', error);
    }
  };

  return (
    <div className="preferences-form">
      <h1>Set Your Preferences</h1>
      <form onSubmit={handleSubmit}>
        {/* Add form fields */}
        <button type="submit">Save Preferences</button>
      </form>
    </div>
  );
}