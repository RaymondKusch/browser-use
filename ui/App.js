import React, { useState } from 'react';
import AgentReasoning from './AgentReasoning';
import BrowserView from './BrowserView';
import MermaidDiagram from './MermaidDiagram';

const App = () => {
    const [instructions, setInstructions] = useState('');
    const [reasoning, setReasoning] = useState([]);
    const [browserUrl, setBrowserUrl] = useState('');
    const [mermaidDiagram, setMermaidDiagram] = useState('');

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

        // Example Mermaid diagram
        const diagram = `
            graph TD;
                A[Start] --> B[Process Instructions];
                B --> C[Action Sequence];
                C --> D[End];
        `;
        setMermaidDiagram(diagram);
    };

    return (
        <div className="app-container">
            <div className="left-panel">
                <textarea
                    value={instructions}
                    onChange={handleInstructionsChange}
                    placeholder="Enter instructions for the agent"
                />
                <button onClick={handleRunAgent}>Run Agent</button>
                <AgentReasoning reasoning={reasoning} />
                <MermaidDiagram diagram={mermaidDiagram} />
            </div>
            <div className="right-panel">
                <BrowserView url={browserUrl} />
            </div>
        </div>
    );
};

export default App;
