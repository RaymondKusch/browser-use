import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

const MermaidDiagram = ({ diagram }) => {
  const mermaidRef = useRef(null);
  const diagramId = useRef(`mermaid-${Math.random().toString(36).substr(2, 9)}`);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      mermaid.initialize({
        startOnLoad: true,
        theme: 'default',
        securityLevel: 'loose',
        logLevel: 'error',
        deterministicIds: true,
        fontFamily: 'monospace',
        htmlLabels: true,
        flowchart: {
          htmlLabels: true,
          useMaxWidth: true,
        }
      });
    }
  }, []);

  useEffect(() => {
    const renderDiagram = async () => {
      if (typeof window !== 'undefined' && diagram && mermaidRef.current) {
        try {
          // Clear previous content
          mermaidRef.current.innerHTML = '';
          
          // Generate new SVG
          const { svg } = await mermaid.render(diagramId.current, diagram);
          
          // Insert the SVG
          mermaidRef.current.innerHTML = svg;
        } catch (error) {
          console.error('Mermaid rendering failed:', error);
          // Fallback to displaying the diagram definition
          mermaidRef.current.innerHTML = `
            <pre style="color: red; background: #ffebee; padding: 10px; border-radius: 4px;">
              ${diagram}
            </pre>
          `;
        }
      }
    };

    renderDiagram();
  }, [diagram]);

  return (
    <div className="mermaid-container" style={{ width: '100%', overflow: 'auto' }}>
      <div ref={mermaidRef} className="mermaid" style={{ minHeight: '50px' }}></div>
    </div>
  );
};

export default MermaidDiagram;
