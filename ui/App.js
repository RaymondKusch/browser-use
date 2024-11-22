import React, { useState, useEffect } from 'react';
import AgentReasoning from './AgentReasoning';
import BrowserView from './BrowserView';
import MermaidDiagram from './MermaidDiagram';

/**
 * Main App component that manages the state and interactions.
 */
const App = () => {
    const [instructions, setInstructions] = useState('');
    const [reasoning, setReasoning] = useState([]);
    const [browserUrl, setBrowserUrl] = useState('');
    const [mermaidDiagram, setMermaidDiagram] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    /**
     * Handle change in instructions input.
     * @param {Event} e - The input change event.
     */
    const handleInstructionsChange = (e) => {
        setInstructions(e.target.value);
    };

    /**
     * Handle running the agent with the provided instructions.
     */
    const handleRunAgent = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await fetch('/api/run-task', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ task: instructions }),
            });

            if (!response.ok) {
                throw new Error('Failed to run task');
            }

            const data = await response.json();
            
            // Update reasoning steps
            const steps = data.steps.map(step => 
                step.extracted_content || step.error || 'Processing...'
            );
            setReasoning(steps);

            // Update mermaid diagram
            setMermaidDiagram(data.mermaid_diagram);

        } catch (err) {
            setError(err.message);
            console.error('Error running task:', err);
        } finally {
            setIsLoading(false);
        }
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
                        disabled={isLoading}
                    />
                    <button 
                        onClick={handleRunAgent} 
                        className="run-button"
                        disabled={isLoading || !instructions.trim()}
                    >
                        {isLoading ? 'Running...' : 'Run Agent'}
                    </button>
                </div>
                {error && (
                    <div className="error-message">
                        {error}
                    </div>
                )}
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
        </div>
    );
};

export default App;
