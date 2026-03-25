class WeaponSystem {
    constructor(game) {
        this.game = game;
        
        // Define weapon types
        this.weaponTypes = {
            crimsonBolt: {
                name: 'Crimson Bolt',
                description: 'Basic red energy projectiles',
                projectileType: 'bolt',
                damage: 10,
                fireRate: 0.4,
                projectileSpeed: 400,
                range: 300,
                multiShot: 1,
                spreadAngle: 0,
                color: '#ff4444'
            },
            
            bloodWhip: {
                name: 'Blood Whip',
                description: 'Close-range sweeping attack',
                projectileType: 'whip',
                damage: 15,
                fireRate: 0.6,
                projectileSpeed: 0, // Doesn't move
                range: 80,
                multiShot: 1,
                spreadAngle: 0.5, // Wide sweep
                color: '#cc2222'
            },
            
            shadowBlade: {
                name: 'Shadow Blade',
                description: 'Fast piercing projectiles',
                projectileType: 'blade',
                damage: 8,
                fireRate: 0.2,
                projectileSpeed: 600,
                range: 250,
                multiShot: 1,
                spreadAngle: 0,
                piercing: 2,
                color: '#6622cc'
            },
            
            eclipseOrb: {
                name: 'Eclipse Orb',
                description: 'Slow but explosive projectiles',
                projectileType: 'orb',
                damage: 20,
                fireRate: 0.8,
                projectileSpeed: 200,
                range: 350,
                multiShot: 1,
                spreadAngle: 0,
                explosive: true,
                explosionRadius: 40,
                color: '#cc4422'
            },
            
            voidScythe: {
                name: 'Void Scythe',
                description: 'Spinning projectiles that return and pierce',
                projectileType: 'scythe',
                damage: 18,
                fireRate: 0.4,
                projectileSpeed: 400,
                range: 250,
                multiShot: 1,
                spreadAngle: 0,
                returning: true,
                piercing: 3,
                color: '#442266'
            },
            
            // ULTIMATE WEAPONS
            crimsonDestroyer: {
                name: 'Crimson Destroyer',
                description: 'Ultimate energy weapon with explosive bursts',
                projectileType: 'destroyer',
                damage: 25,
                fireRate: 0.3,
                projectileSpeed: 500,
                range: 400,
                multiShot: 3,
                spreadAngle: 0.3,
                piercing: 2,
                explosive: true,
                explosionRadius: 50,
                color: '#ff0000'
            },
            
            voidReaper: {
                name: 'Void Reaper',
                description: 'Ultimate scythe that dominates the battlefield',
                projectileType: 'reaper',
                damage: 30,
                fireRate: 0.35,
                projectileSpeed: 450,
                range: 300,
                multiShot: 2,
                spreadAngle: 0.4,
                returning: true,
                piercing: 5,
                homing: true,
                color: '#330044'
            },
            
            eclipseAnnihilator: {
                name: 'Eclipse Annihilator',
                description: 'Ultimate explosive weapon that devastates enemies',
                projectileType: 'annihilator',
                damage: 35,
                fireRate: 0.6,
                projectileSpeed: 250,
                range: 450,
                multiShot: 1,
                spreadAngle: 0,
                explosive: true,
                explosionRadius: 80,
                chain: 3,
                color: '#ff8800'
            },
            
            // UNIQUE NEW WEAPONS
            astralSpear: {
                name: 'Astral Spear',
                description: 'Ethereal spear that phases through enemies and walls',
                projectileType: 'spear',
                damage: 14,
                fireRate: 0.35,
                projectileSpeed: 500,
                range: 600,
                multiShot: 1,
                spreadAngle: 0,
                piercing: 999, // Pierces everything
                phasing: true, // Special property: ignores walls
                color: '#88aaff'
            },
            
            soulReaper: {
                name: 'Soul Reaper',
                description: 'Scythe that grows stronger with each enemy killed',
                projectileType: 'reaper_soul',
                damage: 8,
                fireRate: 0.45,
                projectileSpeed: 350,
                range: 200,
                multiShot: 1,
                spreadAngle: 0,
                returning: true,
                soulGrowth: true, // Damage increases with kills
                color: '#aa44aa'
            },
            
            temporalRifle: {
                name: 'Temporal Rifle',
                description: 'Rifle that fires through time, hitting enemies before they move',
                projectileType: 'temporal',
                damage: 12,
                fireRate: 0.8,
                projectileSpeed: 800,
                range: 500,
                multiShot: 1,
                spreadAngle: 0,
                temporal: true, // Hits enemy future positions
                color: '#44ffff'
            },
            
            stormCaller: {
                name: 'Storm Caller',
                description: 'Summons lightning that jumps between all nearby enemies',
                projectileType: 'lightning',
                damage: 16,
                fireRate: 1.2,
                projectileSpeed: 0, // Instant
                range: 250,
                multiShot: 1,
                spreadAngle: 0,
                lightning: true, // Special area lightning effect
                color: '#ffff44'
            },
            
            gravityWell: {
                name: 'Gravity Well',
                description: 'Creates gravitational anomalies that pull enemies and explode',
                projectileType: 'gravity',
                damage: 20,
                fireRate: 1.5,
                projectileSpeed: 100,
                range: 300,
                multiShot: 1,
                spreadAngle: 0,
                explosive: true,
                explosionRadius: 100,
                gravity: true, // Pulls enemies before exploding
                color: '#8844ff'
            }
        };
        
        // Available weapon upgrades
        this.weaponEvolutions = {
            crimsonBolt: ['bloodWhip', 'shadowBlade'],
            bloodWhip: ['eclipseOrb'],
            shadowBlade: ['voidScythe'],
            eclipseOrb: ['voidScythe'],
            voidScythe: ['voidReaper'],
            
            // Ultimate evolutions (require specific conditions)
            crimsonDestroyer: [],
            voidReaper: [],
            eclipseAnnihilator: []
        };
        
        // Ultimate evolution requirements
        this.ultimateRequirements = {
            crimsonDestroyer: {
                baseWeapon: ['crimsonBolt', 'bloodWhip'],
                minLevel: 15,
                requiredUpgrades: ['explosive', 'multiShot', 'damage']
            },
            voidReaper: {
                baseWeapon: ['voidScythe'],
                minLevel: 20,
                requiredUpgrades: ['piercing', 'homing']
            },
            eclipseAnnihilator: {
                baseWeapon: ['eclipseOrb'],
                minLevel: 18,
                requiredUpgrades: ['explosive', 'chain']
            }
        };
    }
    
    // Get weapon upgrade options for upgrade system
    getWeaponUpgrades(currentWeapon) {
        const upgrades = {};
        const player = this.game.player;
        
        // Evolution upgrades
        if (this.weaponEvolutions[currentWeapon]) {
            this.weaponEvolutions[currentWeapon].forEach(weaponType => {
                const weapon = this.weaponTypes[weaponType];
                upgrades[`evolve_${weaponType}`] = {
                    name: `Evolve: ${weapon.name}`,
                    description: weapon.description,
                    effect: (player) => {
                        this.evolveWeapon(player, weaponType);
                    }
                };
            });
        }
        
        // Check for available ultimate evolutions
        if (player) {
            Object.keys(this.ultimateRequirements).forEach(ultimateWeapon => {
                const requirements = this.ultimateRequirements[ultimateWeapon];
                if (this.canEvolveToUltimate(player, ultimateWeapon, requirements)) {
                    const weapon = this.weaponTypes[ultimateWeapon];
                    upgrades[`evolve_${ultimateWeapon}`] = {
                        name: `🌟 Ultimate: ${weapon.name}`,
                        description: `${weapon.description} (ULTIMATE)`,
                        effect: (player) => {
                            this.evolveWeapon(player, ultimateWeapon);
                        }
                    };
                }
            });
        }
        
        // Weapon enhancement upgrades
        const currentWeaponData = this.weaponTypes[currentWeapon];
        if (currentWeaponData) {
            upgrades.weaponDamage = {
                name: `${currentWeaponData.name} Power`,
                description: `Increase ${currentWeaponData.name} damage by 5`,
                effect: (player) => { player.damage += 5; }
            };
            
            upgrades.weaponSpeed = {
                name: `${currentWeaponData.name} Speed`,
                description: `Increase ${currentWeaponData.name} fire rate by 15%`,
                effect: (player) => { player.fireRate = Math.max(player.fireRate * 0.85, 0.05); }
            };
        }
        
        return upgrades;
    }
    
    canEvolveToUltimate(player, ultimateWeapon, requirements) {
        // Check level requirement
        if (this.game.stats.level < requirements.minLevel) {
            return false;
        }
        
        // Check base weapon requirement
        if (!requirements.baseWeapon.includes(player.weaponType)) {
            return false;
        }
        
        // Check required upgrades (simplified check)
        for (let upgrade of requirements.requiredUpgrades) {
            switch (upgrade) {
                case 'explosive':
                    if (!player.explosive) return false;
                    break;
                case 'multiShot':
                    if (!player.multiShot || player.multiShot < 2) return false;
                    break;
                case 'damage':
                    // Check if player has upgraded damage significantly
                    if (player.damage < 20) return false;
                    break;
                case 'piercing':
                    if (!player.piercing || player.piercing < 2) return false;
                    break;
                case 'homing':
                    if (!player.homing) return false;
                    break;
                case 'chain':
                    if (!player.chain) return false;
                    break;
            }
        }
        
        return true;
    }
    
    evolveWeapon(player, newWeaponType) {
        const newWeapon = this.weaponTypes[newWeaponType];
        if (!newWeapon) return;
        
        // Store current upgrades before evolution
        const currentMultiShot = player.multiShot || 1;
        const currentSpreadAngle = player.spreadAngle || 0;
        const currentPiercing = player.piercing || 0;
        const currentExplosive = player.explosive;
        const currentExplosionRadius = player.explosionRadius || 0;
        const currentReturning = player.returning;
        const currentHoming = player.homing;
        const currentChain = player.chain || 0;
        
        // Update base damage tracking
        player.baseDamage = newWeapon.damage;
        
        // Apply new weapon stats (base stats only)
        player.weaponType = newWeaponType;
        player.damage = newWeapon.damage;
        player.fireRate = newWeapon.fireRate;
        player.projectileSpeed = newWeapon.projectileSpeed;
        player.projectileRange = newWeapon.range;
        
        // Apply special properties, keeping the better values
        if (newWeapon.piercing) {
            player.piercing = Math.max(newWeapon.piercing, currentPiercing);
        }
        if (newWeapon.explosive || currentExplosive) {
            player.explosive = true;
            player.explosionRadius = Math.max(newWeapon.explosionRadius || 0, currentExplosionRadius);
        }
        if (newWeapon.returning || currentReturning) {
            player.returning = true;
        }
        if (newWeapon.multiShot || currentMultiShot > 1) {
            player.multiShot = Math.max(newWeapon.multiShot || 1, currentMultiShot);
            player.spreadAngle = Math.max(newWeapon.spreadAngle || 0, currentSpreadAngle);
        }
        if (newWeapon.homing || currentHoming) {
            player.homing = true;
        }
        if (newWeapon.chain || currentChain > 0) {
            player.chain = Math.max(newWeapon.chain || 0, currentChain);
        }
        
        // Update damage based on fury if active
        if (player.fury) {
            player.updateDamageFromFury();
        }
        
        // Visual feedback
        this.game.upgradeSystem.showUpgradeNotification(`Weapon Evolved: ${newWeapon.name}`);
    }
    
    createProjectileFromWeapon(player, weaponData, angle) {
        const weaponType = this.weaponTypes[weaponData.type];
        if (!weaponType) return null;
        
        switch (weaponType.projectileType) {
            case 'bolt':
                return this.createBoltProjectileFromWeapon(player, weaponData, angle, weaponType);
            case 'whip':
                return this.createWhipProjectileFromWeapon(player, weaponData, angle, weaponType);
            case 'blade':
                return this.createBladeProjectileFromWeapon(player, weaponData, angle, weaponType);
            case 'orb':
                return this.createOrbProjectileFromWeapon(player, weaponData, angle, weaponType);
            case 'scythe':
                return this.createScytheProjectileFromWeapon(player, weaponData, angle, weaponType);
            case 'destroyer':
                return this.createDestroyerProjectileFromWeapon(player, weaponData, angle, weaponType);
            case 'reaper':
                return this.createReaperProjectileFromWeapon(player, weaponData, angle, weaponType);
            case 'annihilator':
                return this.createAnnihilatorProjectileFromWeapon(player, weaponData, angle, weaponType);
            case 'gravity':
                return this.createGravityProjectileFromWeapon(player, weaponData, angle, weaponType);
            default:
                return this.createBoltProjectileFromWeapon(player, weaponData, angle, weaponType);
        }
    }

    createProjectile(player, angle) {
        const weaponType = player.weaponType || 'crimsonBolt';
        const weapon = this.weaponTypes[weaponType];
        
        switch (weapon.projectileType) {
            case 'bolt':
                return this.createBoltProjectile(player, angle, weapon);
            case 'whip':
                return this.createWhipProjectile(player, angle, weapon);
            case 'blade':
                return this.createBladeProjectile(player, angle, weapon);
            case 'orb':
                return this.createOrbProjectile(player, angle, weapon);
            case 'scythe':
                return this.createScytheProjectile(player, angle, weapon);
            case 'destroyer':
                return this.createDestroyerProjectile(player, angle, weapon);
            case 'reaper':
                return this.createReaperProjectile(player, angle, weapon);
            case 'annihilator':
                return this.createAnnihilatorProjectile(player, angle, weapon);
            case 'gravity':
                return this.createGravityProjectile(player, angle, weapon);
            default:
                return this.createBoltProjectile(player, angle, weapon);
        }
    }
    
    createBoltProjectile(player, angle, weapon) {
        const projectileX = player.x + Math.cos(angle) * (player.width / 2 + 5);
        const projectileY = player.y + Math.sin(angle) * (player.height / 2 + 5);
        
        const projectile = new Projectile(
            this.game,
            projectileX,
            projectileY,
            Math.cos(angle) * weapon.projectileSpeed,
            Math.sin(angle) * weapon.projectileSpeed,
            player.damage,
            player.projectileRange,
            'player'
        );
        
        projectile.color = weapon.color;
        return projectile;
    }
    
    createWhipProjectile(player, angle, weapon) {
        // Whip creates a short-range arc projectile
        const projectileX = player.x + Math.cos(angle) * (player.width / 2 + 5);
        const projectileY = player.y + Math.sin(angle) * (player.height / 2 + 5);
        
        const projectile = new Projectile(
            this.game,
            projectileX,
            projectileY,
            Math.cos(angle) * 200, // Improved speed from 50 to 200
            Math.sin(angle) * 200,
            player.damage,
            weapon.range,
            'player'
        );
        
        projectile.color = weapon.color;
        projectile.width = 30; // Wider hitbox
        projectile.height = 30;
        projectile.piercing = 999; // Hits everything in path
        
        return projectile;
    }
    
    createBladeProjectile(player, angle, weapon) {
        const projectileX = player.x + Math.cos(angle) * (player.width / 2 + 5);
        const projectileY = player.y + Math.sin(angle) * (player.height / 2 + 5);
        
        const projectile = new Projectile(
            this.game,
            projectileX,
            projectileY,
            Math.cos(angle) * weapon.projectileSpeed,
            Math.sin(angle) * weapon.projectileSpeed,
            player.damage,
            player.projectileRange,
            'player'
        );
        
        projectile.color = weapon.color;
        projectile.piercing = weapon.piercing || player.piercing;
        projectile.width = 6; // Slightly larger
        projectile.height = 6;
        
        return projectile;
    }
    
    createOrbProjectile(player, angle, weapon) {
        const projectileX = player.x + Math.cos(angle) * (player.width / 2 + 5);
        const projectileY = player.y + Math.sin(angle) * (player.height / 2 + 5);
        
        const projectile = new Projectile(
            this.game,
            projectileX,
            projectileY,
            Math.cos(angle) * weapon.projectileSpeed,
            Math.sin(angle) * weapon.projectileSpeed,
            player.damage,
            player.projectileRange,
            'player'
        );
        
        projectile.color = weapon.color;
        projectile.explosive = weapon.explosive || player.explosive;
        projectile.explosionRadius = weapon.explosionRadius || player.explosionRadius;
        projectile.width = 8; // Larger orb
        projectile.height = 8;
        
        return projectile;
    }
    
    createScytheProjectile(player, angle, weapon) {
        const projectileX = player.x + Math.cos(angle) * (player.width / 2 + 5);
        const projectileY = player.y + Math.sin(angle) * (player.height / 2 + 5);
        
        const projectile = new Projectile(
            this.game,
            projectileX,
            projectileY,
            Math.cos(angle) * weapon.projectileSpeed,
            Math.sin(angle) * weapon.projectileSpeed,
            player.damage,
            player.projectileRange,
            'player'
        );
        
        projectile.color = weapon.color;
        projectile.returning = weapon.returning || player.returning;
        projectile.piercing = weapon.piercing || player.piercing || 1; // Can hit multiple enemies
        projectile.width = 10; // Large scythe
        projectile.height = 10;
        projectile.spin = 0; // For visual spinning effect
        
        return projectile;
    }
    
    createDestroyerProjectile(player, angle, weapon) {
        const projectileX = player.x + Math.cos(angle) * (player.width / 2 + 5);
        const projectileY = player.y + Math.sin(angle) * (player.height / 2 + 5);
        
        const projectile = new Projectile(
            this.game,
            projectileX,
            projectileY,
            Math.cos(angle) * weapon.projectileSpeed,
            Math.sin(angle) * weapon.projectileSpeed,
            player.damage,
            player.projectileRange,
            'player'
        );
        
        projectile.color = weapon.color;
        projectile.piercing = weapon.piercing || player.piercing || 1;
        projectile.explosive = weapon.explosive || player.explosive;
        projectile.explosionRadius = weapon.explosionRadius || player.explosionRadius;
        projectile.width = 8;
        projectile.height = 8;
        
        return projectile;
    }
    
    createReaperProjectile(player, angle, weapon) {
        const projectileX = player.x + Math.cos(angle) * (player.width / 2 + 5);
        const projectileY = player.y + Math.sin(angle) * (player.height / 2 + 5);
        
        const projectile = new Projectile(
            this.game,
            projectileX,
            projectileY,
            Math.cos(angle) * weapon.projectileSpeed,
            Math.sin(angle) * weapon.projectileSpeed,
            player.damage,
            player.projectileRange,
            'player'
        );
        
        projectile.color = weapon.color;
        projectile.returning = weapon.returning || player.returning;
        projectile.piercing = weapon.piercing || player.piercing || 1;
        projectile.homing = weapon.homing || player.homing;
        projectile.width = 12;
        projectile.height = 12;
        projectile.spin = 0;
        
        return projectile;
    }
    
    createAnnihilatorProjectile(player, angle, weapon) {
        const projectileX = player.x + Math.cos(angle) * (player.width / 2 + 5);
        const projectileY = player.y + Math.sin(angle) * (player.height / 2 + 5);
        
        const projectile = new Projectile(
            this.game,
            projectileX,
            projectileY,
            Math.cos(angle) * weapon.projectileSpeed,
            Math.sin(angle) * weapon.projectileSpeed,
            player.damage,
            player.projectileRange,
            'player'
        );
        
        projectile.color = weapon.color;
        projectile.explosive = weapon.explosive || player.explosive;
        projectile.explosionRadius = weapon.explosionRadius || player.explosionRadius;
        projectile.chain = weapon.chain || player.chain;
        projectile.width = 10;
        projectile.height = 10;
        
        return projectile;
    }
    
    // New methods that use weapon data objects instead of player properties
    createBoltProjectileFromWeapon(player, weaponData, angle, weaponType) {
        const projectileX = player.x + Math.cos(angle) * (player.width / 2 + 5);
        const projectileY = player.y + Math.sin(angle) * (player.height / 2 + 5);
        
        const projectile = new Projectile(
            this.game,
            projectileX,
            projectileY,
            Math.cos(angle) * weaponData.projectileSpeed,
            Math.sin(angle) * weaponData.projectileSpeed,
            weaponData.damage,
            weaponData.projectileRange,
            'player'
        );
        
        projectile.color = weaponType.color;
        return projectile;
    }
    
    createWhipProjectileFromWeapon(player, weaponData, angle, weaponType) {
        const projectileX = player.x + Math.cos(angle) * (player.width / 2 + 5);
        const projectileY = player.y + Math.sin(angle) * (player.height / 2 + 5);
        
        const projectile = new Projectile(
            this.game,
            projectileX,
            projectileY,
            Math.cos(angle) * Math.max(weaponData.projectileSpeed, 200),
            Math.sin(angle) * Math.max(weaponData.projectileSpeed, 200),
            weaponData.damage,
            weaponData.projectileRange,
            'player'
        );
        
        projectile.color = weaponType.color;
        projectile.width = 30;
        projectile.height = 30;
        projectile.piercing = 999;
        
        return projectile;
    }
    
    createBladeProjectileFromWeapon(player, weaponData, angle, weaponType) {
        const projectileX = player.x + Math.cos(angle) * (player.width / 2 + 5);
        const projectileY = player.y + Math.sin(angle) * (player.height / 2 + 5);
        
        const projectile = new Projectile(
            this.game,
            projectileX,
            projectileY,
            Math.cos(angle) * weaponData.projectileSpeed,
            Math.sin(angle) * weaponData.projectileSpeed,
            weaponData.damage,
            weaponData.projectileRange,
            'player'
        );
        
        projectile.color = weaponType.color;
        projectile.piercing = weaponData.piercing;
        projectile.width = 6;
        projectile.height = 6;
        
        return projectile;
    }
    
    createOrbProjectileFromWeapon(player, weaponData, angle, weaponType) {
        const projectileX = player.x + Math.cos(angle) * (player.width / 2 + 5);
        const projectileY = player.y + Math.sin(angle) * (player.height / 2 + 5);
        
        const projectile = new Projectile(
            this.game,
            projectileX,
            projectileY,
            Math.cos(angle) * weaponData.projectileSpeed,
            Math.sin(angle) * weaponData.projectileSpeed,
            weaponData.damage,
            weaponData.projectileRange,
            'player'
        );
        
        projectile.color = weaponType.color;
        projectile.explosive = weaponData.explosive;
        projectile.explosionRadius = weaponData.explosionRadius;
        projectile.width = 8;
        projectile.height = 8;
        
        return projectile;
    }
    
    createScytheProjectileFromWeapon(player, weaponData, angle, weaponType) {
        const projectileX = player.x + Math.cos(angle) * (player.width / 2 + 5);
        const projectileY = player.y + Math.sin(angle) * (player.height / 2 + 5);
        
        const projectile = new Projectile(
            this.game,
            projectileX,
            projectileY,
            Math.cos(angle) * weaponData.projectileSpeed,
            Math.sin(angle) * weaponData.projectileSpeed,
            weaponData.damage,
            weaponData.projectileRange,
            'player'
        );
        
        projectile.color = weaponType.color;
        projectile.returning = weaponData.returning;
        projectile.piercing = weaponData.piercing;
        projectile.width = 10;
        projectile.height = 10;
        projectile.spin = 0;
        
        return projectile;
    }
    
    createDestroyerProjectileFromWeapon(player, weaponData, angle, weaponType) {
        const projectileX = player.x + Math.cos(angle) * (player.width / 2 + 5);
        const projectileY = player.y + Math.sin(angle) * (player.height / 2 + 5);
        
        const projectile = new Projectile(
            this.game,
            projectileX,
            projectileY,
            Math.cos(angle) * weaponData.projectileSpeed,
            Math.sin(angle) * weaponData.projectileSpeed,
            weaponData.damage,
            weaponData.projectileRange,
            'player'
        );
        
        projectile.color = weaponType.color;
        projectile.piercing = weaponData.piercing;
        projectile.explosive = weaponData.explosive;
        projectile.explosionRadius = weaponData.explosionRadius;
        projectile.width = 8;
        projectile.height = 8;
        
        return projectile;
    }
    
    createReaperProjectileFromWeapon(player, weaponData, angle, weaponType) {
        const projectileX = player.x + Math.cos(angle) * (player.width / 2 + 5);
        const projectileY = player.y + Math.sin(angle) * (player.height / 2 + 5);
        
        const projectile = new Projectile(
            this.game,
            projectileX,
            projectileY,
            Math.cos(angle) * weaponData.projectileSpeed,
            Math.sin(angle) * weaponData.projectileSpeed,
            weaponData.damage,
            weaponData.projectileRange,
            'player'
        );
        
        projectile.color = weaponType.color;
        projectile.returning = weaponData.returning;
        projectile.piercing = weaponData.piercing;
        projectile.homing = weaponData.homing;
        projectile.width = 12;
        projectile.height = 12;
        projectile.spin = 0;
        
        return projectile;
    }
    
    createAnnihilatorProjectileFromWeapon(player, weaponData, angle, weaponType) {
        const projectileX = player.x + Math.cos(angle) * (player.width / 2 + 5);
        const projectileY = player.y + Math.sin(angle) * (player.height / 2 + 5);
        
        const projectile = new Projectile(
            this.game,
            projectileX,
            projectileY,
            Math.cos(angle) * weaponData.projectileSpeed,
            Math.sin(angle) * weaponData.projectileSpeed,
            weaponData.damage,
            weaponData.projectileRange,
            'player'
        );
        
        projectile.color = weaponType.color;
        projectile.explosive = weaponData.explosive;
        projectile.explosionRadius = weaponData.explosionRadius;
        projectile.chain = weaponData.chain;
        projectile.width = 10;
        projectile.height = 10;
        
        return projectile;
    }
    
    createGravityProjectile(player, angle, weapon) {
        const projectileX = player.x + Math.cos(angle) * (player.width / 2 + 5);
        const projectileY = player.y + Math.sin(angle) * (player.height / 2 + 5);
        
        const projectile = new Projectile(
            this.game,
            projectileX,
            projectileY,
            Math.cos(angle) * weapon.projectileSpeed,
            Math.sin(angle) * weapon.projectileSpeed,
            player.damage,
            player.projectileRange,
            'player'
        );
        
        // Special gravity properties
        projectile.color = weapon.color;
        projectile.explosive = weapon.explosive;
        projectile.explosionRadius = weapon.explosionRadius;
        projectile.gravity = true;
        projectile.gravityRange = 80; // Range for gravity pull effect
        projectile.gravityStrength = 150; // Pull strength
        projectile.width = 16;
        projectile.height = 16;
        projectile.projectileType = 'gravity';
        
        return projectile;
    }
    
    createGravityProjectileFromWeapon(player, weaponData, angle, weaponType) {
        const projectileX = player.x + Math.cos(angle) * (player.width / 2 + 5);
        const projectileY = player.y + Math.sin(angle) * (player.height / 2 + 5);
        
        const projectile = new Projectile(
            this.game,
            projectileX,
            projectileY,
            Math.cos(angle) * weaponData.projectileSpeed,
            Math.sin(angle) * weaponData.projectileSpeed,
            weaponData.damage,
            weaponData.projectileRange,
            'player'
        );
        
        // Special gravity properties
        projectile.color = weaponType.color;
        projectile.explosive = weaponData.explosive;
        projectile.explosionRadius = weaponData.explosionRadius;
        projectile.gravity = true;
        projectile.gravityRange = 80; // Range for gravity pull effect
        projectile.gravityStrength = 150; // Pull strength
        projectile.width = 16;
        projectile.height = 16;
        projectile.projectileType = 'gravity';
        
        return projectile;
    }
}