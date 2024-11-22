import React, { useEffect } from 'react';
import mermaid from 'mermaid';

const MermaidDiagram = ({ diagram }) => {
    useEffect(() => {
        mermaid.initialize({ startOnLoad: true });
        mermaid.contentLoaded();
    }, [diagram]);

    return (
        <div className="mermaid">
            {diagram}
        </div>
    );
};

export default MermaidDiagram;
