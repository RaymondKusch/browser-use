import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

const MermaidDiagram = ({ diagram }) => {
  const ref = useRef(null);

  useEffect(() => {
    if (diagram && ref.current) {
      // Clear previous diagram
      ref.current.innerHTML = '';

      // Render the diagram
      mermaid.mermaidAPI.render('mermaid-svg', diagram, (svgCode) => {
        ref.current.innerHTML = svgCode;
      });
    }
  }, [diagram]);

  return <div ref={ref} />;
};

export default MermaidDiagram;
