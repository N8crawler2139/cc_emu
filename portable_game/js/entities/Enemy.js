class Enemy {
    constructor(game, x, y, enemyType = 'wraith') {
        this.game = game;
        this.type = 'enemy';
        this.x = x;
        this.y = y;
        this.active = true;
        
        // Set properties based on enemy type
        this.enemyType = enemyType;
        this.setTypeProperties();
        
        // Movement properties
        this.vx = 0;
        this.vy = 0;
        this.angle = 0;
        
        // AI properties
        this.target = null;
        this.lastPathUpdate = 0;
        this.pathUpdateInterval = 0.1; // Update path every 0.1 seconds
        
        // Visual properties
        this.hitFlash = false;
        this.hitFlashTime = 0;
        this.hitFlashDuration = 0.1;
    }
    
    setTypeProperties() {
        switch (this.enemyType) {
            case 'wraith':
                this.width = 16;
                this.height = 16;
                this.maxHealth = 20;
                this.health = this.maxHealth;
                this.speed = 100;
                this.damage = 15;
                this.xpValue = 8;
                this.color = '#8844bb';
                break;
                
            case 'bat':
                this.width = 12;
                this.height = 12;
                this.maxHealth = 5;
                this.health = this.maxHealth;
                this.speed = 200;
                this.damage = 8;
                this.xpValue = 4;
                this.color = '#bb4444';
                this.erraticMovement = true;
                this.erraticTimer = 0;
                this.erraticDirection = { x: 0, y: 0 };
                break;
                
            case 'golem':
                this.width = 24;
                this.height = 24;
                this.maxHealth = 100;
                this.health = this.maxHealth;
                this.speed = 50;
                this.damage = 30;
                this.xpValue = 20;
                this.color = '#666666';
                break;
                
            case 'cultist':
                this.width = 18;
                this.height = 18;
                this.maxHealth = 35;
                this.health = this.maxHealth;
                this.speed = 80;
                this.damage = 20;
                this.xpValue = 15;
                this.color = '#aa44aa';
                this.rangedAttack = true;
                this.lastShotTime = 0;
                this.shotCooldown = 2.0; // 2 seconds between shots
                this.attackRange = 250;
                break;
                
            case 'elite_wraith':
                this.width = 20;
                this.height = 20;
                this.maxHealth = 60;
                this.health = this.maxHealth;
                this.speed = 120;
                this.damage = 25;
                this.xpValue = 30;
                this.color = '#dd44dd';
                this.elite = true;
                break;
                
            default:
                this.setTypeProperties.call(this, 'wraith');
        }
        
        // Scale with game time for difficulty
        const timeMultiplier = 1 + (this.game.gameTime / 120); // Increase every 2 minutes
        this.maxHealth = Math.floor(this.maxHealth * timeMultiplier);
        this.health = this.maxHealth;
        this.damage = Math.floor(this.damage * timeMultiplier);
        this.xpValue = Math.floor(this.xpValue * timeMultiplier);
    }
    
    update(deltaTime) {
        this.updateAI(deltaTime);
        this.updateMovement(deltaTime);
        this.updateVisuals(deltaTime);
    }
    
    updateAI(deltaTime) {
        // Find player target
        if (!this.target || this.target.type !== 'player') {
            const players = this.game.getEntitiesByType('player');
            if (players.length > 0) {
                this.target = players[0];
            }
        }
        
        if (!this.target) return;
        
        this.lastPathUpdate += deltaTime;
        
        if (this.lastPathUpdate >= this.pathUpdateInterval) {
            this.calculateMovement();
            this.lastPathUpdate = 0;
        }
        
        // Ranged attack logic for cultists
        if (this.rangedAttack) {
            this.updateRangedAttack(deltaTime);
        }
    }
    
    calculateMovement() {
        if (!this.target) return;
        
        const dx = this.target.x - this.x;
        const dy = this.target.y - this.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        if (distance > 0) {
            if (this.enemyType === 'bat' && this.erraticMovement) {
                // Bats move erratically
                this.erraticTimer += this.lastPathUpdate;
                if (this.erraticTimer >= 0.5) {
                    this.erraticDirection.x = (Math.random() - 0.5) * 2;
                    this.erraticDirection.y = (Math.random() - 0.5) * 2;
                    this.erraticTimer = 0;
                }
                
                const normalizedX = dx / distance;
                const normalizedY = dy / distance;
                
                // Mix direct movement with erratic movement
                this.vx = (normalizedX * 0.7 + this.erraticDirection.x * 0.3) * this.speed;
                this.vy = (normalizedY * 0.7 + this.erraticDirection.y * 0.3) * this.speed;
            } else if (this.enemyType === 'cultist' && this.rangedAttack) {
                // Cultists try to maintain distance for ranged attacks
                if (distance > this.attackRange) {
                    // Move closer if too far
                    this.vx = (dx / distance) * this.speed;
                    this.vy = (dy / distance) * this.speed;
                } else if (distance < this.attackRange * 0.7) {
                    // Back away if too close
                    this.vx = -(dx / distance) * this.speed * 0.5;
                    this.vy = -(dy / distance) * this.speed * 0.5;
                } else {
                    // Stay in position and strafe
                    const perpX = -dy / distance;
                    const perpY = dx / distance;
                    this.vx = perpX * this.speed * 0.3;
                    this.vy = perpY * this.speed * 0.3;
                }
            } else {
                // Direct movement toward target
                this.vx = (dx / distance) * this.speed;
                this.vy = (dy / distance) * this.speed;
            }
            
            this.angle = Math.atan2(dy, dx);
        }
    }
    
    updateMovement(deltaTime) {
        this.x += this.vx * deltaTime;
        this.y += this.vy * deltaTime;
    }
    
    updateVisuals(deltaTime) {
        if (this.hitFlash) {
            this.hitFlashTime += deltaTime;
            if (this.hitFlashTime >= this.hitFlashDuration) {
                this.hitFlash = false;
                this.hitFlashTime = 0;
            }
        }
    }
    
    updateRangedAttack(deltaTime) {
        if (!this.target) return;
        
        this.lastShotTime += deltaTime;
        
        if (this.lastShotTime >= this.shotCooldown) {
            const dx = this.target.x - this.x;
            const dy = this.target.y - this.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            // Only shoot if player is within range
            if (distance <= this.attackRange) {
                this.fireProjectile(dx / distance, dy / distance);
                this.lastShotTime = 0;
            }
        }
    }
    
    fireProjectile(dirX, dirY) {
        const projectile = new Projectile(
            this.game,
            this.x,
            this.y,
            dirX,
            dirY,
            'enemy',
            this.damage
        );
        projectile.speed = 200;
        projectile.color = '#aa44aa';
        projectile.range = this.attackRange;
        this.game.addEntity(projectile);
    }
    
    takeDamage(amount) {
        this.health -= amount;
        this.hitFlash = true;
        this.hitFlashTime = 0;
        
        // Show damage number
        this.game.renderSystem.addDamageNumber(this.x, this.y - this.height/2, amount, '#ffff44');
        
        if (this.health <= 0) {
            this.die();
        }
    }
    
    die() {
        // Add explosion effect
        this.game.renderSystem.addExplosion(this.x, this.y, this.width);
        
        // Add experience pickup
        const pickup = new Pickup(this.game, this.x, this.y, 'xp', this.xpValue);
        this.game.addEntity(pickup);
        
        // Increment kill counter
        this.game.addKill();
        
        // Notify player of enemy kill for special effects
        if (this.game.player) {
            this.game.player.onEnemyKilled();
        }
        
        this.active = false;
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
        if (other.type === 'player') {
            other.takeDamage(this.damage);
        }
    }
    
    render(ctx) {
        ctx.save();
        
        // Move to enemy position
        ctx.translate(this.x, this.y);
        
        // Set color (flash white when hit)
        let color = this.color;
        if (this.hitFlash) {
            color = '#ffffff';
        }
        
        // Draw enemy based on type
        switch (this.enemyType) {
            case 'wraith':
                this.renderWraith(ctx, color);
                break;
            case 'bat':
                this.renderBat(ctx, color);
                break;
            case 'golem':
                this.renderGolem(ctx, color);
                break;
            case 'cultist':
                this.renderCultist(ctx, color);
                break;
            case 'elite_wraith':
                this.renderEliteWraith(ctx, color);
                break;
        }
        
        // Draw health bar for stronger enemies
        if (this.maxHealth > 20) {
            this.renderHealthBar(ctx);
        }
        
        ctx.restore();
    }
    
    renderWraith(ctx, color) {
        // Draw as a diamond/rhombus shape
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.moveTo(0, -this.height / 2);
        ctx.lineTo(this.width / 2, 0);
        ctx.lineTo(0, this.height / 2);
        ctx.lineTo(-this.width / 2, 0);
        ctx.closePath();
        ctx.fill();
        
        // Add glow effect
        ctx.shadowColor = color;
        ctx.shadowBlur = 8;
        ctx.fill();
        ctx.shadowBlur = 0;
    }
    
    renderBat(ctx, color) {
        // Draw as a small circle with wing-like extensions
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(0, 0, this.width / 2, 0, Math.PI * 2);
        ctx.fill();
        
        // Wing flapping effect
        const wingOffset = Math.sin(this.game.gameTime * 20) * 2;
        ctx.fillRect(-this.width / 2 - 2, wingOffset - 1, 4, 2);
        ctx.fillRect(this.width / 2 - 2, -wingOffset - 1, 4, 2);
    }
    
    renderGolem(ctx, color) {
        // Draw as a larger rectangle
        ctx.fillStyle = color;
        ctx.fillRect(-this.width / 2, -this.height / 2, this.width, this.height);
        
        // Add stone-like texture
        ctx.strokeStyle = '#444444';
        ctx.lineWidth = 1;
        ctx.strokeRect(-this.width / 2, -this.height / 2, this.width, this.height);
        
        // Add some detail lines
        ctx.beginPath();
        ctx.moveTo(-this.width / 4, -this.height / 2);
        ctx.lineTo(-this.width / 4, this.height / 2);
        ctx.moveTo(this.width / 4, -this.height / 2);
        ctx.lineTo(this.width / 4, this.height / 2);
        ctx.stroke();
    }
    
    renderCultist(ctx, color) {
        // Draw as a pentagram/star shape
        ctx.fillStyle = color;
        ctx.beginPath();
        
        const spikes = 5;
        const outerRadius = this.width / 2;
        const innerRadius = outerRadius * 0.4;
        
        for (let i = 0; i < spikes * 2; i++) {
            const angle = (i * Math.PI) / spikes;
            const radius = i % 2 === 0 ? outerRadius : innerRadius;
            const x = Math.cos(angle - Math.PI / 2) * radius;
            const y = Math.sin(angle - Math.PI / 2) * radius;
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        
        ctx.closePath();
        ctx.fill();
        
        // Add mystical glow
        ctx.shadowColor = color;
        ctx.shadowBlur = 10;
        ctx.fill();
        ctx.shadowBlur = 0;
        
        // Add eye in the center
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(0, 0, 2, 0, Math.PI * 2);
        ctx.fill();
    }
    
    renderEliteWraith(ctx, color) {
        // Draw as a larger diamond with spikes
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.moveTo(0, -this.height / 2);
        ctx.lineTo(this.width / 2, 0);
        ctx.lineTo(0, this.height / 2);
        ctx.lineTo(-this.width / 2, 0);
        ctx.closePath();
        ctx.fill();
        
        // Add spikes
        ctx.beginPath();
        ctx.moveTo(0, -this.height / 2 - 3);
        ctx.lineTo(-3, -this.height / 2 + 3);
        ctx.lineTo(3, -this.height / 2 + 3);
        ctx.closePath();
        ctx.fill();
        
        // Add additional spikes on sides
        ctx.fillRect(-this.width / 2 - 3, -2, 6, 4);
        ctx.fillRect(this.width / 2 - 3, -2, 6, 4);
        
        // Add intense glow effect for elite
        ctx.shadowColor = color;
        ctx.shadowBlur = 15;
        ctx.fill();
        ctx.shadowBlur = 0;
        
        // Add pulsing inner core
        const pulseIntensity = Math.sin(this.game.gameTime * 5) * 0.5 + 0.5;
        ctx.fillStyle = '#ffffff';
        ctx.globalAlpha = pulseIntensity * 0.5;
        ctx.beginPath();
        ctx.arc(0, 0, 3, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1;
    }
    
    renderHealthBar(ctx) {
        const barWidth = this.width + 4;
        const barHeight = 3;
        const healthPercent = this.health / this.maxHealth;
        
        // Background
        ctx.fillStyle = '#333333';
        ctx.fillRect(-barWidth / 2, -this.height / 2 - 8, barWidth, barHeight);
        
        // Health fill
        ctx.fillStyle = healthPercent > 0.5 ? '#44ff44' : (healthPercent > 0.25 ? '#ffff44' : '#ff4444');
        ctx.fillRect(-barWidth / 2, -this.height / 2 - 8, barWidth * healthPercent, barHeight);
        
        // Border
        ctx.strokeStyle = '#666666';
        ctx.lineWidth = 1;
        ctx.strokeRect(-barWidth / 2, -this.height / 2 - 8, barWidth, barHeight);
    }
}