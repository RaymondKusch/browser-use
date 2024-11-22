import React from 'react';

const AgentReasoning = ({ reasoning }) => {
    return (
        <div className="agent-reasoning">
            <h2>Agent Reasoning</h2>
            <ul>
                {reasoning.map((step, index) => (
                    <li key={index}>{step}</li>
                ))}
            </ul>
        </div>
    );
};

export default AgentReasoning;
