class RenderSystem {
    constructor(game) {
        this.game = game;
        this.ctx = game.ctx;
        
        // Rendering layers for proper z-ordering
        this.renderLayers = {
            background: [],
            pickups: [],
            enemies: [],
            projectiles: [],
            player: [],
            effects: [],
            ui: []
        };
        
        // Explosion effects
        this.explosions = [];
        
        // Chain lightning effects
        this.chainLightning = [];
        
        // Damage numbers
        this.damageNumbers = [];
    }
    
    render() {
        // Clear previous frame layers
        this.clearLayers();
        
        // Sort entities into render layers
        this.sortEntitiesIntoLayers();
        
        // Render each layer in order
        this.renderLayer('background');
        this.renderLayer('pickups');
        this.renderLayer('enemies');
        this.renderLayer('projectiles');
        this.renderLayer('player');
        this.renderExplosions();
        this.renderChainLightning();
        this.renderDamageNumbers();
        this.renderLayer('effects');
        this.renderLayer('ui');
    }
    
    clearLayers() {
        for (let layer in this.renderLayers) {
            this.renderLayers[layer].length = 0;
        }
    }
    
    sortEntitiesIntoLayers() {
        for (let [id, entity] of this.game.entities) {
            if (!entity.active) continue;
            
            switch (entity.type) {
                case 'player':
                    this.renderLayers.player.push(entity);
                    break;
                case 'enemy':
                    this.renderLayers.enemies.push(entity);
                    break;
                case 'projectile':
                    this.renderLayers.projectiles.push(entity);
                    break;
                case 'pickup':
                    this.renderLayers.pickups.push(entity);
                    break;
                default:
                    this.renderLayers.effects.push(entity);
                    break;
            }
        }
    }
    
    renderLayer(layerName) {
        const entities = this.renderLayers[layerName];
        
        for (let entity of entities) {
            if (entity.render && typeof entity.render === 'function') {
                this.ctx.save();
                entity.render(this.ctx);
                this.ctx.restore();
            }
        }
    }
    
    // Utility methods for rendering effects
    renderExplosion(x, y, radius, color = '#ff4444') {
        this.ctx.save();
        
        // Outer glow
        this.ctx.shadowColor = color;
        this.ctx.shadowBlur = 20;
        this.ctx.fillStyle = color + '40'; // Semi-transparent
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Inner bright flash
        this.ctx.shadowBlur = 10;
        this.ctx.fillStyle = '#ffffff';
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius * 0.3, 0, Math.PI * 2);
        this.ctx.fill();
        
