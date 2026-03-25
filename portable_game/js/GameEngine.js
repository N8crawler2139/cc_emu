class GameEngine {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.gameState = 'menu'; // menu, playing, paused, gameOver
        this.lastTime = 0;
        this.deltaTime = 0;
        this.gameTime = 0;
        
        // Game entities
        this.entities = new Map();
        this.entityIdCounter = 0;
        
        // Input tracking
        this.keys = {};
        this.mousePos = { x: 0, y: 0 };
        
        // Game stats
        this.stats = {
            level: 1,
            xp: 0,
            xpRequired: 200,
            health: 100,
            maxHealth: 100,
            kills: 0,
            time: 0
        };
        
        // Systems
        this.collisionSystem = null;
        this.renderSystem = null;
        this.spawnSystem = null;
        this.weaponSystem = null;
        this.upgradeSystem = null;
        this.metaSystem = null;
        this.stageSystem = null;
        this.hud = null;
        
        this.init();
    }
    
    init() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        
        // Initialize systems
        this.collisionSystem = new CollisionSystem(this);
        this.renderSystem = new RenderSystem(this);
        this.spawnSystem = new SpawnSystem(this);
        this.weaponSystem = new WeaponSystem(this);
        this.upgradeSystem = new UpgradeSystem(this);
        this.metaSystem = new MetaProgressionSystem(this);
        this.stageSystem = new StageSystem(this);
        this.hud = new HUD(this);
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Keyboard events
        document.addEventListener('keydown', (e) => {
            this.keys[e.code] = true;
            
            // Handle pause functionality
            if (e.code === 'KeyP' || e.code === 'Pause') {
                if (this.gameState === 'playing') {
                    this.pauseGame();
                } else if (this.gameState === 'paused') {
                    this.resumeGame();
                }
            }
            
            // Handle resume with Escape key when paused
            if (e.code === 'Escape' && this.gameState === 'paused') {
                this.resumeGame();
            }
            
            e.preventDefault();
        });
        
        document.addEventListener('keyup', (e) => {
            this.keys[e.code] = false;
            e.preventDefault();
        });
        
        // Mouse events
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            this.mousePos.x = e.clientX - rect.left;
            this.mousePos.y = e.clientY - rect.top;
        });
    }
    
    start(stageNumber = 1) {
        this.gameState = 'playing';
        this.resetGame();
        
        // Hide menu, show game
        document.getElementById('startMenu').classList.add('hidden');
        document.getElementById('gameCanvas').classList.remove('hidden');
        document.getElementById('gameUI').classList.remove('hidden');
        
        // Create player
        this.player = new Player(this, this.canvas.width / 2, this.canvas.height / 2);
        this.addEntity(this.player);
        
        // Apply selected character stats and abilities
        this.metaSystem.applyCharacterStats(this.player);
        
        // Apply permanent upgrades from meta progression
        this.metaSystem.applyPermanentUpgrades(this.player);
        
        // Initialize stage
        this.stageSystem.initializeStage(stageNumber);
        
        // Start game loop
        this.gameLoop();
    }
    
    resetGame() {
        this.entities.clear();
        this.entityIdCounter = 0;
        this.gameTime = 0;
        
        // Clear input state to prevent drift bug
        this.keys = {};
        
        this.stats = {
            level: 1,
            xp: 0,
            xpRequired: 200,
            health: 100,
            maxHealth: 100,
            kills: 0,
            time: 0
        };
        this.spawnSystem.reset();
    }
    
    gameLoop(currentTime = 0) {
        if (this.gameState !== 'playing' && this.gameState !== 'upgrading' && this.gameState !== 'paused') return;
        
        // Calculate delta time
        this.deltaTime = (currentTime - this.lastTime) / 1000;
        this.lastTime = currentTime;
        
        // Only update game time and entities when actually playing
        if (this.gameState === 'playing') {
            this.gameTime += this.deltaTime;
            this.stats.time = this.gameTime;
            
            // Update all entities
            this.update();
        }
        
        // Always render everything
        this.render();
        
        // Continue loop
        requestAnimationFrame((time) => this.gameLoop(time));
    }
    
    pauseGame() {
        this.gameState = 'paused';
        this.showPauseMenu();
    }
    
    resumeGame() {
        this.gameState = 'playing';
        this.hidePauseMenu();
    }
    
    showPauseMenu() {
        // Create pause overlay if it doesn't exist
        let pauseMenu = document.getElementById('pauseMenu');
        if (!pauseMenu) {
            pauseMenu = document.createElement('div');
            pauseMenu.id = 'pauseMenu';
            pauseMenu.innerHTML = `
                <div class="pause-overlay">
                    <div class="pause-content">
                        <h2>GAME PAUSED</h2>
                        <p>Press <strong>P</strong> or <strong>ESC</strong> to resume</p>
                        <button id="resumeBtn">Resume Game</button>
                        <button id="mainMenuBtn">Main Menu</button>
                    </div>
                </div>
            `;
            document.body.appendChild(pauseMenu);
            
            // Add event listeners
            document.getElementById('resumeBtn').addEventListener('click', () => {
                this.resumeGame();
            });
            
            document.getElementById('mainMenuBtn').addEventListener('click', () => {
                this.goToMainMenu();
            });
        }
        
        pauseMenu.classList.remove('hidden');
    }
    
    hidePauseMenu() {
        const pauseMenu = document.getElementById('pauseMenu');
        if (pauseMenu) {
            pauseMenu.classList.add('hidden');
        }
    }
    
    goToMainMenu() {
        this.gameState = 'menu';
        this.hidePauseMenu();
        
        // Hide game UI and show menu
        document.getElementById('gameCanvas').classList.add('hidden');
        document.getElementById('gameUI').classList.add('hidden');
        document.getElementById('startMenu').classList.remove('hidden');
        
        // Clear entities
        this.entities.clear();
    }
    
    update() {
        // Update all entities
        for (let [id, entity] of this.entities) {
            if (entity.active) {
                entity.update(this.deltaTime);
            } else {
                this.removeEntity(id);
            }
        }
        
        // Update systems
        this.spawnSystem.update(this.deltaTime);
        this.collisionSystem.update();
        this.stageSystem.update();
        this.renderSystem.updateExplosions(this.deltaTime);
        this.renderSystem.updateChainLightning(this.deltaTime);
        this.renderSystem.updateDamageNumbers(this.deltaTime);
        this.hud.update();
        
        // Check game over condition
        if (this.stats.health <= 0) {
            this.gameOver();
        }
    }
    
    render() {
        // Clear canvas
        this.ctx.fillStyle = '#0d0d1a';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Render all entities
        this.renderSystem.render();
    }
    
    addEntity(entity) {
        const id = this.entityIdCounter++;
        entity.id = id;
        this.entities.set(id, entity);
        return id;
    }
    
    removeEntity(id) {
        this.entities.delete(id);
    }
    
    getEntitiesByType(type) {
        return Array.from(this.entities.values()).filter(entity => entity.type === type);
    }
    
    addXP(amount) {
        // Apply XP bonus from meta progression
        const xpBonus = this.metaSystem.metaData.permanentUpgrades.xpBonus || 0;
        const multiplier = 1 + (xpBonus * 0.1);
        const finalAmount = Math.floor(amount * multiplier);
        
        this.stats.xp += finalAmount;
        
        // Check for level up
        if (this.stats.xp >= this.stats.xpRequired) {
            this.levelUp();
        }
    }
    
    levelUp() {
        this.stats.level++;
        this.stats.xp -= this.stats.xpRequired;
        this.stats.xpRequired = Math.floor(this.stats.xpRequired * 1.5);
        
        // Heal player on level up
        this.stats.health = Math.min(this.stats.health + 20, this.stats.maxHealth);
        
        // Show upgrade menu instead of automatic upgrades
        this.upgradeSystem.showUpgradeMenu();
    }
    
    takeDamage(amount) {
        this.stats.health = Math.max(0, this.stats.health - amount);
    }
    
    addKill() {
        this.stats.kills++;
    }
    
    gameOver() {
        this.gameState = 'gameOver';
        
        // Process meta progression
        const essenceGained = this.metaSystem.onGameEnd(this.stats);
        
        // Show enhanced game over screen
        const timeStr = `${Math.floor(this.stats.time / 60)}:${Math.floor(this.stats.time % 60).toString().padStart(2, '0')}`;
        alert(`Game Over!\nTime: ${timeStr} | Kills: ${this.stats.kills} | Level: ${this.stats.level}\n\n+${essenceGained} Soul Essence earned!\nTotal Essence: ${this.metaSystem.metaData.soulEssence}`);
        
        // Return to menu
        this.gameState = 'menu';
        document.getElementById('startMenu').classList.remove('hidden');
        document.getElementById('gameCanvas').classList.add('hidden');
        document.getElementById('gameUI').classList.add('hidden');
    }
    
    isKeyPressed(keyCode) {
        return !!this.keys[keyCode];
    }
    
    getMousePosition() {
        return { ...this.mousePos };
    }
}

// Global function for start button
function startGame() {
    if (window.game) {
        window.game.start();
    }
}

// Global function for meta progression button
function showMetaProgression() {
    if (window.game && window.game.metaSystem) {
        window.game.metaSystem.showMetaProgressionMenu();
    }
}

// Global function for character selection button
function showCharacterSelection() {
    if (window.game && window.game.metaSystem) {
        window.game.metaSystem.showCharacterSelection();
    }
}