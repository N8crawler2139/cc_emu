// Initialize the game when the page loads
window.addEventListener('load', () => {
    console.log('Crimson Eclipse - Initializing...');
    
    // Create the global game instance
    window.game = new GameEngine();
    
    console.log('Game engine initialized. Click START GAME to begin!');
});

// Handle window resize
window.addEventListener('resize', () => {
    if (window.game && window.game.canvas) {
        // You could implement dynamic canvas resizing here if needed
        // For now, we'll keep the fixed size
    }
});

// Handle visibility change (pause when tab is hidden)
document.addEventListener('visibilitychange', () => {
    if (window.game) {
        if (document.hidden) {
            // Tab is hidden - could pause the game here
            if (window.game.gameState === 'playing') {
                // For now, we'll let it continue running
                // You could implement pause functionality here
            }
        } else {
            // Tab is visible again
            if (window.game.gameState === 'playing') {
                // Reset the last time to prevent large delta jumps
                window.game.lastTime = performance.now();
            }
        }
    }
});

// Prevent context menu on right click (since we might use right click for abilities later)
document.addEventListener('contextmenu', (e) => {
    e.preventDefault();
});

// Prevent default behavior for arrow keys and WASD when game is active
document.addEventListener('keydown', (e) => {
    if (window.game && window.game.gameState === 'playing') {
        const preventKeys = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'KeyW', 'KeyA', 'KeyS', 'KeyD', 'Space'];
        if (preventKeys.includes(e.code)) {
            e.preventDefault();
        }
    }
});

// Debug information (remove in production)
if (typeof console !== 'undefined') {
    console.log('Crimson Eclipse - Debug Mode');
    console.log('Controls: WASD or Arrow Keys to move');
    console.log('Game will auto-fire at nearest enemies');
    console.log('Collect blue orbs for experience');
    console.log('Survive as long as possible!');
    
    // Add debug functions to window for testing
    window.debugGame = {
        addXP: (amount) => {
            if (window.game) {
                window.game.addXP(amount);
                console.log(`Added ${amount} XP`);
            }
        },
        
        setHealth: (amount) => {
            if (window.game) {
                window.game.stats.health = amount;
                console.log(`Set health to ${amount}`);
            }
        },
        
        levelUp: () => {
            if (window.game) {
                window.game.levelUp();
                console.log('Forced level up');
            }
        },
        
        spawnEnemy: (type = 'wraith') => {
            if (window.game && window.game.gameState === 'playing') {
                const enemy = new Enemy(window.game, 100, 100, type);
                window.game.addEntity(enemy);
                console.log(`Spawned ${type} enemy`);
            }
        },
        
        getStats: () => {
            if (window.game) {
                console.log('Game Stats:', window.game.stats);
                console.log('Entities:', window.game.entities.size);
            }
        }
    };
    
    console.log('Debug functions available: window.debugGame');
    console.log('  - addXP(amount)');
    console.log('  - setHealth(amount)');
    console.log('  - levelUp()');
    console.log('  - spawnEnemy(type)');
    console.log('  - getStats()');
}