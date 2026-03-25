class MetaProgressionSystem {
    constructor(game) {
        this.game = game;
        this.loadMetaProgress();
    }
    
    loadMetaProgress() {
        try {
            const saved = localStorage.getItem('crimsonEclipse_meta');
            if (saved) {
                this.metaData = JSON.parse(saved);
            } else {
                this.metaData = this.getDefaultMetaData();
            }
        } catch (e) {
            console.warn('Failed to load meta progression, using defaults');
            this.metaData = this.getDefaultMetaData();
        }
    }
    
    saveMetaProgress() {
        try {
            localStorage.setItem('crimsonEclipse_meta', JSON.stringify(this.metaData));
        } catch (e) {
            console.warn('Failed to save meta progression');
        }
    }
    
    getDefaultMetaData() {
        return {
            soulEssence: 0,
            totalRuns: 0,
            bestTime: 0,
            totalKills: 0,
            highestLevel: 1,
            permanentUpgrades: {
                startingHealth: 0,     // +10 health per level (max 5)
                startingDamage: 0,     // +2 damage per level (max 5)
                startingSpeed: 0,      // +10% speed per level (max 3)
                startingMagnetism: 0,  // +20 pickup range per level (max 3)
                xpBonus: 0,           // +10% XP gain per level (max 5)
                soulMultiplier: 0,    // +10% soul essence gain per level (max 5)
                startingFireRate: 0,  // +10% fire rate per level (max 3)
                startingLuck: 0,      // +5% crit chance per level (max 3)
                projectorRange: 0,    // +15% projectile range per level (max 3)
                startingRegen: 0,     // Start with regeneration per level (max 3)
                powerUpDuration: 0,   // +20% power-up duration per level (max 4)
                bossRewards: 0,       // +25% essence from bosses per level (max 3)
                multiWeaponMastery: 0,  // +1 max weapon slot per level (max 2, total 5 weapons)
                arcaneResonance: 0,     // Start with random weapon type (max 4 tiers)
                vampiricInstinct: 0,    // +15% vampiric healing chance per level (max 3)
                shadowEvasion: 0,       // +10% invulnerability reduction per level (max 3)
                explosiveMastery: 0,    // +20% explosion radius per level (max 3)
                chainReaction: 0,       // +1 max chain lightning jumps per level (max 2)
                soulHarvest: 0,         // +25% pickup range per level (max 4)
                berserkerRage: 0,       // Start with berserker upgrade (max 1)
                timeMastery: 0,         // +10% slower time in dangerous situations (max 2)
                criticalMastery: 0,     // +10% critical damage multiplier per level (max 3)
                weaponEvolution: 0      // Unlock weapon evolution trees earlier (max 2)
            },
            unlockedWeapons: ['crimsonBolt'], // Weapons unlocked for future runs
            unlockedCharacters: ['survivor'], // Characters unlocked for play
            selectedCharacter: 'survivor', // Currently selected character
            achievements: []
        };
    }
    
    calculateSoulEssenceGain(stats) {
        // Base essence from performance
        let essence = 0;
        
        // Essence from time survived (1 per 30 seconds)
        essence += Math.floor(stats.time / 30);
        
        // Essence from kills (1 per 10 kills)
        essence += Math.floor(stats.kills / 10);
        
        // Essence from level reached (2 per level after 5)
        if (stats.level > 5) {
            essence += (stats.level - 5) * 2;
        }
        
        // Apply soul multiplier
        const multiplier = 1 + (this.metaData.permanentUpgrades.soulMultiplier * 0.1);
        essence = Math.floor(essence * multiplier);
        
        return Math.max(1, essence); // Always get at least 1 essence
    }
    
    addSoulEssence(amount) {
        this.metaData.soulEssence += amount;
        this.saveMetaProgress();
    }
    
    canAffordUpgrade(upgradeType) {
        const cost = this.getUpgradeCost(upgradeType);
        return this.metaData.soulEssence >= cost;
    }
    
    getUpgradeCost(upgradeType) {
        const currentLevel = this.metaData.permanentUpgrades[upgradeType] || 0;
        const baseCosts = {
            startingHealth: 10,
            startingDamage: 15,
            startingSpeed: 20,
            startingMagnetism: 12,
            xpBonus: 18,
            soulMultiplier: 25,
            startingFireRate: 22,
            startingLuck: 30,
            projectorRange: 18,
            startingRegen: 35,
            powerUpDuration: 20,
            bossRewards: 40,
            multiWeaponMastery: 75,    // Expensive - allows up to 5 total weapons
            arcaneResonance: 50,       // Unlocks additional starting weapons
            vampiricInstinct: 45,      // Powerful vampiric healing boost
            shadowEvasion: 30,         // Survivability upgrade
            explosiveMastery: 35,      // Boosts all explosive effects
            chainReaction: 55,         // Enhances chain lightning
            soulHarvest: 25,          // Better pickup range
            berserkerRage: 100,       // One-time powerful upgrade
            timeMastery: 80,          // Rare time manipulation
            criticalMastery: 60,      // Critical damage enhancement
            weaponEvolution: 90       // Unlocks evolutions earlier
        };
        
        const baseCost = baseCosts[upgradeType] || 10;
        return baseCost + (currentLevel * baseCost * 0.5);
    }
    
    getMaxUpgradeLevel(upgradeType) {
        const maxLevels = {
            startingHealth: 5,
            startingDamage: 5,
            startingSpeed: 3,
            startingMagnetism: 3,
            xpBonus: 5,
            soulMultiplier: 5,
            startingFireRate: 3,
            startingLuck: 3,
            projectorRange: 3,
            startingRegen: 3,
            powerUpDuration: 4,
            bossRewards: 3,
            multiWeaponMastery: 2,   // +1 weapon slot per level (3, 4, 5 total)
            arcaneResonance: 4,      // 4 tiers of starting weapon variety
            vampiricInstinct: 3,     // Up to 45% vampiric healing chance
            shadowEvasion: 3,        // Significant invulnerability reduction
            explosiveMastery: 3,     // Major explosion radius boost
            chainReaction: 2,        // Up to 2 additional chain jumps
            soulHarvest: 4,          // Massive pickup range boost
            berserkerRage: 1,        // One-time unlock
            timeMastery: 2,          // 20% slower time when in danger
            criticalMastery: 3,      // Significant critical damage boost
            weaponEvolution: 2       // Earlier evolution access
        };
        return maxLevels[upgradeType] || 5;
    }
    
    purchaseUpgrade(upgradeType) {
        const cost = this.getUpgradeCost(upgradeType);
        const currentLevel = this.metaData.permanentUpgrades[upgradeType] || 0;
        const maxLevel = this.getMaxUpgradeLevel(upgradeType);
        
        if (this.canAffordUpgrade(upgradeType) && currentLevel < maxLevel) {
            this.metaData.soulEssence -= cost;
            this.metaData.permanentUpgrades[upgradeType] = currentLevel + 1;
            this.saveMetaProgress();
            return true;
        }
        return false;
    }
    
    applyPermanentUpgrades(player) {
        const upgrades = this.metaData.permanentUpgrades;
        
        // Apply starting bonuses
        if (upgrades.startingHealth > 0) {
            const bonus = upgrades.startingHealth * 10;
            this.game.stats.maxHealth += bonus;
            this.game.stats.health += bonus;
        }
        
        if (upgrades.startingDamage > 0) {
            player.damage += upgrades.startingDamage * 2;
        }
        
        if (upgrades.startingSpeed > 0) {
            player.speed *= (1 + upgrades.startingSpeed * 0.1);
        }
        
        if (upgrades.startingMagnetism > 0) {
            player.magnetRange = (player.magnetRange || 50) + (upgrades.startingMagnetism * 20);
        }
        
        if (upgrades.startingFireRate > 0) {
            player.fireRate *= Math.pow(0.9, upgrades.startingFireRate); // 10% faster per level
        }
        
        if (upgrades.startingLuck > 0) {
            player.criticalChance = (player.criticalChance || 0) + (upgrades.startingLuck * 0.05);
        }
        
        if (upgrades.projectorRange > 0) {
            player.projectileRange *= Math.pow(1.15, upgrades.projectorRange); // 15% more per level
        }
        
        if (upgrades.startingRegen > 0) {
            player.regeneration = (player.regeneration || 0) + upgrades.startingRegen;
        }
        
        // Apply new permanent upgrades
        if (upgrades.multiWeaponMastery > 0) {
            player.maxWeapons = 3 + upgrades.multiWeaponMastery; // Base 3, up to 5
        }
        
        if (upgrades.arcaneResonance > 0) {
            // Add additional starting weapons based on tier
            const startingWeapons = ['bloodWhip', 'shadowBlade', 'eclipseOrb', 'voidScythe'];
            for (let i = 0; i < Math.min(upgrades.arcaneResonance, startingWeapons.length); i++) {
                if (Math.random() < 0.7) { // 70% chance per tier
                    player.addWeapon(startingWeapons[i]);
                }
            }
        }
        
        if (upgrades.vampiricInstinct > 0) {
            player.vampiric = (player.vampiric || 0) + (upgrades.vampiricInstinct * 0.15);
        }
        
        if (upgrades.shadowEvasion > 0) {
            player.invulnerabilityTime *= Math.pow(0.9, upgrades.shadowEvasion); // 10% faster recovery per level
        }
        
        if (upgrades.explosiveMastery > 0) {
            // Apply to any weapon that gets explosive upgrade
            player.explosionRadiusMultiplier = 1 + (upgrades.explosiveMastery * 0.2);
        }
        
        if (upgrades.chainReaction > 0) {
            player.bonusChainJumps = upgrades.chainReaction;
        }
        
        if (upgrades.soulHarvest > 0) {
            player.magnetRange = (player.magnetRange || 50) + (upgrades.soulHarvest * 25);
        }
        
        if (upgrades.berserkerRage > 0) {
            player.berserker = true; // Start with berserker ability
        }
        
        if (upgrades.timeMastery > 0) {
            player.timeSlowMastery = upgrades.timeMastery * 0.1; // 10% slower time per level when in danger
        }
        
        if (upgrades.criticalMastery > 0) {
            player.criticalDamageMultiplier = 2 + (upgrades.criticalMastery * 0.1); // Base 2x, up to 2.3x
        }
        
        if (upgrades.weaponEvolution > 0) {
            player.evolutionLevelReduction = upgrades.weaponEvolution * 3; // Evolve 3/6 levels earlier
        }
    }
    
    onGameEnd(stats) {
        // Update meta statistics
        this.metaData.totalRuns++;
        this.metaData.totalKills += stats.kills;
        
        if (stats.time > this.metaData.bestTime) {
            this.metaData.bestTime = stats.time;
        }
        
        if (stats.level > this.metaData.highestLevel) {
            this.metaData.highestLevel = stats.level;
        }
        
        // Calculate and award soul essence
        const essenceGained = this.calculateSoulEssenceGain(stats);
        this.addSoulEssence(essenceGained);
        
        this.saveMetaProgress();
        
        return essenceGained;
    }
    
    getUpgradeDescription(upgradeType) {
        const descriptions = {
            startingHealth: 'Start with +10 max health',
            startingDamage: 'Start with +2 weapon damage',
            startingSpeed: 'Start with +10% movement speed',
            startingMagnetism: 'Start with +20 pickup range',
            xpBonus: 'Gain +10% more experience',
            soulMultiplier: 'Gain +10% more soul essence',
            startingFireRate: 'Start with +10% faster firing',
            startingLuck: 'Start with +5% critical hit chance',
            projectorRange: 'Start with +15% projectile range',
            startingRegen: 'Start with health regeneration',
            powerUpDuration: 'Power-ups last +20% longer',
            bossRewards: 'Gain +25% essence from bosses',
            multiWeaponMastery: 'Unlock additional weapon slots (+1 per level)',
            arcaneResonance: 'Start with additional random weapons',
            vampiricInstinct: 'Start with +15% vampiric healing chance',
            shadowEvasion: 'Reduce invulnerability time by 10%',
            explosiveMastery: 'Increase all explosion radius by 20%',
            chainReaction: 'Chain lightning jumps 1 more time',
            soulHarvest: 'Increase pickup range by 25',
            berserkerRage: 'Start with berserker ability unlocked',
            timeMastery: 'Slow time by 10% when in danger',
            criticalMastery: 'Increase critical damage multiplier by 10%',
            weaponEvolution: 'Unlock weapon evolutions 3 levels earlier'
        };
        return descriptions[upgradeType] || 'Unknown upgrade';
    }
    
    showMetaProgressionMenu() {
        // Create meta progression UI
        const metaMenu = document.createElement('div');
        metaMenu.id = 'metaMenu';
        metaMenu.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(13, 13, 26, 0.95);
            border: 3px solid #ff4444;
            padding: 30px;
            text-align: center;
            z-index: 300;
            border-radius: 10px;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            color: #ff4444;
            font-family: 'Courier New', monospace;
        `;
        
        metaMenu.innerHTML = `
            <h2>Soul Sanctum</h2>
            <p>Soul Essence: <span style="color: #ffaa44; font-weight: bold;">${this.metaData.soulEssence}</span></p>
            <p style="font-size: 12px; opacity: 0.8;">Permanent upgrades that persist between runs</p>
            <div id="upgradeList"></div>
            <button id="closeMetaMenu" style="
                background: rgba(255, 68, 68, 0.2);
                border: 2px solid #ff4444;
                color: #ff4444;
                padding: 10px 20px;
                font-size: 14px;
                font-family: inherit;
                cursor: pointer;
                margin-top: 20px;
                transition: all 0.3s ease;
            ">Close</button>
        `;
        
        const upgradeList = metaMenu.querySelector('#upgradeList');
        
        // Create upgrade options
        Object.keys(this.metaData.permanentUpgrades).forEach(upgradeType => {
            const currentLevel = this.metaData.permanentUpgrades[upgradeType];
            const maxLevel = this.getMaxUpgradeLevel(upgradeType);
            const cost = this.getUpgradeCost(upgradeType);
            const canAfford = this.canAffordUpgrade(upgradeType);
            const isMaxed = currentLevel >= maxLevel;
            
            const upgradeDiv = document.createElement('div');
            upgradeDiv.style.cssText = `
                background: rgba(255, 68, 68, 0.1);
                border: 1px solid #ff4444;
                margin: 10px 0;
                padding: 15px;
                border-radius: 5px;
                text-align: left;
            `;
            
            const statusText = isMaxed ? 'MAX' : `Cost: ${cost} essence`;
            const buttonDisabled = !canAfford || isMaxed;
            
            upgradeDiv.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: bold; margin-bottom: 5px;">
                            ${this.formatUpgradeName(upgradeType)} (${currentLevel}/${maxLevel})
                        </div>
                        <div style="font-size: 12px; opacity: 0.8;">
                            ${this.getUpgradeDescription(upgradeType)}
                        </div>
                    </div>
                    <button ${buttonDisabled ? 'disabled' : ''} 
                            onclick="window.game.metaSystem.purchaseUpgrade('${upgradeType}'); this.closest('#metaMenu').remove(); window.game.metaSystem.showMetaProgressionMenu();"
                            style="
                                background: ${buttonDisabled ? 'rgba(100, 100, 100, 0.3)' : 'rgba(255, 68, 68, 0.3)'};
                                border: 1px solid ${buttonDisabled ? '#666' : '#ff4444'};
                                color: ${buttonDisabled ? '#666' : '#ff4444'};
                                padding: 8px 15px;
                                font-size: 12px;
                                cursor: ${buttonDisabled ? 'not-allowed' : 'pointer'};
                                border-radius: 3px;
                            ">
                        ${statusText}
                    </button>
                </div>
            `;
            
            upgradeList.appendChild(upgradeDiv);
        });
        
        // Add close button functionality
        metaMenu.querySelector('#closeMetaMenu').onclick = () => {
            document.body.removeChild(metaMenu);
        };
        
        document.body.appendChild(metaMenu);
    }
    
    formatUpgradeName(upgradeType) {
        const names = {
            startingHealth: 'Vampire Vitality',
            startingDamage: 'Crimson Power',
            startingSpeed: 'Shadow Stride',
            startingMagnetism: 'Soul Attraction',
            xpBonus: 'Arcane Knowledge',
            soulMultiplier: 'Soul Resonance',
            startingFireRate: 'Rapid Reflexes',
            startingLuck: 'Fortune\'s Favor',
            projectorRange: 'Eagle Eye',
            startingRegen: 'Eternal Vigor',
            powerUpDuration: 'Essence Mastery',
            bossRewards: 'Soul Reaper',
            multiWeaponMastery: 'Multi-Weapon Mastery',
            arcaneResonance: 'Arcane Resonance',
            vampiricInstinct: 'Vampiric Instinct',
            shadowEvasion: 'Shadow Evasion',
            explosiveMastery: 'Explosive Mastery',
            chainReaction: 'Chain Reaction',
            soulHarvest: 'Soul Harvest',
            berserkerRage: 'Berserker Rage',
            timeMastery: 'Time Mastery',
            criticalMastery: 'Critical Mastery',
            weaponEvolution: 'Weapon Evolution'
        };
        return names[upgradeType] || upgradeType;
    }
    
    getAvailableCharacters() {
        return {
            survivor: {
                name: 'The Survivor',
                description: 'A balanced fighter who survived the first night of the crimson eclipse',
                unlockCost: 0, // Starting character - always unlocked
                startingWeapons: ['crimsonBolt'],
                startingStats: {
                    health: 100,
                    damage: 10,
                    speed: 150,
                    fireRate: 0.4,
                    criticalChance: 0,
                    regeneration: 0,
                    magnetRange: 50
                },
                specialAbility: 'None',
                color: '#ff4444'
            },
            
            berserker: {
                name: 'The Berserker',
                description: 'A fierce warrior who gets stronger as enemies fall around them',
                unlockCost: 150,
                startingWeapons: ['bloodWhip'],
                startingStats: {
                    health: 80, // Lower health
                    damage: 15, // Higher damage
                    speed: 160, // Slightly faster
                    fireRate: 0.5, // Slower fire rate
                    criticalChance: 0.1, // 10% crit chance
                    regeneration: 0,
                    magnetRange: 40 // Lower pickup range
                },
                specialAbility: 'Blood Fury - Start with Blood Fury ability unlocked',
                color: '#cc2222'
            },
            
            assassin: {
                name: 'The Shadow Assassin',
                description: 'A swift killer who strikes from the shadows with piercing attacks',
                unlockCost: 200,
                startingWeapons: ['shadowBlade'],
                startingStats: {
                    health: 75, // Lower health
                    damage: 8, // Lower damage
                    speed: 200, // Much faster
                    fireRate: 0.2, // Much faster fire rate
                    criticalChance: 0.15, // 15% crit chance
                    regeneration: 0,
                    magnetRange: 60 // Better pickup range
                },
                specialAbility: 'Shadow Step - Start with increased movement speed and piercing attacks',
                color: '#6622cc'
            },
            
            demolisher: {
                name: 'The Demolisher',
                description: 'A heavy weapons expert who specializes in explosive devastation',
                unlockCost: 250,
                startingWeapons: ['eclipseOrb'],
                startingStats: {
                    health: 120, // Higher health
                    damage: 20, // Much higher damage
                    speed: 120, // Slower movement
                    fireRate: 0.8, // Slower fire rate
                    criticalChance: 0,
                    regeneration: 0,
                    magnetRange: 45
                },
                specialAbility: 'Explosive Expert - Start with Eclipse Burst ability and larger explosion radius',
                color: '#cc4422'
            },
            
            reaper: {
                name: 'The Soul Reaper',
                description: 'A dark mystic who commands void scythes and returns from the brink of death',
                unlockCost: 300,
                startingWeapons: ['voidScythe'],
                startingStats: {
                    health: 90,
                    damage: 18, // High damage
                    speed: 140, // Slightly slower
                    fireRate: 0.4,
                    criticalChance: 0.05,
                    regeneration: 1, // Start with regeneration
                    magnetRange: 70 // Better pickup range
                },
                specialAbility: 'Phoenix Feather - Start with one revival and returning projectiles',
                color: '#442266'
            },
            
            templar: {
                name: 'The Templar',
                description: 'A holy warrior with incredible resilience and healing abilities',
                unlockCost: 180,
                startingWeapons: ['crimsonBolt'],
                startingStats: {
                    health: 150, // Much higher health
                    damage: 8, // Lower damage
                    speed: 130, // Slower movement
                    fireRate: 0.6, // Slower fire rate
                    criticalChance: 0,
                    regeneration: 2, // Strong regeneration
                    magnetRange: 80 // Best pickup range
                },
                specialAbility: 'Divine Vigor - Start with strong health regeneration and extra health',
                color: '#ffaa44'
            }
        };
    }
    
    canUnlockCharacter(characterId) {
        const characters = this.getAvailableCharacters();
        const character = characters[characterId];
        if (!character) return false;
        
        return this.metaData.soulEssence >= character.unlockCost && 
               !this.metaData.unlockedCharacters.includes(characterId);
    }
    
    unlockCharacter(characterId) {
        const characters = this.getAvailableCharacters();
        const character = characters[characterId];
        if (!character || !this.canUnlockCharacter(characterId)) return false;
        
        this.metaData.soulEssence -= character.unlockCost;
        this.metaData.unlockedCharacters.push(characterId);
        this.saveMetaProgress();
        return true;
    }
    
    selectCharacter(characterId) {
        if (this.metaData.unlockedCharacters.includes(characterId)) {
            this.metaData.selectedCharacter = characterId;
            this.saveMetaProgress();
            return true;
        }
        return false;
    }
    
    getSelectedCharacter() {
        const characters = this.getAvailableCharacters();
        return characters[this.metaData.selectedCharacter] || characters['survivor'];
    }
    
    showCharacterSelection() {
        // Create character selection UI
        const charMenu = document.createElement('div');
        charMenu.id = 'characterMenu';
        charMenu.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(13, 13, 26, 0.95);
            border: 3px solid #ff4444;
            padding: 30px;
            text-align: center;
            z-index: 300;
            border-radius: 10px;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
            color: #ff4444;
            font-family: 'Courier New', monospace;
        `;
        
        charMenu.innerHTML = `
            <h2>Character Selection</h2>
            <p>Soul Essence: <span style="color: #ffaa44; font-weight: bold;">${this.metaData.soulEssence}</span></p>
            <p style="font-size: 12px; opacity: 0.8;">Choose your character for the next run</p>
            <div id="characterList" style="display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; margin: 20px 0;"></div>
            <button id="closeCharacterMenu" style="
                background: rgba(255, 68, 68, 0.2);
                border: 2px solid #ff4444;
                color: #ff4444;
                padding: 10px 20px;
                font-size: 14px;
                font-family: inherit;
                cursor: pointer;
                margin-top: 20px;
                transition: all 0.3s ease;
            ">Close</button>
        `;
        
        const characterList = charMenu.querySelector('#characterList');
        const characters = this.getAvailableCharacters();
        
        Object.keys(characters).forEach(characterId => {
            const character = characters[characterId];
            const isUnlocked = this.metaData.unlockedCharacters.includes(characterId);
            const isSelected = this.metaData.selectedCharacter === characterId;
            const canUnlock = this.canUnlockCharacter(characterId);
            
            const characterDiv = document.createElement('div');
            characterDiv.style.cssText = `
                background: ${isSelected ? 'rgba(255, 68, 68, 0.3)' : 'rgba(255, 68, 68, 0.1)'};
                border: ${isSelected ? '3px solid #ff4444' : '1px solid #ff4444'};
                padding: 15px;
                border-radius: 8px;
                width: 220px;
                text-align: left;
                cursor: ${isUnlocked ? 'pointer' : 'default'};
                opacity: ${isUnlocked ? '1' : '0.6'};
            `;
            
            const statusText = isUnlocked ? 
                (isSelected ? 'SELECTED' : 'UNLOCKED') : 
                (canUnlock ? `UNLOCK: ${character.unlockCost}` : `LOCKED: ${character.unlockCost}`);
            
            characterDiv.innerHTML = `
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <div style="width: 20px; height: 20px; background: ${character.color}; border-radius: 50%; margin-right: 10px;"></div>
                    <div style="font-weight: bold; font-size: 14px;">${character.name}</div>
                </div>
                <div style="font-size: 11px; opacity: 0.8; margin-bottom: 8px; line-height: 1.3;">
                    ${character.description}
                </div>
                <div style="font-size: 10px; margin-bottom: 8px;">
                    <div style="color: #ffaa44;">HP: ${character.startingStats.health} | DMG: ${character.startingStats.damage} | SPD: ${character.startingStats.speed}</div>
                    <div style="color: #aaaaaa; margin-top: 2px;">Weapon: ${character.startingWeapons[0]}</div>
                </div>
                <div style="font-size: 9px; color: #88ff88; margin-bottom: 10px; line-height: 1.2;">
                    ${character.specialAbility}
                </div>
                <div style="text-align: center;">
                    <button onclick="window.game.metaSystem.${isUnlocked ? 'selectCharacter' : (canUnlock ? 'unlockCharacter' : '')}('${characterId}'); this.closest('#characterMenu').remove(); window.game.metaSystem.showCharacterSelection();"
                            ${(!isUnlocked && !canUnlock) ? 'disabled' : ''}
                            style="
                                background: ${isSelected ? 'rgba(68, 255, 68, 0.3)' : (isUnlocked ? 'rgba(255, 68, 68, 0.3)' : (canUnlock ? 'rgba(255, 255, 68, 0.3)' : 'rgba(100, 100, 100, 0.3)'))};
                                border: 1px solid ${isSelected ? '#44ff44' : (isUnlocked ? '#ff4444' : (canUnlock ? '#ffff44' : '#666'))};
                                color: ${isSelected ? '#44ff44' : (isUnlocked ? '#ff4444' : (canUnlock ? '#ffff44' : '#666'))};
                                padding: 6px 12px;
                                font-size: 10px;
                                cursor: ${(!isUnlocked && !canUnlock) ? 'not-allowed' : 'pointer'};
                                border-radius: 3px;
                                width: 100%;
                            ">
                        ${statusText}
                    </button>
                </div>
            `;
            
            characterList.appendChild(characterDiv);
        });
        
        // Add close button functionality
        charMenu.querySelector('#closeCharacterMenu').onclick = () => {
            document.body.removeChild(charMenu);
        };
        
        document.body.appendChild(charMenu);
    }
    
    applyCharacterStats(player) {
        const selectedCharacter = this.getSelectedCharacter();
        
        // Apply character starting stats
        const stats = selectedCharacter.startingStats;
        player.damage = stats.damage;
        player.baseDamage = stats.damage; // For fury calculations
        player.speed = stats.speed;
        player.fireRate = stats.fireRate;
        player.projectileRange = 300; // Default range
        player.criticalChance = stats.criticalChance;
        player.regeneration = stats.regeneration;
        player.magnetRange = stats.magnetRange;
        player.color = selectedCharacter.color;
        
        // Apply character starting weapons
        if (selectedCharacter.startingWeapons && selectedCharacter.startingWeapons.length > 0) {
            // Clear default weapon and add character weapon
            player.weapons = [];
            selectedCharacter.startingWeapons.forEach(weaponType => {
                player.addWeapon(weaponType);
            });
        }
        
        // Apply special abilities based on character
        const characterId = this.metaData.selectedCharacter;
        switch (characterId) {
            case 'berserker':
                player.fury = true; // Start with Blood Fury ability
                break;
                
            case 'assassin':
                // Start with piercing attacks - apply to all weapons
                player.weapons.forEach(weapon => {
                    weapon.piercing = Math.max(weapon.piercing || 0, 2);
                });
                break;
                
            case 'demolisher':
                // Start with explosive attacks
                player.weapons.forEach(weapon => {
                    weapon.explosive = true;
                    weapon.explosionRadius = (weapon.explosionRadius || 30) + 10; // Larger explosions
                });
                break;
                
            case 'reaper':
                // Start with returning projectiles and one revival
                player.weapons.forEach(weapon => {
                    weapon.returning = true;
                });
                player.phoenixFeather = 1; // One revival
                break;
                
            case 'templar':
                // Already has strong regeneration from stats, no additional special abilities needed
                break;
        }
        
        // Update health after all other stats are applied
        this.game.stats.health = stats.health;
        this.game.stats.maxHealth = stats.health;
    }
}