import React, { useState } from 'react';
import ROMAnalysisDemo from './ROMAnalysisDemo'; // Your WebSocket component
import HttpPoseAnalysis from './HttpPoseAnalysis'; // New HTTP component

function App() {
  const [mode, setMode] = useState('http'); // 'websocket' or 'http'

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Mode Selector */}
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="max-w-7xl mx-auto flex items-center gap-4">
          <span className="text-white font-semibold">Connection Mode:</span>
          <button
            onClick={() => setMode('http')}
            className={`px-4 py-2 rounded-lg transition ${
              mode === 'http' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            HTTP (Recommended)
          </button>
          <button
            onClick={() => setMode('websocket')}
            className={`px-4 py-2 rounded-lg transition ${
              mode === 'websocket' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            WebSocket
          </button>
        </div>
      </div>

      {/* Component Display */}
      {mode === 'http' ? <HttpPoseAnalysis /> : <ROMAnalysisDemo />}
    </div>
  );
}

export default App;