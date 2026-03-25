class SpawnSystem {
    constructor(game) {
        this.game = game;
        this.reset();
    }
    
    reset() {
        this.timeSinceLastSpawn = 0;
        this.baseSpawnRate = 2.0; // seconds between spawns
        this.currentSpawnRate = this.baseSpawnRate;
        this.maxEnemies = 100;
        this.enemyTypes = ['wraith', 'bat', 'golem', 'cultist', 'elite_wraith'];
        this.allowedEnemies = ['wraith', 'bat']; // Stage-specific enemies
        this.waveTimer = 0;
        this.nextWaveTime = 30; // First wave at 30 seconds
        
        // Pickup spawning
        this.timeSinceLastPickup = 0;
        this.pickupSpawnRate = 15; // seconds between special pickups
        
        // Stage modifiers
        this.spawnRateMultiplier = 1.0;
        this.difficultyMultiplier = 1.0;
    }
    
    update(deltaTime) {
        this.timeSinceLastSpawn += deltaTime;
        this.waveTimer += deltaTime;
        this.timeSinceLastPickup += deltaTime;
        
        // Check for special waves
        if (this.waveTimer >= this.nextWaveTime) {
            this.spawnWave();
            this.waveTimer = 0;
            this.nextWaveTime = 30 + Math.random() * 20; // Next wave in 30-50 seconds
        }
        
        // Check for special pickup spawning
        if (this.timeSinceLastPickup >= this.pickupSpawnRate) {
            this.spawnSpecialPickup();
            this.timeSinceLastPickup = 0;
        }
        
        // Regular spawning
        this.updateSpawnRate();
        
        if (this.timeSinceLastSpawn >= this.currentSpawnRate) {
            this.spawnEnemy();
            this.timeSinceLastSpawn = 0;
        }
    }
    
    updateSpawnRate() {
        // Increase spawn rate over time
        const timeMultiplier = 1 + (this.game.gameTime / 60); // Increase every minute
        const enemyCount = this.game.getEntitiesByType('enemy').length;
        
        // Reduce spawn rate if too many enemies
        const enemyPressure = Math.max(0, 1 - (enemyCount / this.maxEnemies));
        
        // Apply stage modifiers
        const stageModifier = this.spawnRateMultiplier;
        
        this.currentSpawnRate = (this.baseSpawnRate / (timeMultiplier * stageModifier)) * (0.3 + enemyPressure * 0.7);
        
        // Minimum spawn rate
        this.currentSpawnRate = Math.max(this.currentSpawnRate, 0.1);
    }
    
    spawnEnemy() {
        const enemyCount = this.game.getEntitiesByType('enemy').length;
        if (enemyCount >= this.maxEnemies) return;
        
        const enemyType = this.selectEnemyType();
        const spawnPos = this.getSpawnPosition();
        
        const enemy = new Enemy(this.game, spawnPos.x, spawnPos.y, enemyType);
        this.game.addEntity(enemy);
    }
    
    selectEnemyType() {
        // Convert allowed enemies from stage system format to spawn system format
        const enemyMapping = {
            'shadowWraith': 'wraith',
            'bloodBat': 'bat', 
            'boneGolem': 'golem',
            'eclipseCultist': 'cultist',
            'eliteWraith': 'elite_wraith'
        };
        
        const availableTypes = this.allowedEnemies.map(enemy => 
            enemyMapping[enemy] || enemy
        ).filter(type => this.enemyTypes.includes(type));
        
        if (availableTypes.length === 0) {
            return 'wraith'; // Fallback
        }
        
        const gameTime = this.game.gameTime;
        
        // Weight distribution based on game time and available enemies
        if (availableTypes.includes('wraith') && gameTime < 60) {
            return Math.random() < 0.7 ? 'wraith' : this.getRandomEnemyType(availableTypes);
        }
        
        return this.getRandomEnemyType(availableTypes);
    }
    
    getRandomEnemyType(availableTypes) {
        return availableTypes[Math.floor(Math.random() * availableTypes.length)];
    }
    
    getSpawnPosition() {
        const canvas = this.game.canvas;
        const margin = 50;
        
        // Spawn off-screen around the edges
        const side = Math.floor(Math.random() * 4);
        let x, y;
        
        switch (side) {
            case 0: // Top
                x = Math.random() * canvas.width;
                y = -margin;
                break;
            case 1: // Right
                x = canvas.width + margin;
                y = Math.random() * canvas.height;
                break;
            case 2: // Bottom
                x = Math.random() * canvas.width;
                y = canvas.height + margin;
                break;
            case 3: // Left
                x = -margin;
                y = Math.random() * canvas.height;
                break;
        }
        
        return { x, y };
    }
    
    spawnWave() {
        const waveSize = 5 + Math.floor(this.game.gameTime / 30); // Larger waves over time
        const waveType = this.selectWaveType();
        
        for (let i = 0; i < waveSize; i++) {
            setTimeout(() => {
                const spawnPos = this.getWaveSpawnPosition(i, waveSize);
                const enemy = new Enemy(this.game, spawnPos.x, spawnPos.y, waveType);
                this.game.addEntity(enemy);
            }, i * 200); // Stagger spawns
        }
    }
    
    selectWaveType() {
        const gameTime = this.game.gameTime;
        
        if (gameTime < 60) {
            return Math.random() < 0.7 ? 'bat' : 'wraith';
        } else if (gameTime < 180) {
            const rand = Math.random();
            if (rand < 0.4) return 'bat';
            else if (rand < 0.7) return 'wraith';
            else return 'golem';
        } else {
            // Mixed waves in late game
            return this.selectEnemyType();
        }
    }
    
    getWaveSpawnPosition(index, waveSize) {
        const canvas = this.game.canvas;
        const margin = 100;
        
        // Spawn wave from one side
        const side = Math.floor(Math.random() * 4);
        let x, y;
        
        switch (side) {
            case 0: // Top
                x = (canvas.width / waveSize) * index + Math.random() * 50 - 25;
                y = -margin - Math.random() * 50;
                break;
            case 1: // Right
                x = canvas.width + margin + Math.random() * 50;
                y = (canvas.height / waveSize) * index + Math.random() * 50 - 25;
                break;
            case 2: // Bottom
                x = (canvas.width / waveSize) * index + Math.random() * 50 - 25;
                y = canvas.height + margin + Math.random() * 50;
                break;
            case 3: // Left
                x = -margin - Math.random() * 50;
                y = (canvas.height / waveSize) * index + Math.random() * 50 - 25;
                break;
        }
        
        return { x, y };
    }
    
    spawnSpecialPickup() {
        // Random chance for health vs powerup
        const isHealthPickup = Math.random() < 0.4; // 40% chance for health, 60% for powerup
        
        const spawnPos = this.getRandomMapPosition();
        
        if (isHealthPickup) {
            // Only spawn health if player needs it
            if (this.game.stats.health < this.game.stats.maxHealth * 0.8) {
                const healthValue = 25 + Math.random() * 25; // 25-50 health
                const pickup = new Pickup(this.game, spawnPos.x, spawnPos.y, 'health', healthValue);
                this.game.addEntity(pickup);
            }
        } else {
            // Spawn powerup
            const pickup = new Pickup(this.game, spawnPos.x, spawnPos.y, 'powerup', 1);
            this.game.addEntity(pickup);
        }
    }
    
    getRandomMapPosition() {
        const canvas = this.game.canvas;
        const margin = 100;
        
        // Spawn somewhere on the map, not too close to edges
        const x = margin + Math.random() * (canvas.width - 2 * margin);
        const y = margin + Math.random() * (canvas.height - 2 * margin);
        
        return { x, y };
    }
    
    // Stage system integration methods
    setStageModifiers(spawnRateMultiplier, difficultyMultiplier) {
        this.spawnRateMultiplier = spawnRateMultiplier;
        this.difficultyMultiplier = difficultyMultiplier;
    }
    
    setAllowedEnemies(allowedEnemies) {
        this.allowedEnemies = allowedEnemies;
    }
    
    getDifficultyMultiplier() {
        return this.difficultyMultiplier;
    }
}