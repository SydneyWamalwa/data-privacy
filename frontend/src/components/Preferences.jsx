import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Preferences() {
  const [prefs, setPrefs] = useState({
    budget: [50, 500],
    interests: [],
    dataSharing: true
  });
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://backend:5000/api/save-preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(prefs)
      });
      if (response.ok) navigate('/dashboard');
    } catch (error) {
      console.error('Save failed:', error);
    }
  };

  return (
    <div className="preferences-form">
      <h2>Privacy Preferences</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Budget Range ($)</label>
          <input
            type="range"
            min="0"
            max="1000"
            value={prefs.budget[1]}
            onChange={(e) => setPrefs({...prefs, budget: [prefs.budget[0], e.target.value]})}
          />
          <div>${prefs.budget[0]} - ${prefs.budget[1]}</div>
        </div>

        <div className="form-group">
          <label>
            <input
              type="checkbox"
              checked={prefs.dataSharing}
              onChange={(e) => setPrefs({...prefs, dataSharing: e.target.checked})}
            />
            Share Anonymous Data
          </label>
        </div>

        <button type="submit">Save Preferences</button>
      </form>
    </div>
  );
}