        this.ctx.restore();
    }
    
    renderLightning(startX, startY, endX, endY, color = '#4444ff') {
        this.ctx.save();
        
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 2;
        this.ctx.shadowColor = color;
        this.ctx.shadowBlur = 5;
        
        this.ctx.beginPath();
        this.ctx.moveTo(startX, startY);
        
        // Add some randomness to make it look like lightning
        const segments = 5;
        for (let i = 1; i <= segments; i++) {
            const progress = i / segments;
            const x = startX + (endX - startX) * progress + (Math.random() - 0.5) * 20;
            const y = startY + (endY - startY) * progress + (Math.random() - 0.5) * 20;
            this.ctx.lineTo(x, y);
        }
        
        this.ctx.stroke();
        this.ctx.restore();
    }
    
    renderShockwave(x, y, radius, color = '#ff4444') {
        this.ctx.save();
        
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 3;
        this.ctx.shadowColor = color;
        this.ctx.shadowBlur = 10;
        
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius, 0, Math.PI * 2);
        this.ctx.stroke();
        
        this.ctx.restore();
    }
    
    renderDamageNumber(x, y, damage, color = '#ff4444') {
        this.ctx.save();
        
        this.ctx.font = 'bold 16px monospace';
        this.ctx.fillStyle = color;
        this.ctx.strokeStyle = '#000000';
        this.ctx.lineWidth = 2;
        this.ctx.textAlign = 'center';
        
        // Add glow effect
        this.ctx.shadowColor = color;
        this.ctx.shadowBlur = 5;
        
        const text = damage.toString();
        this.ctx.strokeText(text, x, y);
        this.ctx.fillText(text, x, y);
        
        this.ctx.restore();
    }
    
    // Screen shake effect
    applyScreenShake(intensity = 5) {
        const shakeX = (Math.random() - 0.5) * intensity;
        const shakeY = (Math.random() - 0.5) * intensity;
        
        this.ctx.save();
        this.ctx.translate(shakeX, shakeY);
    }
    
    removeScreenShake() {
        this.ctx.restore();
    }
    
    // Particle system for simple effects
    renderParticles(particles) {
        for (let particle of particles) {
            if (particle.life <= 0) continue;
            
            this.ctx.save();
            
            this.ctx.globalAlpha = particle.life / particle.maxLife;
            this.ctx.fillStyle = particle.color;
            
            const size = particle.size * (particle.life / particle.maxLife);
            this.ctx.fillRect(
                particle.x - size / 2,
                particle.y - size / 2,
                size,
                size
            );
            
            this.ctx.restore();
        }
    }
    
    // Explosion effect management
    addExplosion(x, y, radius) {
        this.explosions.push({
            x: x,
            y: y,
            radius: radius,
            life: 0.5, // Duration in seconds
            maxLife: 0.5
        });
    }
    
    updateExplosions(deltaTime) {
        this.explosions = this.explosions.filter(explosion => {
            explosion.life -= deltaTime;
            return explosion.life > 0;
        });
    }
    
    renderExplosions() {
        for (let explosion of this.explosions) {
            const progress = 1 - (explosion.life / explosion.maxLife);
            const currentRadius = explosion.radius * (0.5 + progress * 0.5);
            const alpha = explosion.life / explosion.maxLife;
            
            this.ctx.save();
            this.ctx.globalAlpha = alpha;
            this.renderExplosion(explosion.x, explosion.y, currentRadius);
            this.ctx.restore();
        }
    }
    
    // Chain lightning effect management
    addChainLightning(x1, y1, x2, y2) {
        this.chainLightning.push({
            x1: x1,
            y1: y1,
            x2: x2,
            y2: y2,
            life: 0.3, // Duration in seconds
            maxLife: 0.3
        });
    }
    
    updateChainLightning(deltaTime) {
        this.chainLightning = this.chainLightning.filter(lightning => {
            lightning.life -= deltaTime;
            return lightning.life > 0;
        });
    }
    
    renderChainLightning() {
        for (let lightning of this.chainLightning) {
            const alpha = lightning.life / lightning.maxLife;
            
            this.ctx.save();
            this.ctx.globalAlpha = alpha;
            this.ctx.strokeStyle = '#44ffff';
            this.ctx.lineWidth = 3;
            this.ctx.shadowColor = '#44ffff';
            this.ctx.shadowBlur = 10;
            
            // Draw main lightning bolt
            this.ctx.beginPath();
            this.ctx.moveTo(lightning.x1, lightning.y1);
            
            // Add some randomness to make it look like lightning
            const segments = 3;
            const dx = (lightning.x2 - lightning.x1) / segments;
            const dy = (lightning.y2 - lightning.y1) / segments;
            
            for (let i = 1; i < segments; i++) {
                const x = lightning.x1 + dx * i + (Math.random() - 0.5) * 10;
                const y = lightning.y1 + dy * i + (Math.random() - 0.5) * 10;
                this.ctx.lineTo(x, y);
            }
            
            this.ctx.lineTo(lightning.x2, lightning.y2);
            this.ctx.stroke();
            
            this.ctx.restore();
        }
    }
    
    // Damage numbers management
    addDamageNumber(x, y, damage, color = '#ff4444') {
        this.damageNumbers.push({
            x: x,
            y: y,
            damage: damage,
            color: color,
            life: 1.0, // Duration in seconds
            maxLife: 1.0,
            velocity: -60, // Pixels per second upward
            startY: y
        });
    }
    
    updateDamageNumbers(deltaTime) {
        this.damageNumbers = this.damageNumbers.filter(damageNumber => {
            damageNumber.life -= deltaTime;
            damageNumber.y += damageNumber.velocity * deltaTime;
            return damageNumber.life > 0;
        });
    }
    
    renderDamageNumbers() {
        for (let damageNumber of this.damageNumbers) {
            const progress = 1 - (damageNumber.life / damageNumber.maxLife);
            const alpha = damageNumber.life / damageNumber.maxLife;
            const scale = 1 + (progress * 0.5); // Grow slightly as it fades
            
            this.ctx.save();
            this.ctx.globalAlpha = alpha;
            this.ctx.font = `bold ${16 * scale}px monospace`;
            this.ctx.fillStyle = damageNumber.color;
            this.ctx.strokeStyle = '#000000';
            this.ctx.lineWidth = 2;
            this.ctx.textAlign = 'center';
            
            // Add glow effect
            this.ctx.shadowColor = damageNumber.color;
            this.ctx.shadowBlur = 8;
            
            const text = damageNumber.damage.toString();
            this.ctx.strokeText(text, damageNumber.x, damageNumber.y);
            this.ctx.fillText(text, damageNumber.x, damageNumber.y);
            
            this.ctx.restore();
        }
    }
}