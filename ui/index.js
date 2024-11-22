import React from 'react';
import { createRoot } from 'react-dom/client';
import mermaid from 'mermaid';
import App from './App';
import './styles.css';

// Initialize mermaid
mermaid.initialize({
  startOnLoad: true,
  theme: 'default',
  securityLevel: 'loose',
});

const container = document.getElementById('root');
const root = createRoot(container);
root.render(<App />);
