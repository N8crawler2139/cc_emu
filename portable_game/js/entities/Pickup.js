class Pickup {
    constructor(game, x, y, type, value) {
        this.game = game;
        this.type = 'pickup';
        this.x = x;
        this.y = y;
        this.pickupType = type; // 'xp', 'health', 'powerup'
        this.value = value;
        this.active = true;
        
        this.width = 8;
        this.height = 8;
        
        // Visual properties
        this.pulseTime = 0;
        this.collected = false;
        this.collectAnimationTime = 0;
        this.collectAnimationDuration = 0.3;
        
        // Movement toward player
        this.magnetRange = 80;
        this.magnetSpeed = 200;
        
        // Set color based on type
        switch (this.pickupType) {
            case 'xp':
                this.color = '#4466ff';
                this.glowColor = '#6688ff';
                break;
            case 'health':
                this.color = '#ff4444';
                this.glowColor = '#ff6666';
                break;
            case 'powerup':
                this.color = '#44ff44';
                this.glowColor = '#66ff66';
                break;
            default:
                this.color = '#ffffff';
                this.glowColor = '#ffffff';
        }
    }
    
    update(deltaTime) {
        this.pulseTime += deltaTime;
        
        if (this.collected) {
            this.updateCollectAnimation(deltaTime);
        } else {
            this.updateMagnetism(deltaTime);
            this.checkPlayerCollection();
        }
    }
    
    updateMagnetism(deltaTime) {
        // Check if player is within magnet range
        const players = this.game.getEntitiesByType('player');
        if (players.length === 0) return;
        
        const player = players[0];
        const dx = player.x - this.x;
        const dy = player.y - this.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        // Use player's magnet range if it exists, otherwise use default
        const magnetRange = player.magnetRange || this.magnetRange;
        
        if (distance <= magnetRange && distance > 0) {
            // Move toward player
            const normalizedX = dx / distance;
            const normalizedY = dy / distance;
            
            this.x += normalizedX * this.magnetSpeed * deltaTime;
            this.y += normalizedY * this.magnetSpeed * deltaTime;
        }
    }
    
    checkPlayerCollection() {
        const players = this.game.getEntitiesByType('player');
        if (players.length === 0) return;
        
        const player = players[0];
        const dx = player.x - this.x;
        const dy = player.y - this.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        // Check for collection (closer range than magnetism)
        if (distance <= 15) {
            this.collect();
        }
    }
    
    collect() {
        if (this.collected) return;
        
        this.collected = true;
        
        // Apply pickup effect
        switch (this.pickupType) {
            case 'xp':
                this.game.addXP(this.value);
                break;
            case 'health':
                this.game.stats.health = Math.min(
                    this.game.stats.health + this.value,
                    this.game.stats.maxHealth
                );
                break;
            case 'powerup':
                this.applyPowerupEffect();
                break;
        }
    }
    
    updateCollectAnimation(deltaTime) {
        this.collectAnimationTime += deltaTime;
        
        if (this.collectAnimationTime >= this.collectAnimationDuration) {
            this.active = false;
        }
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
        if (!this.active) return;
        
        ctx.save();
        ctx.translate(this.x, this.y);
        
        if (this.collected) {
            // Collection animation - scale up and fade out
            const progress = this.collectAnimationTime / this.collectAnimationDuration;
            const scale = 1 + progress * 2;
            const alpha = 1 - progress;
            
            ctx.scale(scale, scale);
            ctx.globalAlpha = alpha;
        }
        
        // Pulsing effect
        const pulseScale = 1 + Math.sin(this.pulseTime * 8) * 0.1;
        ctx.scale(pulseScale, pulseScale);
        
        // Glow effect
        ctx.shadowColor = this.glowColor;
        ctx.shadowBlur = 10;
        
        // Draw pickup based on type
        switch (this.pickupType) {
            case 'xp':
                this.renderXP(ctx);
                break;
            case 'health':
                this.renderHealth(ctx);
                break;
            case 'powerup':
                this.renderPowerup(ctx);
                break;
        }
        
        ctx.shadowBlur = 0;
        ctx.restore();
    }
    
    renderXP(ctx) {
        // Draw as a glowing orb
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(0, 0, this.width / 2, 0, Math.PI * 2);
        ctx.fill();
        
        // Inner bright core
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(0, 0, this.width / 4, 0, Math.PI * 2);
        ctx.fill();
    }
    
    renderHealth(ctx) {
        // Draw as a cross/plus symbol
        ctx.fillStyle = this.color;
        
        // Horizontal bar
        ctx.fillRect(-this.width / 2, -this.height / 6, this.width, this.height / 3);
        
        // Vertical bar
        ctx.fillRect(-this.width / 6, -this.height / 2, this.width / 3, this.height);
        
        // White highlight
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(-this.width / 3, -this.height / 12, this.width / 1.5, this.height / 6);
        ctx.fillRect(-this.width / 12, -this.height / 3, this.width / 6, this.height / 1.5);
    }
    
    renderPowerup(ctx) {
        // Draw as a star
        ctx.fillStyle = this.color;
        ctx.beginPath();
        
        const spikes = 5;
        const outerRadius = this.width / 2;
        const innerRadius = outerRadius * 0.5;
        
        for (let i = 0; i < spikes * 2; i++) {
            const angle = (i * Math.PI) / spikes;
            const radius = i % 2 === 0 ? outerRadius : innerRadius;
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        
        ctx.closePath();
        ctx.fill();
        
        // Inner glow
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(0, 0, innerRadius / 2, 0, Math.PI * 2);
        ctx.fill();
    }
    
    applyPowerupEffect() {
        // Random powerup effects
        const powerups = [
            'tempDamage',
            'tempSpeed',
            'tempFireRate',
            'shield',
            'magnet'
        ];
        
        const powerup = powerups[Math.floor(Math.random() * powerups.length)];
        const player = this.game.player;
        
        if (!player) return;
        
        // Get power-up duration multiplier from meta progression
        const baseDuration = {
            tempDamage: 10000,
            tempSpeed: 8000,
            tempFireRate: 12000,
            shield: 5000,
            magnet: 15000
        };
        
        const durationMultiplier = this.getPowerUpDurationMultiplier();
        
        switch (powerup) {
            case 'tempDamage':
                this.applyTemporaryBoost(player, 'damage', 1.5, baseDuration.tempDamage * durationMultiplier); // 50% more damage
                this.game.upgradeSystem.showUpgradeNotification('Damage Boost!');
                break;
            case 'tempSpeed':
                this.applyTemporaryBoost(player, 'speed', 1.3, baseDuration.tempSpeed * durationMultiplier); // 30% more speed
                this.game.upgradeSystem.showUpgradeNotification('Speed Boost!');
                break;
            case 'tempFireRate':
                this.applyTemporaryBoost(player, 'fireRate', 0.7, baseDuration.tempFireRate * durationMultiplier); // Faster fire rate
                this.game.upgradeSystem.showUpgradeNotification('Rapid Fire!');
                break;
            case 'shield':
                player.invulnerabilityTime = Math.min(player.invulnerabilityTime, 0.1); // Reduced invuln time
                this.applyTemporaryShield(player, baseDuration.shield * durationMultiplier); // Enhanced protection
                this.game.upgradeSystem.showUpgradeNotification('Eclipse Shield!');
                break;
            case 'magnet':
                this.applyTemporaryBoost(player, 'magnetRange', 3, baseDuration.magnet * durationMultiplier); // 3x magnet range
                this.game.upgradeSystem.showUpgradeNotification('Soul Magnet!');
                break;
        }
    }
    
    getPowerUpDurationMultiplier() {
        // Get duration bonus from meta progression
        const metaSystem = this.game.metaSystem;
        if (metaSystem && metaSystem.metaData && metaSystem.metaData.permanentUpgrades) {
            const powerUpLevel = metaSystem.metaData.permanentUpgrades.powerUpDuration || 0;
            return 1 + (powerUpLevel * 0.2); // 20% longer per level
        }
        return 1.0;
    }
    
    applyTemporaryBoost(player, property, multiplier, duration) {
        const originalValue = player[property];
        const boostedValue = property === 'fireRate' ? originalValue * multiplier : originalValue * multiplier;
        
        // Apply boost
        player[property] = boostedValue;
        
        // Store boost info for visual indication
        if (!player.activeBoosts) player.activeBoosts = [];
        player.activeBoosts.push({
            property: property,
            originalValue: originalValue,
            endTime: Date.now() + duration
        });
        
        // Remove boost after duration
        setTimeout(() => {
            player[property] = originalValue;
            // Remove from active boosts
            if (player.activeBoosts) {
                player.activeBoosts = player.activeBoosts.filter(boost => 
                    boost.property !== property || boost.endTime !== Date.now() + duration
                );
            }
        }, duration);
    }
    
    applyTemporaryShield(player, duration) {
        player.shielded = true;
        player.shieldEndTime = Date.now() + duration;
        
        setTimeout(() => {
            player.shielded = false;
            player.shieldEndTime = 0;
        }, duration);
    }
}