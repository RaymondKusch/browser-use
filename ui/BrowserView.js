import React from 'react';

const BrowserView = ({ url }) => {
    return (
        <div className="browser-view">
            <iframe src={url} title="Browser View" width="100%" height="100%"></iframe>
        </div>
    );
};

export default BrowserView;
