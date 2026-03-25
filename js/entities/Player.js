class Player {
    constructor(game, x, y) {
        this.game = game;
        this.type = 'player';
        this.x = x;
        this.y = y;
        this.width = 20;
        this.height = 20;
        this.active = true;
        
        // Movement properties
        this.speed = 150; // pixels per second
        this.vx = 0;
        this.vy = 0;
        
        // Combat properties
        this.damage = 10;
        this.fireRate = 0.4; // seconds between shots
        this.timeSinceLastShot = 0;
        this.projectileSpeed = 400;
        this.projectileRange = 300;
        
        // Visual properties
        this.color = '#ff4444';
        this.angle = 0; // facing direction
        
        // Invincibility frames after taking damage
        this.invulnerable = false;
        this.invulnerabilityTime = 1.0; // seconds
        this.timeSinceHit = 0;
        
        // Weapon properties - now supports multiple weapons
        this.weapons = [
            {
                type: 'crimsonBolt',
                damage: 10,
                fireRate: 0.4,
                projectileSpeed: 400,
                projectileRange: 300,
                multiShot: 1,
                spreadAngle: 0,
                piercing: 0,
                explosive: false,
                explosionRadius: 0,
                returning: false,
                homing: false,
                chain: 0,
                chainRange: 100,
                timeSinceLastShot: 0
            }
        ];
        this.maxWeapons = 3;
        
        // Legacy weapon properties for backwards compatibility
        this.weaponType = 'crimsonBolt';
        
        // Upgrade properties
        this.multiShot = 1;
        this.spreadAngle = 0;
        this.piercing = 0;
        this.explosive = false;
        this.explosionRadius = 0;
        this.criticalChance = 0;
        this.regeneration = 0;
        this.magnetRange = 50;
        this.timeSinceRegen = 0;
        this.returning = false;
        
        // Power-up properties
        this.shielded = false;
        this.shieldEndTime = 0;
        this.activeBoosts = [];
        
        // Blood Fury properties
        this.fury = false;
        this.furyStacks = 0;
        this.furyDuration = 5;
        this.furyEndTime = 0;
        this.baseDamage = 10; // Store original damage for fury calculations
        
        // Spirit Guardian properties
        this.guardians = 0;
        this.guardianEntities = [];
        
        // Chain Lightning properties
        this.chain = 0;
        this.chainRange = 100;
        
        // Track collected upgrades for UI display
        this.collectedUpgrades = [];
    }
    
    update(deltaTime) {
        this.handleInput(deltaTime);
        this.updateMovement(deltaTime);
        this.updateShooting(deltaTime);
        this.updateInvulnerability(deltaTime);
        this.updateRegeneration(deltaTime);
        this.updateFury(deltaTime);
        this.updateGuardians(deltaTime);
        this.updateAura(deltaTime);
        this.constrainToCanvas();
    }
    
    handleInput(deltaTime) {
        let moveX = 0;
        let moveY = 0;
        
        // Movement input (WASD or Arrow keys)
        if (this.game.isKeyPressed('KeyW') || this.game.isKeyPressed('ArrowUp')) {
            moveY = -1;
        }
        if (this.game.isKeyPressed('KeyS') || this.game.isKeyPressed('ArrowDown')) {
            moveY = 1;
        }
        if (this.game.isKeyPressed('KeyA') || this.game.isKeyPressed('ArrowLeft')) {
            moveX = -1;
        }
        if (this.game.isKeyPressed('KeyD') || this.game.isKeyPressed('ArrowRight')) {
            moveX = 1;
        }
        
        // Normalize diagonal movement
        if (moveX !== 0 && moveY !== 0) {
            const length = Math.sqrt(moveX * moveX + moveY * moveY);
            moveX /= length;
            moveY /= length;
        }
        
        // Set velocity
        this.vx = moveX * this.speed;
        this.vy = moveY * this.speed;
        
        // Update facing direction based on nearest enemy or mouse
        this.updateFacingDirection();
    }
    
    updateFacingDirection() {
        // Find nearest enemy to aim at
        const enemies = this.game.getEntitiesByType('enemy');
        let nearestEnemy = null;
        let nearestDistance = Infinity;
        
        for (let enemy of enemies) {
            const dx = enemy.x - this.x;
            const dy = enemy.y - this.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < nearestDistance) {
                nearestDistance = distance;
                nearestEnemy = enemy;
            }
        }
        
        if (nearestEnemy) {
            const dx = nearestEnemy.x - this.x;
            const dy = nearestEnemy.y - this.y;
            this.angle = Math.atan2(dy, dx);
        }
    }
    
    updateMovement(deltaTime) {
        // Apply velocity
        this.x += this.vx * deltaTime;
        this.y += this.vy * deltaTime;
    }
    
    updateShooting(deltaTime) {
        // Update shooting for each weapon
        this.weapons.forEach(weapon => {
            weapon.timeSinceLastShot += deltaTime;
        });
        
        // Auto-fire any weapon that's ready if enemies are present
        const enemies = this.game.getEntitiesByType('enemy');
        if (enemies.length > 0) {
            this.weapons.forEach((weapon, index) => {
                if (weapon.timeSinceLastShot >= weapon.fireRate) {
                    this.shootWeapon(weapon, index);
                    weapon.timeSinceLastShot = 0;
                }
            });
        }
        
        // Legacy support - update main weapon timers
        this.timeSinceLastShot += deltaTime;
        if (enemies.length > 0 && this.timeSinceLastShot >= this.fireRate) {
            // This ensures backwards compatibility but won't actually fire
            // since the new system handles all firing
            this.timeSinceLastShot = 0;
        }
    }
    
    updateInvulnerability(deltaTime) {
        if (this.invulnerable) {
            this.timeSinceHit += deltaTime;
            if (this.timeSinceHit >= this.invulnerabilityTime) {
                this.invulnerable = false;
                this.timeSinceHit = 0;
            }
        }
    }
    
    shootWeapon(weapon, weaponIndex) {
        // Calculate damage with critical hit chance
        let originalDamage = weapon.damage;
        if (Math.random() < this.criticalChance) {
            weapon.damage *= 2;
        }
        
        // Create multiple projectiles if multishot is upgraded
        for (let i = 0; i < weapon.multiShot; i++) {
            let angle = this.angle;
            
            // Spread projectiles if multishot > 1
            if (weapon.multiShot > 1) {
                const spread = weapon.spreadAngle * (weapon.multiShot - 1);
                angle += (-spread / 2) + (spread * i / (weapon.multiShot - 1));
            }
            
            // Use weapon system to create the appropriate projectile
            const projectile = this.game.weaponSystem.createProjectileFromWeapon(this, weapon, angle);
            
            // Apply weapon-specific properties to projectile
            if (weapon.piercing) projectile.piercing = weapon.piercing;
            if (weapon.explosive) {
                projectile.explosive = weapon.explosive;
                projectile.explosionRadius = weapon.explosionRadius;
            }
            if (weapon.returning) projectile.returning = weapon.returning;
            if (weapon.chain) {
                projectile.chain = weapon.chain;
                projectile.chainsRemaining = weapon.chain;
                projectile.chainRange = weapon.chainRange;
            }
            if (weapon.homing) {
                projectile.homing = weapon.homing;
            }
            if (weapon.freezing) {
                projectile.freezing = weapon.freezing;
                projectile.slowEffect = weapon.slowEffect;
            }
            if (weapon.bouncing) {
                projectile.bouncing = weapon.bouncing;
            }
            
            this.game.addEntity(projectile);
        }
        
        // Reset damage after critical hit
        weapon.damage = originalDamage;
    }
    
    // Legacy shoot method for backwards compatibility
    shoot() {
        // Calculate damage with critical hit chance
        let originalDamage = this.damage;
        if (Math.random() < this.criticalChance) {
            this.damage *= 2;
        }
        
        // Create multiple projectiles if multishot is upgraded
        for (let i = 0; i < this.multiShot; i++) {
            let angle = this.angle;
            
            // Spread projectiles if multishot > 1
            if (this.multiShot > 1) {
                const spread = this.spreadAngle * (this.multiShot - 1);
                angle += (-spread / 2) + (spread * i / (this.multiShot - 1));
            }
            
            // Use weapon system to create the appropriate projectile
            const projectile = this.game.weaponSystem.createProjectile(this, angle);
            
            // Apply upgrade properties to projectile
            if (this.piercing) projectile.piercing = Math.max(projectile.piercing || 0, this.piercing);
            if (this.explosive) {
                projectile.explosive = this.explosive;
                projectile.explosionRadius = this.explosionRadius;
            }
            if (this.returning) projectile.returning = this.returning;
            if (this.chain) {
                projectile.chain = this.chain;
                projectile.chainsRemaining = this.chain;
                projectile.chainRange = this.chainRange;
            }
            if (this.homing) {
                projectile.homing = this.homing;
            }
            if (this.freezing) {
                projectile.freezing = this.freezing;
                projectile.slowEffect = this.slowEffect;
            }
            if (this.bouncing) {
                projectile.bouncing = this.bouncing;
            }
            
            this.game.addEntity(projectile);
        }
        
        // Reset damage after critical hit
        this.damage = originalDamage;
    }
    
    constrainToCanvas() {
        // Keep player within canvas bounds
        const halfWidth = this.width / 2;
        const halfHeight = this.height / 2;
        
        if (this.x - halfWidth < 0) {
            this.x = halfWidth;
        } else if (this.x + halfWidth > this.game.canvas.width) {
            this.x = this.game.canvas.width - halfWidth;
        }
        
        if (this.y - halfHeight < 0) {
            this.y = halfHeight;
        } else if (this.y + halfHeight > this.game.canvas.height) {
            this.y = this.game.canvas.height - halfHeight;
        }
    }
    
    takeDamage(amount) {
        if (this.invulnerable) return;
        
        // Shield blocks damage
        if (this.shielded && Date.now() < this.shieldEndTime) {
            return; // No damage taken while shielded
        }
        
        this.game.takeDamage(amount);
        this.invulnerable = true;
        this.timeSinceHit = 0;
    }
    
    getBounds() {
        return {
            x: this.x - this.width / 2,
            y: this.y - this.height / 2,
            width: this.width,
            height: this.height
        };
    }
    
    render(ctx) {
        // Flicker effect when invulnerable
        if (this.invulnerable && Math.floor(this.timeSinceHit * 10) % 2 === 0) {
            return; // Skip rendering for flicker effect
        }
        
        ctx.save();
        
        // Shield effect
        if (this.shielded && Date.now() < this.shieldEndTime) {
            ctx.shadowColor = '#4444ff';
            ctx.shadowBlur = 15;
            ctx.strokeStyle = '#4444ff';
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.width + 5, 0, Math.PI * 2);
            ctx.stroke();
        }
        
        // Move to player position
        ctx.translate(this.x, this.y);
        ctx.rotate(this.angle);
        
        // Draw player as a triangle pointing in facing direction
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.moveTo(this.width / 2, 0);
        ctx.lineTo(-this.width / 2, -this.height / 2);
        ctx.lineTo(-this.width / 2, this.height / 2);
        ctx.closePath();
        ctx.fill();
        
        // Draw outline
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1;
        ctx.stroke();
        
        ctx.restore();
        
        // Render spirit guardians
        this.renderGuardians(ctx);
    }
    
    renderGuardians(ctx) {
        this.guardianEntities.forEach(guardian => {
            ctx.save();
            ctx.translate(guardian.x, guardian.y);
            
            // Draw guardian as a small glowing orb
            ctx.shadowColor = '#44ffff';
            ctx.shadowBlur = 10;
            ctx.fillStyle = '#44ffff';
            ctx.beginPath();
            ctx.arc(0, 0, 6, 0, Math.PI * 2);
            ctx.fill();
            
            // Draw trail effect
            ctx.strokeStyle = '#88ffff';
            ctx.lineWidth = 2;
            ctx.stroke();
            
            ctx.restore();
        });
    }
    
    updateRegeneration(deltaTime) {
        if (this.regeneration > 0) {
            this.timeSinceRegen += deltaTime;
            
            // Regenerate 1 HP per point of regeneration every 2 seconds
            if (this.timeSinceRegen >= 2.0) {
                const healAmount = this.regeneration;
                this.game.stats.health = Math.min(
                    this.game.stats.health + healAmount,
                    this.game.stats.maxHealth
                );
                this.timeSinceRegen = 0;
            }
        }
    }
    
    updateFury(deltaTime) {
        if (this.fury && this.furyStacks > 0) {
            const currentTime = Date.now() / 1000;
            
            // Check if fury has expired
            if (currentTime > this.furyEndTime) {
                this.furyStacks = 0;
                this.updateDamageFromFury();
            }
        }
    }
    
    updateGuardians(deltaTime) {
        // Spirit Guardian functionality - create orbiting spirits
        if (this.guardians > 0 && this.guardianEntities.length < this.guardians) {
            // Create missing guardian entities
            for (let i = this.guardianEntities.length; i < this.guardians; i++) {
                const guardian = {
                    angle: (i / this.guardians) * Math.PI * 2,
                    radius: 40,
                    damage: 5,
                    speed: 2, // rotation speed
                    lastHit: 0
                };
                this.guardianEntities.push(guardian);
            }
        }
        
        // Update guardian positions and rotation
        this.guardianEntities.forEach((guardian, index) => {
            guardian.angle += guardian.speed * deltaTime;
            guardian.x = this.x + Math.cos(guardian.angle) * guardian.radius;
            guardian.y = this.y + Math.sin(guardian.angle) * guardian.radius;
        });
    }
    
    onEnemyKilled() {
        // Blood Fury effect - stack damage on kills
        if (this.fury) {
            this.furyStacks = Math.min(this.furyStacks + 1, 10); // Max 10 stacks
            this.furyEndTime = Date.now() / 1000 + this.furyDuration;
            this.updateDamageFromFury();
        }
    }
    
    updateDamageFromFury() {
        // Update damage based on fury stacks
        const furyBonus = this.fury ? this.furyStacks * 2 : 0; // +2 damage per stack
        
        // Update legacy damage property for compatibility
        if (this.fury) {
            this.damage = this.baseDamage + furyBonus;
        } else {
            this.damage = this.baseDamage;
        }
        
        // CRITICAL: Update all weapons in multi-weapon system
        if (this.weapons && this.weapons.length > 0) {
            this.weapons.forEach((weapon, index) => {
                // Each weapon stores its base damage when added
                if (!weapon.baseDamage) {
                    // If baseDamage not set, use current damage as base
                    weapon.baseDamage = weapon.damage;
                }
                
                // Apply fury bonus to weapon damage
                if (this.fury && furyBonus > 0) {
                    weapon.damage = weapon.baseDamage + furyBonus;
                } else {
                    weapon.damage = weapon.baseDamage;
                }
            });
        }
    }
    
    addWeapon(weaponType) {
        // Don't add if already at max weapons
        if (this.weapons.length >= this.maxWeapons) {
            return false;
        }
        
        // Don't add if already have this weapon type
        if (this.weapons.some(w => w.type === weaponType)) {
            return false;
        }
        
        const weaponData = this.game.weaponSystem.weaponTypes[weaponType];
        if (!weaponData) return false;
        
        const newWeapon = {
            type: weaponType,
            damage: weaponData.damage,
            baseDamage: weaponData.damage, // Store base damage for fury calculations
            fireRate: weaponData.fireRate,
            projectileSpeed: weaponData.projectileSpeed,
            projectileRange: weaponData.range,
            multiShot: weaponData.multiShot || 1,
            spreadAngle: weaponData.spreadAngle || 0,
            piercing: weaponData.piercing || 0,
            explosive: weaponData.explosive || false,
            explosionRadius: weaponData.explosionRadius || 0,
            returning: weaponData.returning || false,
            homing: weaponData.homing || false,
            chain: weaponData.chain || 0,
            chainRange: weaponData.chainRange || 100,
            timeSinceLastShot: 0
        };
        
        this.weapons.push(newWeapon);
        
        // Apply current fury bonus to new weapon if active
        if (this.fury && this.furyStacks > 0) {
            this.updateDamageFromFury();
        }
        
        return true;
    }
    
    upgradeWeapon(weaponIndex, upgradeType, value) {
        if (weaponIndex >= 0 && weaponIndex < this.weapons.length) {
            const weapon = this.weapons[weaponIndex];
            
            switch (upgradeType) {
                case 'damage':
                    weapon.damage += value;
                    weapon.baseDamage = (weapon.baseDamage || weapon.damage - value) + value; // Update base damage too
                    break;
                case 'fireRate':
                    weapon.fireRate = Math.max(weapon.fireRate * (1 - value), 0.05);
                    break;
                case 'projectileSpeed':
                    weapon.projectileSpeed *= (1 + value);
                    break;
                case 'projectileRange':
                    weapon.projectileRange *= (1 + value);
                    break;
                case 'multiShot':
                    weapon.multiShot += value;
                    weapon.spreadAngle = Math.max(weapon.spreadAngle, 0.2);
                    break;
                case 'piercing':
                    weapon.piercing += value;
                    break;
                case 'explosive':
                    weapon.explosive = true;
                    weapon.explosionRadius = weapon.explosionRadius || 30;
                    break;
                case 'explosionRadius':
                    weapon.explosionRadius += value;
                    break;
                case 'returning':
                    weapon.returning = true;
                    break;
                case 'homing':
                    weapon.homing = true;
                    break;
                case 'chain':
                    weapon.chain += value;
                    break;
            }
        }
    }
    
    updateAura(deltaTime) {
        // Death Aura functionality - damage nearby enemies
        if (this.aura && this.aura > 0) {
            const enemies = this.game.getEntitiesByType('enemy');
            const currentTime = Date.now();
            
            enemies.forEach(enemy => {
                const dx = enemy.x - this.x;
                const dy = enemy.y - this.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance <= this.auraRange) {
                    // Damage enemy every 0.5 seconds
                    if (!enemy.lastAuraDamage || currentTime - enemy.lastAuraDamage >= 500) {
                        const damage = this.auraDamage * this.aura;
                        enemy.takeDamage(damage);
                        enemy.lastAuraDamage = currentTime;
                        
                        // Visual effect for aura damage
                        if (this.game.renderSystem) {
                            this.game.renderSystem.addDamageNumber(enemy.x, enemy.y, damage, '#aa44ff');
                        }
                    }
                }
            });
        }
    }
    
    getActiveBuffs() {
        const buffs = [];
        
        // Blood Fury buff
        if (this.fury && this.furyStacks > 0) {
            const timeLeft = Math.max(0, this.furyEndTime - Date.now() / 1000);
            buffs.push({
                name: 'Blood Fury',
                stacks: this.furyStacks,
                timeLeft: timeLeft,
                color: '#ff4444'
            });
        }
        
        // Shield buff
        if (this.shielded && Date.now() < this.shieldEndTime) {
            const timeLeft = Math.max(0, (this.shieldEndTime - Date.now()) / 1000);
            buffs.push({
                name: 'Eclipse Shield',
                timeLeft: timeLeft,
                color: '#4444ff'
            });
        }
        
        // Death Aura buff
        if (this.aura && this.aura > 0) {
            buffs.push({
                name: 'Death Aura',
                stacks: this.aura,
                color: '#aa44ff'
            });
        }
        
        // Active power-up boosts
        this.activeBoosts.forEach(boost => {
            if (boost.endTime > Date.now()) {
                const timeLeft = Math.max(0, (boost.endTime - Date.now()) / 1000);
                // Convert property name to readable buff name
                let buffName = 'Power-up';
                if (boost.property === 'damage') buffName = 'Damage Boost';
                else if (boost.property === 'speed') buffName = 'Speed Boost';
                else if (boost.property === 'fireRate') buffName = 'Rapid Fire';
                else if (boost.property === 'magnetRange') buffName = 'Soul Magnet';
                
                buffs.push({
                    name: buffName,
                    timeLeft: timeLeft,
                    color: '#44ff44'
                });
            }
        });
        
        return buffs;
    }
}