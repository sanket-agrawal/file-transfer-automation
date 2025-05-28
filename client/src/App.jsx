import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import axios from "axios";
import RemoteSelector from './components/RemoteSelector';

function App() {
   return (
    <div className="bg-gray-100 min-h-screen p-4">
      <RemoteSelector />
    </div>
  );
}

export default App
