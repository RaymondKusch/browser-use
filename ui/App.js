import React, { useState, useEffect } from 'react';
import AgentReasoning from './AgentReasoning';
import BrowserView from './BrowserView';
import MermaidDiagram from './MermaidDiagram';

const App = () => {
    const [instructions, setInstructions] = useState('');
    const [reasoning, setReasoning] = useState([]);
    const [browserUrl, setBrowserUrl] = useState('');
    const [mermaidDiagram, setMermaidDiagram] = useState(`graph TD
    A[Start] --> B[Ready]`);
    const [diagramDefinition, setDiagramDefinition] = useState('');

    const handleInstructionsChange = (e) => {
        setInstructions(e.target.value);
    };

    const handleRunAgent = () => {
        // Simulate agent reasoning steps
        const reasoningSteps = [
            'Received instructions',
            'Parsed instructions',
            'Initiated action sequence',
            'Action sequence completed',
        ];
        setReasoning(reasoningSteps);

        // Generate Mermaid diagram based on reasoning steps
        const diagram = `
graph TD
    A[Start] --> B[Receive Instructions]
    B --> C[Parse Instructions]
    C --> D[Execute Actions]
    D --> E[Complete]
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style E fill:#9f9,stroke:#333,stroke-width:2px
`;
        setMermaidDiagram(diagram.trim());
    };

    // When you receive new agent output
    const handleAgentOutput = (output) => {
        // If the output contains a Mermaid diagram definition
        const cleanDefinition = output.trim().replace(/^graph TD/, 'graph TD\n  ');
        setDiagramDefinition(cleanDefinition);
    };

    return (
        <div className="app-container">
            <div className="left-panel">
                <div className="input-section">
                    <textarea
                        value={instructions}
                        onChange={handleInstructionsChange}
                        placeholder="Enter instructions for the agent"
                        className="instructions-input"
                    />
                    <button onClick={handleRunAgent} className="run-button">
                        Run Agent
                    </button>
                </div>
                <div className="reasoning-section">
                    <AgentReasoning reasoning={reasoning} />
                </div>
                <div className="diagram-section">
                    <MermaidDiagram diagram={mermaidDiagram} />
                </div>
            </div>
            <div className="right-panel">
                <BrowserView url={browserUrl} />
            </div>
            <div>
                <MermaidDiagram 
                    diagram={diagramDefinition || 'graph TD\n  A[Start] --> B[Ready]'} 
                />
            </div>
        </div>
    );
};

export default App;
