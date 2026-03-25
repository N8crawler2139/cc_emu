class StageSystem {
    constructor(game) {
        this.game = game;
        this.currentStage = 1;
        this.stageStartTime = 0;
        this.stageCompleted = false;
        
        // Define stages
        this.stages = {
            1: {
                name: "Crimson Fields",
                description: "The cursed grasslands under the eternal eclipse",
                backgroundColor: "#0d0d1a",
                surviveDuration: 300, // 5 minutes
                enemies: ['shadowWraith', 'bloodBat'],
                bosses: [],
                spawnRateMultiplier: 1.0,
                difficultyMultiplier: 1.0,
                reward: { soulEssence: 50 }
            },
            2: {
                name: "Bone Gardens",
                description: "Ancient cemetery where the dead refuse to rest",
                backgroundColor: "#1a0d1a",
                surviveDuration: 420, // 7 minutes
                enemies: ['shadowWraith', 'bloodBat', 'boneGolem'],
                bosses: [],
                spawnRateMultiplier: 1.2,
                difficultyMultiplier: 1.3,
                reward: { soulEssence: 75 }
            },
            3: {
                name: "Cultist Sanctum", 
                description: "Dark temple where fanatics worship the eclipse",
                backgroundColor: "#1a0d0d",
                surviveDuration: 480, // 8 minutes
                enemies: ['shadowWraith', 'bloodBat', 'boneGolem', 'eclipseCultist'],
                bosses: [],
                spawnRateMultiplier: 1.4,
                difficultyMultiplier: 1.6,
                reward: { soulEssence: 100 }
            },
            4: {
                name: "Elite Wraith Domain",
                description: "Realm of enhanced spirits and shadow lords",
                backgroundColor: "#0d1a0d",
                surviveDuration: 540, // 9 minutes  
                enemies: ['shadowWraith', 'bloodBat', 'boneGolem', 'eclipseCultist', 'eliteWraith'],
                bosses: [],
                spawnRateMultiplier: 1.6,
                difficultyMultiplier: 2.0,
                reward: { soulEssence: 150 }
            },
            5: {
                name: "Crimson Lord's Throne",
                description: "Face the ultimate master of the eternal eclipse",
                backgroundColor: "#1a0505",
                surviveDuration: 600, // 10 minutes or boss defeat
                enemies: ['shadowWraith', 'bloodBat', 'boneGolem', 'eclipseCultist', 'eliteWraith'],
                bosses: ['crimsonLord'],
                spawnRateMultiplier: 1.8,
                difficultyMultiplier: 2.5,
                reward: { soulEssence: 300 }
            },
            6: {
                name: "Nightmare Depths",
                description: "Descend into the abyss where nightmares take physical form",
                backgroundColor: "#050505",
                surviveDuration: 660, // 11 minutes
                enemies: ['shadowWraith', 'bloodBat', 'boneGolem', 'eclipseCultist', 'eliteWraith'],
                bosses: [],
                spawnRateMultiplier: 2.0,
                difficultyMultiplier: 3.0,
                reward: { soulEssence: 200 }
            },
            7: {
                name: "Void Sanctum",
                description: "Ancient temple floating in the endless void between realms",
                backgroundColor: "#1a001a",
                surviveDuration: 720, // 12 minutes
                enemies: ['shadowWraith', 'bloodBat', 'boneGolem', 'eclipseCultist', 'eliteWraith'],
                bosses: [],
                spawnRateMultiplier: 2.2,
                difficultyMultiplier: 3.5,
                reward: { soulEssence: 250 }
            },
            8: {
                name: "Eclipse's Heart",
                description: "The source of the eternal eclipse - face the true darkness",
                backgroundColor: "#2a0000",
                surviveDuration: 900, // 15 minutes or boss defeat
                enemies: ['shadowWraith', 'bloodBat', 'boneGolem', 'eclipseCultist', 'eliteWraith'],
                bosses: ['voidReaper'],
                spawnRateMultiplier: 2.5,
                difficultyMultiplier: 4.0,
                reward: { soulEssence: 500 },
                isFinalStage: true
            }
        };
        
        this.unlockedStages = 1;
        this.loadProgress();
    }
    
    getCurrentStage() {
        return this.stages[this.currentStage];
    }
    
    initializeStage(stageNumber) {
        if (stageNumber > this.unlockedStages) {
            console.log(`Stage ${stageNumber} is not unlocked yet`);
            return false;
        }
        
        this.currentStage = stageNumber;
        this.stageStartTime = this.game.gameTime;
        this.stageCompleted = false;
        
        const stage = this.getCurrentStage();
        
        // Set background color
        document.body.style.backgroundColor = stage.backgroundColor;
        
        // Apply stage modifiers to spawn system
        if (this.game.spawnSystem) {
            this.game.spawnSystem.setStageModifiers(stage.spawnRateMultiplier, stage.difficultyMultiplier);
            this.game.spawnSystem.setAllowedEnemies(stage.enemies);
            
            // Configure boss spawning if stage has bosses
            if (stage.bosses && stage.bosses.length > 0) {
                // Spawn boss at 80% of stage duration for survival stages
                // For boss stages, spawn earlier
                const bossSpawnTime = stage.bosses.includes('crimsonLord') || stage.bosses.includes('voidReaper') 
                    ? stage.surviveDuration * 0.3  // Spawn boss earlier for boss stages
                    : stage.surviveDuration * 0.8;  // Spawn boss near the end for regular stages
                this.game.spawnSystem.setStageBosses(stage.bosses, bossSpawnTime);
            } else {
                this.game.spawnSystem.setStageBosses([], 0);
            }
        }
        
        // Show stage introduction
        this.showStageIntroduction(stage);
        
        return true;
    }
    
    update() {
        if (this.stageCompleted) return;
        
        const stage = this.getCurrentStage();
        const timeInStage = this.game.gameTime - this.stageStartTime;
        
        // Check win condition: survive required duration
        if (timeInStage >= stage.surviveDuration) {
            this.completeStage();
            return;
        }
        
        // Check win condition: defeat all bosses (if any)
        if (stage.bosses && stage.bosses.length > 0) {
            const aliveBosses = this.game.getEntitiesByType('enemy').filter(enemy => 
                stage.bosses.includes(enemy.enemyType) && enemy.active
            );
            
            if (aliveBosses.length === 0 && timeInStage > 30) { // Give 30s grace period for boss to spawn
                this.completeStage();
                return;
            }
        }
    }
    
    completeStage() {
        this.stageCompleted = true;
        const stage = this.getCurrentStage();
        
        // Award soul essence
        if (stage.reward && stage.reward.soulEssence) {
            this.game.metaSystem.addSoulEssence(stage.reward.soulEssence, 'Stage Completion');
        }
        
        // Unlock next stage
        if (this.currentStage === this.unlockedStages && !stage.isFinalStage) {
            this.unlockedStages++;
            this.saveProgress();
        }
        
        // Show completion screen
        this.showStageComplete(stage);
    }
    
    showStageIntroduction(stage) {
        // Create stage intro overlay
        const intro = document.createElement('div');
        intro.id = 'stageIntro';
        intro.innerHTML = `
            <div class="stage-overlay">
                <div class="stage-content">
                    <h2>Stage ${this.currentStage}</h2>
                    <h3>${stage.name}</h3>
                    <p>${stage.description}</p>
                    <div class="stage-objective">
                        ${stage.bosses && stage.bosses.length > 0 ? 
                            'Defeat the boss to advance' : 
                            `Survive for ${Math.floor(stage.surviveDuration / 60)} minutes`
                        }
                    </div>
                    <button id="beginStageBtn">Begin</button>
                </div>
            </div>
        `;
        document.body.appendChild(intro);
        
        // Pause game until player is ready
        this.game.gameState = 'paused';
        
        document.getElementById('beginStageBtn').addEventListener('click', () => {
            document.body.removeChild(intro);
            this.game.gameState = 'playing';
        });
    }
    
    showStageComplete(stage) {
        // Create completion overlay
        const complete = document.createElement('div');
        complete.id = 'stageComplete';
        complete.innerHTML = `
            <div class="stage-overlay">
                <div class="stage-content">
                    <h2>Stage Complete!</h2>
                    <h3>${stage.name} Cleared</h3>
                    <div class="stage-rewards">
                        <p>+${stage.reward.soulEssence} Soul Essence</p>
                        ${this.currentStage === this.unlockedStages - 1 && !stage.isFinalStage ? 
                            '<p style="color: #44ff44;">New Stage Unlocked!</p>' : ''
                        }
                        ${stage.isFinalStage ? 
                            '<p style="color: #ffff44;">Congratulations! You have conquered the Crimson Eclipse!</p>' : ''
                        }
                    </div>
                    ${!stage.isFinalStage ? 
                        '<button id="nextStageBtn">Next Stage</button>' : ''
                    }
                    <button id="backToMenuBtn">Main Menu</button>
                </div>
            </div>
        `;
        document.body.appendChild(complete);
        
        // Pause game
        this.game.gameState = 'paused';
        
        // Event listeners
        const nextStageBtn = document.getElementById('nextStageBtn');
        if (nextStageBtn) {
            nextStageBtn.addEventListener('click', () => {
                document.body.removeChild(complete);
                if (this.currentStage + 1 <= Object.keys(this.stages).length) {
                    // Start fresh for the next stage
                    this.game.startNewStage(this.currentStage + 1);
                }
            });
        }
        
        document.getElementById('backToMenuBtn').addEventListener('click', () => {
            document.body.removeChild(complete);
            this.game.goToMainMenu();
        });
    }
    
    getStageProgress() {
        const stage = this.getCurrentStage();
        const timeInStage = Math.max(0, this.game.gameTime - this.stageStartTime);
        const progress = Math.min(timeInStage / stage.surviveDuration, 1.0);
        const timeRemaining = Math.max(0, stage.surviveDuration - timeInStage);
        
        return {
            progress: progress,
            timeRemaining: timeRemaining,
            isComplete: this.stageCompleted
        };
    }
    
    saveProgress() {
        localStorage.setItem('crimsonEclipse_unlockedStages', this.unlockedStages.toString());
    }
    
    loadProgress() {
        const saved = localStorage.getItem('crimsonEclipse_unlockedStages');
        if (saved) {
            this.unlockedStages = parseInt(saved);
        }
    }
    
    // Stage selection methods
    getUnlockedStages() {
        return this.unlockedStages;
    }
    
    getAllStages() {
        return this.stages;
    }
    
    resetProgress() {
        this.unlockedStages = 1;
        this.saveProgress();
    }
}