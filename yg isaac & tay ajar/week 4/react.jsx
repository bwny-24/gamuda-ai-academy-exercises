import { useState } from 'react';

function SecretMessage() {
    // 1. Create a boolean state starting at false (hidden)
    const [isVisible, setIsVisible] = useState(false);

    return (
        <div style={{ padding: '20px' }}>
            {/* 2. When clicked, flip the state from true to false, or false to true */}
            <button onClick={() => setIsVisible(!isVisible)}>
                {isVisible ? 'Hide Secret' : 'Show Secret'}
            </button>

            {/* 3. If isVisible is true, show this paragraph */}
            {isVisible && <p>🎉 Surprised! You just unlocked your first React state!</p>}
        </div>
    );
}

export default SecretMessage;