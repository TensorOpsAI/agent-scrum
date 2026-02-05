import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { KanbanBoard } from './components/board/KanbanBoard';
import { Layout } from './components/Layout';
import { useWebSocket } from './hooks/useWebSocket';

function AppContent() {
  // Initialize WebSocket connection
  useWebSocket();

  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<KanbanBoard />} />
      </Route>
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
