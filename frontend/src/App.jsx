import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Preferences from './components/Preferences';
import Dashboard from './components/Dashboard';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Preferences />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  );
}