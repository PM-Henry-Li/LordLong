import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/Layout/MainLayout';

import LabelManagement from './pages/LabelManagement';
import KnowledgeGraph from './pages/KnowledgeGraph';
import ConfigPanel from './pages/ConfigPanel';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/labels" replace />} />
          <Route path="labels" element={<LabelManagement />} />
          <Route path="knowledge-graph" element={<KnowledgeGraph />} />
          <Route path="config" element={<ConfigPanel />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
