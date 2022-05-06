import React from 'react';
import './App.css';
import IdealGasScene from './components/scene/IdealGasScene';
import IdealGasSceneRefactor from './components/scene/IdealGasSceneRefactor';
import Wave2DScene from './components/scene/Wave2DScene';
import SPHScene from './components/scene/SPHScene';

function App() {
  return (
    <div className="App">
      <SPHScene />
    </div>
  );
}

export default App;
