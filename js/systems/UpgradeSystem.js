class UpgradeSystem {
    constructor(game) {
        this.game = game;
        this.upgradeMenu = document.getElementById('upgradeMenu');
        this.upgradeOptions = document.getElementById('upgradeOptions');
        
        // Define all possible upgrades
        this.upgrades = {
            // Weapon upgrades - enhance all your weapons
            damage: {
                name: 'Crimson Power',
                description: '[WEAPON] Increase all weapon damage by +5',
                effect: (player) => { 
                    // Apply to all weapons in multi-weapon system
                    if (player.weapons && player.weapons.length > 0) {
                        player.weapons.forEach(weapon => {
                            weapon.damage += 5;
                            weapon.baseDamage = (weapon.baseDamage || weapon.damage - 5) + 5; // Update base damage for fury calculations
                        });
                    }
                    // Also update legacy properties for compatibility
                    player.damage += 5;
                    player.baseDamage += 5; // Update base damage for fury calculations
                }
            },
            fireRate: {
                name: 'Rapid Fire',
                description: '[WEAPON] All weapons fire 15% faster',
                effect: (player) => { 
                    // Apply to all weapons in multi-weapon system
                    if (player.weapons && player.weapons.length > 0) {
                        player.weapons.forEach(weapon => {
                            weapon.fireRate = Math.max(weapon.fireRate * 0.85, 0.05);
                        });
                    }
                    // Also update legacy properties for compatibility
                    player.fireRate = Math.max(player.fireRate * 0.85, 0.05); 
                }
            },
            projectileSpeed: {
                name: 'Velocity Boost',
                description: '[WEAPON] All weapon projectiles fly 20% faster',
                effect: (player) => { 
                    // Apply to all weapons in multi-weapon system
                    if (player.weapons && player.weapons.length > 0) {
                        player.weapons.forEach(weapon => {
                            weapon.projectileSpeed *= 1.2;
                        });
                    }
                    // Also update legacy properties for compatibility
                    player.projectileSpeed *= 1.2; 
                }
            },
            projectileRange: {
                name: 'Long Shot',
                description: '[WEAPON] All weapon projectiles travel 50% further',
                effect: (player) => { 
                    // Apply to all weapons in multi-weapon system
                    if (player.weapons && player.weapons.length > 0) {
                        player.weapons.forEach(weapon => {
                            weapon.projectileRange *= 1.5;
                        });
                    }
                    // Also update legacy properties for compatibility
                    player.projectileRange *= 1.5; 
                }
            },
            multiShot: {
                name: 'Twin Bolts',
                description: '[WEAPON] All weapons fire one additional projectile',
                effect: (player) => { 
                    // Apply to all weapons in multi-weapon system
                    if (player.weapons && player.weapons.length > 0) {
                        player.weapons.forEach(weapon => {
                            weapon.multiShot = (weapon.multiShot || 1) + 1;
                            weapon.spreadAngle = weapon.spreadAngle || 0.2;
                        });
                    }
                    // Also update legacy properties for compatibility
                    player.multiShot = (player.multiShot || 1) + 1;
                    player.spreadAngle = player.spreadAngle || 0.2;
                }
            },
            
            // Player stat upgrades - improve your character
            health: {
                name: 'Vampire\'s Vigor',
                description: '[PASSIVE] Permanently increase max health by +25',
                effect: (player) => { 
                    player.game.stats.maxHealth += 25;
                    player.game.stats.health += 25;
                }
            },
            speed: {
                name: 'Shadow Step',
                description: '[PASSIVE] Permanently increase movement speed by 20%',
                effect: (player) => { player.speed *= 1.2; }
            },
            regeneration: {
                name: 'Blood Regeneration',
                description: '[PASSIVE] Slowly regenerate health over time',
                effect: (player) => { 
                    player.regeneration = (player.regeneration || 0) + 1;
                }
            },
            magnetism: {
                name: 'Soul Harvest',
                description: '[PASSIVE] Increase XP pickup range by 50%',
                effect: (player) => { 
                    player.magnetRange = (player.magnetRange || 50) * 1.5;
                }
            },
            
            // Special abilities - add new powers to all projectiles
            piercing: {
                name: 'Enhanced Piercing',
                description: '[SPECIAL] All projectiles pierce through 1 additional enemy',
                effect: (player) => { 
                    // Apply to all weapons in multi-weapon system
                    if (player.weapons && player.weapons.length > 0) {
                        player.weapons.forEach(weapon => {
                            weapon.piercing = (weapon.piercing || 0) + 1;
                        });
                    }
                    // Also update legacy properties for compatibility
                    player.piercing = (player.piercing || 0) + 1;
                }
            },
            explosive: {
                name: 'Eclipse Burst',
                description: '[SPECIAL] All projectiles explode on impact, damaging nearby enemies',
                effect: (player) => { 
                    // Apply to all weapons in multi-weapon system
                    if (player.weapons && player.weapons.length > 0) {
                        player.weapons.forEach(weapon => {
                            weapon.explosive = true;
                            weapon.explosionRadius = weapon.explosionRadius || 30;
                        });
                    }
                    // Also update legacy properties for compatibility
                    player.explosive = true;
                    player.explosionRadius = player.explosionRadius || 30;
                }
            },
            criticalHit: {
                name: 'Blood Frenzy',
                description: '[SPECIAL] 15% chance for projectiles to deal double damage',
                effect: (player) => { 
                    player.criticalChance = (player.criticalChance || 0) + 0.15;
                }
            },
            shield: {
                name: 'Eclipse Shield',
                description: '[PASSIVE] Recover from damage 25% faster',
                effect: (player) => { 
                    player.invulnerabilityTime *= 0.75;
                }
            },
            
            // New weapon unlocks
            bloodWhip: {
                name: 'Blood Whip',
                description: '[WEAPON] Add close-range sweeping weapon to your arsenal',
                effect: (player) => { 
                    const success = player.addWeapon('bloodWhip');
                    if (!success && player.weapons.length < player.maxWeapons) {
                        // Upgrade existing weapon instead if we couldn't add
                        player.upgradeWeapon(0, 'damage', 5);
                    }
                }
            },
            shadowBlade: {
                name: 'Shadow Blade', 
                description: '[WEAPON] Add fast piercing weapon to your arsenal',
                effect: (player) => {
                    const success = player.addWeapon('shadowBlade');
                    if (!success && player.weapons.length < player.maxWeapons) {
                        player.upgradeWeapon(0, 'damage', 5);
                    }
                }
            },
            eclipseOrb: {
                name: 'Eclipse Orb',
                description: '[WEAPON] Add explosive orb weapon to your arsenal', 
                effect: (player) => {
                    const success = player.addWeapon('eclipseOrb');
                    if (!success && player.weapons.length < player.maxWeapons) {
                        player.upgradeWeapon(0, 'damage', 5);
                    }
                }
            },
            voidScythe: {
                name: 'Void Scythe',
                description: '[WEAPON] Add returning scythe weapon to your arsenal',
                effect: (player) => {
                    const success = player.addWeapon('voidScythe');
                    if (!success && player.weapons.length < player.maxWeapons) {
                        player.upgradeWeapon(0, 'damage', 5);
                    }
                }
            },
            astralSpear: {
                name: 'Astral Spear',
                description: '[WEAPON] Add ethereal piercing spear that phases through walls',
                effect: (player) => {
                    const success = player.addWeapon('astralSpear');
                    if (!success && player.weapons.length < player.maxWeapons) {
                        player.upgradeWeapon(0, 'damage', 5);
                    }
                }
            },
            soulReaper: {
                name: 'Soul Reaper',
                description: '[WEAPON] Add soul-harvesting scythe that grows stronger with kills',
                effect: (player) => {
                    const success = player.addWeapon('soulReaper');
                    if (!success && player.weapons.length < player.maxWeapons) {
                        player.upgradeWeapon(0, 'damage', 5);
                    }
                }
            },
            temporalRifle: {
                name: 'Temporal Rifle',
                description: '[WEAPON] Add time-manipulating rifle that predicts enemy movement',
                effect: (player) => {
                    const success = player.addWeapon('temporalRifle');
                    if (!success && player.weapons.length < player.maxWeapons) {
                        player.upgradeWeapon(0, 'damage', 5);
                    }
                }
            },
            stormCaller: {
                name: 'Storm Caller',
                description: '[WEAPON] Add lightning weapon that chains to all nearby enemies',
                effect: (player) => {
                    const success = player.addWeapon('stormCaller');
                    if (!success && player.weapons.length < player.maxWeapons) {
                        player.upgradeWeapon(0, 'damage', 5);
                    }
                }
            },
            gravityWell: {
                name: 'Gravity Well',
                description: '[WEAPON] Add gravitational weapon that pulls enemies before exploding',
                effect: (player) => {
                    const success = player.addWeapon('gravityWell');
                    if (!success && player.weapons.length < player.maxWeapons) {
                        player.upgradeWeapon(0, 'damage', 5);
                    }
                }
            },

            // Advanced special abilities
            vampiric: {
                name: 'Crimson Drain',
                description: '10% chance to heal 1 HP on enemy kill',
                effect: (player) => { 
                    player.vampiric = (player.vampiric || 0) + 0.1;
                }
            },
            berserker: {
                name: 'Berserker Rage',
                description: 'Damage increases as health decreases',
                effect: (player) => { 
                    player.berserker = true;
                }
            },
            bouncing: {
                name: 'Ricochet Bolts',
                description: '[SPECIAL] All projectiles bounce off screen edges',
                effect: (player) => { 
                    // Apply to all weapons in multi-weapon system
                    if (player.weapons && player.weapons.length > 0) {
                        player.weapons.forEach(weapon => {
                            weapon.bouncing = true;
                        });
                    }
                    // Also update legacy properties for compatibility
                    player.bouncing = true;
                }
            },
            homing: {
                name: 'Seeking Missiles',
                description: '[SPECIAL] All projectiles track and curve toward nearby enemies, hitting targets around corners',
                effect: (player) => { 
                    // Apply to all weapons in multi-weapon system
                    if (player.weapons && player.weapons.length > 0) {
                        player.weapons.forEach(weapon => {
                            weapon.homing = true;
                        });
                    }
                    // Also update legacy properties for compatibility
                    player.homing = true;
                }
            },
            aura: {
                name: 'Death Aura',
                description: 'Damage nearby enemies over time',
                effect: (player) => { 
                    player.aura = (player.aura || 0) + 1;
                    player.auraRange = player.auraRange || 60;
                    player.auraDamage = player.auraDamage || 2;
                }
            },
            thorns: {
                name: 'Retribution',
                description: 'Reflect 50% damage back to attackers',
                effect: (player) => { 
                    player.thorns = (player.thorns || 0) + 0.5;
                }
            },
            freezing: {
                name: 'Frost Bolts',
                description: '[SPECIAL] All projectiles slow enemies by 30%',
                effect: (player) => { 
                    // Apply to all weapons in multi-weapon system
                    if (player.weapons && player.weapons.length > 0) {
                        player.weapons.forEach(weapon => {
                            weapon.freezing = true;
                            weapon.slowEffect = 0.3;
                        });
                    }
                    // Also update legacy properties for compatibility
                    player.freezing = true;
                    player.slowEffect = 0.3;
                }
            },
            chain: {
                name: 'Chain Lightning',
                description: '[SPECIAL] All projectiles jump to nearby enemies',
                effect: (player) => { 
                    // Apply to all weapons in multi-weapon system
                    if (player.weapons && player.weapons.length > 0) {
                        player.weapons.forEach(weapon => {
                            weapon.chain = (weapon.chain || 0) + 1;
                            weapon.chainRange = weapon.chainRange || 100;
                        });
                    }
                    // Also update legacy properties for compatibility
                    player.chain = (player.chain || 0) + 1;
                    player.chainRange = player.chainRange || 100;
                }
            },
            fury: {
                name: 'Blood Fury',
                description: 'Each kill increases damage for 5 seconds',
                effect: (player) => { 
                    player.fury = true;
                    player.furyStacks = player.furyStacks || 0;
                    player.furyDuration = player.furyDuration || 5;
                }
            },
            guardian: {
                name: 'Spirit Guardian',
                description: 'Summon a protective spirit that orbits you',
                effect: (player) => { 
                    player.guardians = (player.guardians || 0) + 1;
                }
            },
            phoenix: {
                name: 'Phoenix Feather',
                description: 'Revive with 50% health when killed (once per run)',
                effect: (player) => { 
                    if (!player.phoenix) {
                        player.phoenix = true;
                    }
                }
            },
            timeWarp: {
                name: 'Temporal Shift',
                description: 'Briefly slow time when health is low',
                effect: (player) => { 
                    player.timeWarp = true;
                }
            }
        };
    }
    
    showUpgradeMenu() {
        // Pause the game
        this.game.gameState = 'upgrading';
        
        // Use only the new multi-weapon upgrade system (disable old evolution system)
        const availableUpgrades = Object.keys(this.upgrades);
        const selectedUpgrades = this.getRandomUpgrades(availableUpgrades, 3);
        
        // Clear previous options
        this.upgradeOptions.innerHTML = '';
        
        // Create upgrade option elements
        selectedUpgrades.forEach((upgradeKey, index) => {
            const upgrade = this.upgrades[upgradeKey];
            const option = document.createElement('div');
            option.className = 'upgrade-option';
            option.innerHTML = `
                <div class="upgrade-title">${upgrade.name}</div>
                <div class="upgrade-description">${upgrade.description}</div>
            `;
            
            option.addEventListener('click', () => {
                this.selectUpgrade(upgradeKey);
            });
            
            // Add keyboard shortcuts (1, 2, 3)
            document.addEventListener('keydown', (e) => {
                if (e.code === `Digit${index + 1}`) {
                    this.selectUpgrade(upgradeKey);
                }
            }, { once: true });
            
            this.upgradeOptions.appendChild(option);
        });
        
        // Show the menu
        this.upgradeMenu.classList.remove('hidden');
    }
    
    getRandomUpgrades(availableUpgrades, count) {
        const player = this.game.player;
        let filteredUpgrades = [...availableUpgrades];
        
        // Filter out inappropriate upgrades based on current build
        if (player) {
            // Filter out weapons player already has or if at max weapons
            const hasWeapon = (weaponType) => player.weapons.some(w => w.type === weaponType);
            const atMaxWeapons = player.weapons.length >= player.maxWeapons;
            
            if (hasWeapon('bloodWhip') || atMaxWeapons) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'bloodWhip');
            }
            if (hasWeapon('shadowBlade') || atMaxWeapons) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'shadowBlade');
            }
            if (hasWeapon('eclipseOrb') || atMaxWeapons) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'eclipseOrb');
            }
            if (hasWeapon('voidScythe') || atMaxWeapons) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'voidScythe');
            }
            if (hasWeapon('astralSpear') || atMaxWeapons) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'astralSpear');
            }
            if (hasWeapon('soulReaper') || atMaxWeapons) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'soulReaper');
            }
            if (hasWeapon('temporalRifle') || atMaxWeapons) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'temporalRifle');
            }
            if (hasWeapon('stormCaller') || atMaxWeapons) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'stormCaller');
            }
            if (hasWeapon('gravityWell') || atMaxWeapons) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'gravityWell');
            }
            
            // Don't offer piercing upgrade if any weapon already has good piercing
            const hasGoodPiercing = player.weapons.some(w => w.piercing >= 2);
            if (hasGoodPiercing) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'piercing');
            }
            
            // Don't offer single-use upgrades if player already has them
            if (player.explosive) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'explosive');
            }
            
            if (player.phoenix) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'phoenix');
            }
            
            if (player.fury) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'fury');
            }
            
            if (player.homing) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'homing');
            }
            
            if (player.bouncing) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'bouncing');
            }
            
            if (player.freezing) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'freezing');
            }
            
            if (player.berserker) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'berserker');
            }
            
            if (player.timeWarp) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'timeWarp');
            }
            
            // Limit certain upgrades based on current stats
            if (player.criticalChance && player.criticalChance >= 0.3) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'criticalHit');
            }
            
            // Don't offer vampiric if already at max (100%)
            if (player.vampiric && player.vampiric >= 1.0) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'vampiric');
            }
            
            // Don't offer thorns if already at max (100%)
            if (player.thorns && player.thorns >= 1.0) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'thorns');
            }
            
            // Limit guardian count to reasonable max
            if (player.guardians && player.guardians >= 5) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'guardian');
            }
            
            // Limit aura stacking to reasonable max
            if (player.aura && player.aura >= 3) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'aura');
            }
            
            // Limit chain lightning stacking to reasonable max
            if (player.chain && player.chain >= 3) {
                filteredUpgrades = filteredUpgrades.filter(upgrade => upgrade !== 'chain');
            }
        }
        
        const shuffled = filteredUpgrades.sort(() => 0.5 - Math.random());
        return shuffled.slice(0, count);
    }
    
    selectUpgrade(upgradeKey) {
        // Use only the new multi-weapon upgrade system
        const upgrade = this.upgrades[upgradeKey];
        
        // Apply the upgrade effect to the player
        if (this.game.player && upgrade.effect) {
            upgrade.effect(this.game.player);
            
            // Track non-weapon upgrades for UI display
            const weaponUpgrades = ['crimsonBolt', 'bloodWhip', 'shadowBlade', 'eclipseOrb', 'voidScythe', 'astralSpear', 'soulReaper', 'temporalRifle', 'stormCaller', 'gravityWell'];
            if (!weaponUpgrades.includes(upgradeKey) && !this.game.player.collectedUpgrades.includes(upgradeKey)) {
                this.game.player.collectedUpgrades.push(upgradeKey);
            }
        }
        
        // Hide the menu
        this.upgradeMenu.classList.add('hidden');
        
        // Resume the game
        this.game.gameState = 'playing';
        
        // Visual feedback
        this.showUpgradeNotification(upgrade.name);
    }
    
    showUpgradeNotification(upgradeName) {
        // Create a temporary notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: absolute;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(255, 68, 68, 0.9);
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            font-weight: bold;
            z-index: 1000;
            animation: fadeInOut 3s ease;
        `;
        notification.textContent = `${upgradeName} Acquired!`;
        
        // Add CSS animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeInOut {
                0% { opacity: 0; transform: translateX(-50%) translateY(-20px); }
                20% { opacity: 1; transform: translateX(-50%) translateY(0); }
                80% { opacity: 1; transform: translateX(-50%) translateY(0); }
                100% { opacity: 0; transform: translateX(-50%) translateY(-20px); }
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(notification);
        
        // Remove after animation
        setTimeout(() => {
            document.body.removeChild(notification);
            document.head.removeChild(style);
        }, 3000);
    }
}