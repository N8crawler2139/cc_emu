class CollisionSystem {
    constructor(game) {
        this.game = game;
    }
    
    update() {
        const entities = Array.from(this.game.entities.values());
        
        // Check all entity pairs for collisions
        for (let i = 0; i < entities.length; i++) {
            const entityA = entities[i];
            if (!entityA.active) continue;
            
            for (let j = i + 1; j < entities.length; j++) {
                const entityB = entities[j];
                if (!entityB.active) continue;
                
                if (this.checkCollision(entityA, entityB)) {
                    this.handleCollision(entityA, entityB);
                }
            }
        }
    }
    
    checkCollision(entityA, entityB) {
        // Skip if same entity or both are same type (except player-enemy)
        if (entityA === entityB) return false;
        
        // Only check relevant collision pairs
        if (!this.shouldCheckCollision(entityA, entityB)) return false;
        
        const boundsA = entityA.getBounds();
        const boundsB = entityB.getBounds();
        
        return this.rectangleIntersection(boundsA, boundsB);
    }
    
    shouldCheckCollision(entityA, entityB) {
        const typeA = entityA.type;
        const typeB = entityB.type;
        
        // Player vs Enemy
        if ((typeA === 'player' && typeB === 'enemy') || 
            (typeA === 'enemy' && typeB === 'player')) {
            return true;
        }
        
        // Player vs Pickup
        if ((typeA === 'player' && typeB === 'pickup') || 
            (typeA === 'pickup' && typeB === 'player')) {
            return true;
        }
        
        // Projectile vs Enemy (player projectiles)
        if (typeA === 'projectile' && typeB === 'enemy' && entityA.owner === 'player') {
            return true;
        }
        if (typeA === 'enemy' && typeB === 'projectile' && entityB.owner === 'player') {
            return true;
        }
        
        // Projectile vs Player (enemy projectiles)
        if (typeA === 'projectile' && typeB === 'player' && entityA.owner === 'enemy') {
            return true;
        }
        if (typeA === 'player' && typeB === 'projectile' && entityB.owner === 'enemy') {
            return true;
        }
        
        return false;
    }
    
    rectangleIntersection(rectA, rectB) {
        return !(
            rectA.x + rectA.width < rectB.x ||
            rectB.x + rectB.width < rectA.x ||
            rectA.y + rectA.height < rectB.y ||
            rectB.y + rectB.height < rectA.y
        );
    }
    
    handleCollision(entityA, entityB) {
        // Call collision handlers on both entities if they exist
        if (typeof entityA.onCollision === 'function') {
            entityA.onCollision(entityB);
        }
        
        if (typeof entityB.onCollision === 'function') {
            entityB.onCollision(entityA);
        }
        
        // Handle specific collision types
        this.handleSpecificCollisions(entityA, entityB);
    }
    
    handleSpecificCollisions(entityA, entityB) {
        // Player vs Pickup
        if ((entityA.type === 'player' && entityB.type === 'pickup') ||
            (entityA.type === 'pickup' && entityB.type === 'player')) {
            
            const pickup = entityA.type === 'pickup' ? entityA : entityB;
            if (!pickup.collected) {
                pickup.collect();
            }
        }
        
        // Projectile vs Enemy - let projectile handle its own collision logic
        // (This is handled by the projectile's onCollision method)
        
        // Projectile vs Player
        if ((entityA.type === 'projectile' && entityB.type === 'player' && entityA.owner === 'enemy') ||
            (entityA.type === 'player' && entityB.type === 'projectile' && entityB.owner === 'enemy')) {
            
            const projectile = entityA.type === 'projectile' ? entityA : entityB;
            const player = entityA.type === 'player' ? entityA : entityB;
            
            player.takeDamage(projectile.damage);
            projectile.active = false;
        }
        
        // Player vs Enemy (direct contact)
        if ((entityA.type === 'player' && entityB.type === 'enemy') ||
            (entityA.type === 'enemy' && entityB.type === 'player')) {
            
            const player = entityA.type === 'player' ? entityA : entityB;
            const enemy = entityA.type === 'enemy' ? entityA : entityB;
            
            // Apply damage to player
            player.takeDamage(enemy.damage);
        }
    }
    
    // Utility method for circle collision (not used currently but useful for future)
    circleIntersection(circleA, circleB) {
        const dx = circleA.x - circleB.x;
        const dy = circleA.y - circleB.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        return distance < (circleA.radius + circleB.radius);
    }
    
    // Utility method for point-in-rectangle collision
    pointInRectangle(point, rect) {
        return (
            point.x >= rect.x &&
            point.x <= rect.x + rect.width &&
            point.y >= rect.y &&
            point.y <= rect.y + rect.height
        );
    }
}