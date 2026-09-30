import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';

import Header from './components/Header';
import Home from './pages/Home';
import Client from './pages/Client';
import AddClient from './pages/AddClient';
import EditClient from './pages/EditClient';
import Convention from './pages/Convention';
import Analyses from './pages/Analyses';
import Settings from './pages/Settings';
import Logs from './pages/Logs';
import AuditReport from './pages/AuditReport';

export default function App() {
  return (
    <Router>
      <div className="app-shell">
        <Header />

        {/* Routage vers les différentes pages du projet. */}
        <div className="page-container">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/home" element={<Home />} />
            <Route path="/client" element={<Client />} />
            <Route path="/client/add" element={<AddClient />} />
            <Route path="/client/edit" element={<EditClient />} />
            <Route path="/client/:auditId/convention" element={<Convention />} />
            <Route path="/client/:auditId/analyses" element={<Analyses />} />
            <Route path="/client/:auditId/settings" element={<Settings />} />
            <Route path="/client/:auditId/logs" element={<Logs />} />
            <Route path="/client/:auditId/audit" element={<AuditReport />} />
          </Routes>
        </div>

        <ToastContainer />
      </div>
    </Router>
  );
}
