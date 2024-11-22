import React from 'react';

/**
 * AgentReasoning component that displays the agent's reasoning steps.
 * @param {Object} props - The component props.
 * @param {Array} props.reasoning - The reasoning steps to display.
 * @returns {JSX.Element} The AgentReasoning component.
 */
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
