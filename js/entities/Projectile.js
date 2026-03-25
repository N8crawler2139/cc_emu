class Projectile {
    constructor(game, x, y, vx, vy, damage, range, owner) {
        this.game = game;
        this.type = 'projectile';
        this.x = x;
        this.y = y;
        this.vx = vx;
        this.vy = vy;
        this.damage = damage;
        this.range = range;
        this.owner = owner; // 'player' or 'enemy'
        this.active = true;
        
        this.width = 4;
        this.height = 4;
        
        // Track distance traveled
        this.distanceTraveled = 0;
        
        // Visual properties
        this.color = owner === 'player' ? '#ff4444' : '#4444ff';
        this.trailParticles = [];
        
        // Upgrade properties
        this.piercing = 0;
        this.enemiesHit = 0;
        this.explosive = false;
        this.explosionRadius = 0;
        this.returning = false;
        this.hasReturned = false;
        this.spin = 0;
        this.chain = 0;
        this.chainRange = 100;
        this.chainsRemaining = 0;
        this.homing = false;
        this.homingStrength = 150; // pixels per second turning speed
        this.target = null;
        
        // Gravity properties
        this.gravity = false;
        this.gravityRange = 80;
        this.gravityStrength = 150;
        this.gravityPullTime = 1.5; // seconds to pull before exploding
        this.gravityElapsed = 0;
        this.projectileType = null;
    }
    
    update(deltaTime) {
        // Update spin for spinning projectiles
        this.spin += deltaTime * 10;
        
        // Handle homing behavior
        if (this.homing && this.owner === 'player') {
            this.updateHoming(deltaTime);
        }
        
        // Handle gravity well behavior
        if (this.gravity && this.owner === 'player') {
            this.updateGravity(deltaTime);
        }
        
        // Handle returning projectiles
        if (this.returning && !this.hasReturned) {
            if (this.distanceTraveled >= this.range / 2) {
                this.hasReturned = true;
                // Reverse direction toward player
                const players = this.game.getEntitiesByType('player');
                if (players.length > 0) {
                    const player = players[0];
                    const dx = player.x - this.x;
                    const dy = player.y - this.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    if (distance > 0) {
                        const speed = Math.sqrt(this.vx * this.vx + this.vy * this.vy);
                        this.vx = (dx / distance) * speed;
                        this.vy = (dy / distance) * speed;
                    }
                }
            }
        }
        
        // Move projectile
        const moveX = this.vx * deltaTime;
        const moveY = this.vy * deltaTime;
        
        this.x += moveX;
        this.y += moveY;
        
        // Track distance
        this.distanceTraveled += Math.sqrt(moveX * moveX + moveY * moveY);
        
        // Add trail particle
        if (this.trailParticles.length > 5) {
            this.trailParticles.shift();
        }
        this.trailParticles.push({ x: this.x, y: this.y, life: 1.0 });
        
        // Update trail particles
        this.trailParticles.forEach(particle => {
            particle.life -= deltaTime * 3;
        });
        this.trailParticles = this.trailParticles.filter(particle => particle.life > 0);
        
        // Check if projectile should be destroyed
        if (this.returning) {
            // Returning projectiles are destroyed when they reach the player or go too far
            if (this.hasReturned) {
                const players = this.game.getEntitiesByType('player');
                if (players.length > 0) {
                    const player = players[0];
                    const dx = player.x - this.x;
                    const dy = player.y - this.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    if (distance < 20) {
                        this.active = false;
                    }
                }
            }
            if (this.distanceTraveled >= this.range * 2) {
                this.active = false;
            }
        } else {
            if (this.distanceTraveled >= this.range || this.isOffScreen()) {
                this.active = false;
            }
        }
    }
    
    updateHoming(deltaTime) {
        // Find target if we don't have one or if current target is dead
        if (!this.target || !this.target.active) {
            this.findHomingTarget();
        }
        
        // If we have a target, adjust velocity to home in on it
        if (this.target) {
            const dx = this.target.x - this.x;
            const dy = this.target.y - this.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance > 0) {
                // Calculate desired direction to target
                const targetVx = (dx / distance) * Math.sqrt(this.vx * this.vx + this.vy * this.vy);
                const targetVy = (dy / distance) * Math.sqrt(this.vx * this.vx + this.vy * this.vy);
                
                // Gradually adjust velocity toward target direction
                const homingForce = this.homingStrength * deltaTime;
                const vxDiff = targetVx - this.vx;
                const vyDiff = targetVy - this.vy;
                
                // Apply limited turning rate to make homing feel natural
                const maxTurn = homingForce;
                const turnDistance = Math.sqrt(vxDiff * vxDiff + vyDiff * vyDiff);
                
                if (turnDistance > 0) {
                    const turnRatio = Math.min(maxTurn / turnDistance, 1.0);
                    this.vx += vxDiff * turnRatio;
                    this.vy += vyDiff * turnRatio;
                }
            }
        }
    }
    
    findHomingTarget() {
        const enemies = this.game.getEntitiesByType('enemy');
        if (enemies.length === 0) {
            this.target = null;
            return;
        }
        
        // Find closest enemy within a reasonable range
        let closest = null;
        let closestDistance = Infinity;
        const maxHomingRange = 200; // Only home in on enemies within this range
        
        for (let enemy of enemies) {
            const dx = enemy.x - this.x;
            const dy = enemy.y - this.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < closestDistance && distance <= maxHomingRange) {
                closest = enemy;
                closestDistance = distance;
            }
        }
        
        this.target = closest;
    }
    
    isOffScreen() {
        const margin = 50;
        return (
            this.x < -margin ||
            this.x > this.game.canvas.width + margin ||
            this.y < -margin ||
            this.y > this.game.canvas.height + margin
        );
    }
    
    getBounds() {
        return {
            x: this.x - this.width / 2,
            y: this.y - this.height / 2,
            width: this.width,
            height: this.height
        };
    }
    
    onCollision(other) {
        // Handle collision with target
        if (this.owner === 'player' && other.type === 'enemy') {
            other.takeDamage(this.damage);
            this.enemiesHit++;
            
            // Create explosion if explosive
            if (this.explosive) {
                this.createExplosion();
            }
            
            // Chain lightning effect
            if (this.chain > 0 && this.chainsRemaining > 0) {
                this.createChainLightning(other);
                this.chainsRemaining--;
            }
            
            // Check if projectile should continue (piercing)
            if (this.enemiesHit > this.piercing) {
                this.active = false;
            }
        } else if (this.owner === 'enemy' && other.type === 'player') {
            other.takeDamage(this.damage);
            this.active = false;
        }
    }
    
    createExplosion() {
        // Find all enemies within explosion radius
        const enemies = this.game.getEntitiesByType('enemy');
        
        // Check for stacking explosion effects
        let explosionDamageMultiplier = 0.5; // Base explosion damage
        let explosionRadiusBonus = 0;
        
        // Check if player has both explosive weapon AND explosive upgrade
        const player = this.game.player;
        if (player && this.owner === 'player') {
            // Check if projectile has large explosion radius (indicating explosive weapon)
            const isFromExplosiveWeapon = this.explosionRadius >= 40; // Eclipse Orb has 40+ radius
            // Check if player has the Eclipse Burst upgrade
            const hasExplosiveUpgrade = player.explosive;
            
            if (isFromExplosiveWeapon && hasExplosiveUpgrade && this.explosionRadius > 30) {
                // Stacking explosion - bigger boom!
                explosionDamageMultiplier = 0.8; // 80% damage instead of 50%
                explosionRadiusBonus = 20; // +20 radius
            }
        }
        
        const finalExplosionRadius = this.explosionRadius + explosionRadiusBonus;
        
        for (let enemy of enemies) {
            const dx = enemy.x - this.x;
            const dy = enemy.y - this.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance <= finalExplosionRadius) {
                // Explosion damage decreases with distance
                const explosionDamage = Math.floor(this.damage * explosionDamageMultiplier * (1 - distance / finalExplosionRadius));
                if (explosionDamage > 0) {
                    enemy.takeDamage(explosionDamage);
                }
            }
        }
        
        // Visual explosion effect with enhanced size for stacking
        this.game.renderSystem.addExplosion(this.x, this.y, finalExplosionRadius);
    }
    
    createChainLightning(hitEnemy) {
        // Find nearest enemy within chain range that hasn't been hit by this projectile
        const enemies = this.game.getEntitiesByType('enemy');
        let nearestEnemy = null;
        let nearestDistance = Infinity;
        
        for (let enemy of enemies) {
            if (enemy === hitEnemy) continue; // Skip the enemy we just hit
            
            const dx = enemy.x - hitEnemy.x;
            const dy = enemy.y - hitEnemy.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance <= this.chainRange && distance < nearestDistance) {
                nearestDistance = distance;
                nearestEnemy = enemy;
            }
        }
        
        if (nearestEnemy) {
            // Deal chain damage (75% of original damage)
            const chainDamage = Math.floor(this.damage * 0.75);
            nearestEnemy.takeDamage(chainDamage);
            
            // Create visual effect for chain lightning
            this.game.renderSystem.addChainLightning(hitEnemy.x, hitEnemy.y, nearestEnemy.x, nearestEnemy.y);
            
            // Recursively chain if more chains remaining
            if (this.chainsRemaining > 1) {
                const tempProjectile = {
                    ...this,
                    chainsRemaining: this.chainsRemaining - 1,
                    createChainLightning: this.createChainLightning.bind(this)
                };
                setTimeout(() => {
                    tempProjectile.createChainLightning(nearestEnemy);
                }, 100); // Small delay for visual effect
            }
        }
    }
    
    updateGravity(deltaTime) {
        this.gravityElapsed += deltaTime;
        
        // Gravity well slows down after initial movement
        if (this.gravityElapsed > 0.3) { // Slow down after 0.3 seconds
            this.vx *= 0.95;
            this.vy *= 0.95;
        }
        
        // Find enemies within gravity range and pull them
        const enemies = this.game.getEntitiesByType('enemy');
        for (let enemy of enemies) {
            const dx = this.x - enemy.x;
            const dy = this.y - enemy.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance <= this.gravityRange && distance > 5) {
                // Calculate pull force (stronger when closer)
                const pullForce = (this.gravityStrength / (distance + 1)) * deltaTime;
                const pullX = (dx / distance) * pullForce;
                const pullY = (dy / distance) * pullForce;
                
                // Apply pull to enemy
                enemy.x += pullX;
                enemy.y += pullY;
            }
        }
        
        // Explode after gravity pull time
        if (this.gravityElapsed >= this.gravityPullTime) {
            this.createExplosion();
            this.active = false;
        }
    }
    
    render(ctx) {
        // Special rendering for gravity projectiles
        if (this.gravity && this.projectileType === 'gravity') {
            this.renderGravityWell(ctx);
            return;
        }
        
        // Render trail
        this.trailParticles.forEach((particle, index) => {
            const alpha = particle.life * 0.5;
            const size = (index / this.trailParticles.length) * this.width;
            
            ctx.fillStyle = this.color + Math.floor(alpha * 255).toString(16).padStart(2, '0');
            ctx.fillRect(
                particle.x - size / 2,
                particle.y - size / 2,
                size,
                size
            );
        });
        
        // Render projectile with rotation for spinning projectiles
        ctx.save();
        ctx.translate(this.x, this.y);
        
        if (this.spin !== undefined) {
            ctx.rotate(this.spin);
        }
        
        ctx.fillStyle = this.color;
        ctx.fillRect(
            -this.width / 2,
            -this.height / 2,
            this.width,
            this.height
        );
        
        // Add glow effect
        ctx.shadowColor = this.color;
        ctx.shadowBlur = 5;
        ctx.fillRect(
            -this.width / 2,
            -this.height / 2,
            this.width,
            this.height
        );
        ctx.shadowBlur = 0;
        ctx.restore();
    }
    
    renderGravityWell(ctx) {
        ctx.save();
        ctx.translate(this.x, this.y);
        
        // Render gravity range indicator (visible pull area)
        const pulseIntensity = 0.5 + 0.5 * Math.sin(Date.now() * 0.01);
        ctx.strokeStyle = this.color + '40'; // Semi-transparent
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.arc(0, 0, this.gravityRange * pulseIntensity, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);
        
        // Render the gravity well core
        ctx.shadowColor = this.color;
        ctx.shadowBlur = 15;
        
        // Outer ring
        ctx.strokeStyle = this.color;
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.arc(0, 0, this.width / 2 + 4, 0, Math.PI * 2);
        ctx.stroke();
        
        // Inner core
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(0, 0, this.width / 2, 0, Math.PI * 2);
        ctx.fill();
        
        // Central dark spot for gravity effect
        ctx.fillStyle = '#220033';
        ctx.beginPath();
        ctx.arc(0, 0, this.width / 4, 0, Math.PI * 2);
        ctx.fill();
        
        // Swirling effect
        const time = Date.now() * 0.005;
        for (let i = 0; i < 3; i++) {
            const angle = time + (i * Math.PI * 2 / 3);
            const radius = (this.width / 2) * (0.6 + 0.2 * Math.sin(time * 2 + i));
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;
            
            ctx.fillStyle = this.color + '80';
            ctx.beginPath();
            ctx.arc(x, y, 2, 0, Math.PI * 2);
            ctx.fill();
        }
        
        ctx.shadowBlur = 0;
        ctx.restore();
    }
}