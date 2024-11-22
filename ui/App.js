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
        // Logic to run the agent and update reasoning, browserUrl, and mermaidDiagram
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
