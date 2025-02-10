// src/App.jsx
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Preferences from './components/Preferences';
import Dashboard from './components/Dashboard';
import Navigation from './components/Navigation'; // Optional navigation component

export default function App() {
  return (
    <BrowserRouter>
      {/* Optional navigation */}
      <Navigation />

      <Routes>
        <Route path="/" element={<Preferences />} />
        <Route path="/dashboard" element={<Dashboard />} />
        {/* Add error boundary for production */}
        <Route path="*" element={<div>404 Not Found</div>} />
      </Routes>
    </BrowserRouter>
  );
}