import React from 'react';

/**
 * BrowserView component that displays the browser view in an iframe.
 * @param {Object} props - The component props.
 * @param {string} props.url - The URL to display in the iframe.
 * @returns {JSX.Element} The BrowserView component.
 */
const BrowserView = ({ url }) => {
    return (
        <div className="browser-view">
            <iframe src={url} title="Browser View" width="100%" height="100%"></iframe>
        </div>
    );
};

export default BrowserView;
