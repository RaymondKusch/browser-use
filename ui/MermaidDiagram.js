import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

const MermaidDiagram = ({ diagram }) => {
  const mermaidRef = useRef(null);

  useEffect(() => {
    // Check if window is defined (we're in a browser environment)
    if (typeof window !== 'undefined') {
      mermaid.initialize({
        startOnLoad: false,
        theme: 'default',
        securityLevel: 'loose',
        logLevel: 'error',
        // Add SSR configuration
        startOnLoad: true,
        ssr: true
      });
    }
  }, []);

  useEffect(() => {
    // Only run if we're in browser environment and have both diagram and ref
    if (typeof window !== 'undefined' && diagram && mermaidRef.current) {
      try {
        // Clear previous content
        mermaidRef.current.innerHTML = diagram;
        
        // Use async render
        mermaid.run({
          nodes: [mermaidRef.current],
          suppressErrors: true
        }).catch(error => {
          console.error('Mermaid rendering failed:', error);
        });
      } catch (error) {
        console.error('Mermaid rendering failed:', error);
      }
    }
  }, [diagram]);

  return (
    <div className="mermaid-container">
      <div ref={mermaidRef} className="mermaid">
        {diagram}
      </div>
    </div>
  );
};

export default MermaidDiagram;