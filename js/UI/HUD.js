class HUD {
    constructor(game) {
        this.game = game;
        
        // Get UI elements
        this.levelDisplay = document.getElementById('levelDisplay');
        this.healthText = document.getElementById('healthText');
        this.healthFill = document.getElementById('healthFill');
        this.xpText = document.getElementById('xpText');
        this.xpFill = document.getElementById('xpFill');
        this.timeDisplay = document.getElementById('timeDisplay');
        this.killDisplay = document.getElementById('killDisplay');
    }
    
    update() {
        this.updateLevel();
        this.updateHealth();
        this.updateExperience();
        this.updateTime();
        this.updateKills();
        this.updateBuffIndicators();
        this.updateWeaponSlots();
        this.updateUpgradeDisplay();
    }
    
    updateLevel() {
        if (this.levelDisplay) {
            this.levelDisplay.textContent = this.game.stats.level;
        }
    }
    
    updateHealth() {
        const health = this.game.stats.health;
        const maxHealth = this.game.stats.maxHealth;
        const healthPercent = (health / maxHealth) * 100;
        
        if (this.healthText) {
            this.healthText.textContent = `${Math.max(0, Math.floor(health))}/${maxHealth}`;
        }
        
        if (this.healthFill) {
            this.healthFill.style.width = `${Math.max(0, healthPercent)}%`;
            
            // Change color based on health percentage
            if (healthPercent > 60) {
                this.healthFill.style.background = 'linear-gradient(90deg, #00ff00, #44ff44)';
            } else if (healthPercent > 30) {
                this.healthFill.style.background = 'linear-gradient(90deg, #ffff00, #ffff44)';
            } else {
                this.healthFill.style.background = 'linear-gradient(90deg, #ff0000, #ff4444)';
            }
        }
    }
    
    updateExperience() {
        const xp = this.game.stats.xp;
        const xpRequired = this.game.stats.xpRequired;
        const xpPercent = (xp / xpRequired) * 100;
        
        if (this.xpText) {
            this.xpText.textContent = `${xp}/${xpRequired}`;
        }
        
        if (this.xpFill) {
            this.xpFill.style.width = `${xpPercent}%`;
        }
    }
    
    updateTime() {
        if (this.timeDisplay) {
            const totalSeconds = Math.floor(this.game.stats.time);
            const minutes = Math.floor(totalSeconds / 60);
            const seconds = totalSeconds % 60;
            
            this.timeDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
    }
    
    updateKills() {
        if (this.killDisplay) {
            this.killDisplay.textContent = this.game.stats.kills;
        }
    }
    
    updateBuffIndicators() {
        // Get or create buff indicators container
        let buffContainer = document.getElementById('buffIndicators');
        if (!buffContainer) {
            buffContainer = document.createElement('div');
            buffContainer.id = 'buffIndicators';
            buffContainer.style.cssText = `
                position: absolute;
                top: 120px;
                left: 20px;
                display: flex;
                flex-direction: column;
                gap: 5px;
                pointer-events: none;
                z-index: 100;
            `;
            document.body.appendChild(buffContainer);
        }
        
        // Clear existing indicators
        buffContainer.innerHTML = '';
        
        // Get active buffs from player
        if (this.game.player) {
            const buffs = this.game.player.getActiveBuffs();
            
            buffs.forEach(buff => {
                const buffElement = document.createElement('div');
                buffElement.style.cssText = `
                    background: rgba(0, 0, 0, 0.7);
                    border: 1px solid ${buff.color};
                    color: ${buff.color};
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-family: monospace;
                    font-size: 12px;
                    display: flex;
                    align-items: center;
                    gap: 5px;
                    min-width: 100px;
                `;
                
                let text = buff.name;
                if (buff.stacks) {
                    text += ` (${buff.stacks})`;
                }
                if (buff.timeLeft) {
                    text += ` ${Math.ceil(buff.timeLeft)}s`;
                }
                
                buffElement.textContent = text;
                buffContainer.appendChild(buffElement);
            });
        }
    }
    
    // Show damage indicators on screen
    showDamageIndicator(x, y, damage, color = '#ff4444') {
        const indicator = document.createElement('div');
        indicator.style.position = 'absolute';
        indicator.style.left = `${x}px`;
        indicator.style.top = `${y}px`;
        indicator.style.color = color;
        indicator.style.fontSize = '16px';
        indicator.style.fontWeight = 'bold';
        indicator.style.fontFamily = 'monospace';
        indicator.style.pointerEvents = 'none';
        indicator.style.zIndex = '1000';
        indicator.style.textShadow = '1px 1px 2px rgba(0, 0, 0, 0.8)';
        indicator.textContent = `-${damage}`;
        
        document.body.appendChild(indicator);
        
        // Animate the indicator
        let yOffset = 0;
        let opacity = 1;
        const animation = setInterval(() => {
            yOffset += 2;
            opacity -= 0.05;
            
            indicator.style.transform = `translateY(-${yOffset}px)`;
            indicator.style.opacity = opacity;
            
            if (opacity <= 0) {
                clearInterval(animation);
                document.body.removeChild(indicator);
            }
        }, 50);
    }
    
    // Show level up notification
    showLevelUpNotification() {
        const notification = document.createElement('div');
        notification.style.position = 'fixed';
        notification.style.top = '50%';
        notification.style.left = '50%';
        notification.style.transform = 'translate(-50%, -50%)';
        notification.style.color = '#ffff00';
        notification.style.fontSize = '32px';
        notification.style.fontWeight = 'bold';
        notification.style.fontFamily = 'monospace';
        notification.style.textAlign = 'center';
        notification.style.pointerEvents = 'none';
        notification.style.zIndex = '1001';
        notification.style.textShadow = '2px 2px 4px rgba(0, 0, 0, 0.8)';
        notification.innerHTML = 'LEVEL UP!<br><span style="font-size: 16px;">Health Restored!</span>';
        
        document.body.appendChild(notification);
        
        // Animate the notification
        let scale = 0.5;
        let opacity = 1;
        const growPhase = setInterval(() => {
            scale += 0.1;
            notification.style.transform = `translate(-50%, -50%) scale(${scale})`;
            
            if (scale >= 1.2) {
                clearInterval(growPhase);
                
                setTimeout(() => {
                    const fadePhase = setInterval(() => {
                        opacity -= 0.05;
                        notification.style.opacity = opacity;
                        
                        if (opacity <= 0) {
                            clearInterval(fadePhase);
                            document.body.removeChild(notification);
                        }
                    }, 50);
                }, 1000);
            }
        }, 50);
    }
    
    // Show game over screen
    showGameOverScreen(stats) {
        const overlay = document.createElement('div');
        overlay.style.position = 'fixed';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.width = '100%';
        overlay.style.height = '100%';
        overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
        overlay.style.color = '#ff4444';
        overlay.style.fontFamily = 'monospace';
        overlay.style.display = 'flex';
        overlay.style.flexDirection = 'column';
        overlay.style.justifyContent = 'center';
        overlay.style.alignItems = 'center';
        overlay.style.zIndex = '1002';
        
        const minutes = Math.floor(stats.time / 60);
        const seconds = Math.floor(stats.time % 60);
        
        overlay.innerHTML = `
            <h1 style="font-size: 48px; margin-bottom: 20px; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);">GAME OVER</h1>
            <div style="font-size: 18px; text-align: center; margin-bottom: 30px;">
                <p>Time Survived: ${minutes}:${seconds.toString().padStart(2, '0')}</p>
                <p>Enemies Defeated: ${stats.kills}</p>
                <p>Level Reached: ${stats.level}</p>
            </div>
            <button onclick="location.reload()" style="
                background: rgba(255, 68, 68, 0.2);
                border: 2px solid #ff4444;
                color: #ff4444;
                padding: 15px 30px;
                font-size: 18px;
                font-family: inherit;
                cursor: pointer;
                transition: all 0.3s ease;
            ">PLAY AGAIN</button>
        `;
        
        document.body.appendChild(overlay);
    }
    
    updateWeaponSlots() {
        // Get or create weapon slots container
        let weaponSlotsContainer = document.getElementById('weaponSlots');
        if (!weaponSlotsContainer) {
            weaponSlotsContainer = document.createElement('div');
            weaponSlotsContainer.id = 'weaponSlots';
            weaponSlotsContainer.style.cssText = `
                position: absolute;
                top: 20px;
                right: 20px;
                display: flex;
                flex-direction: column;
                gap: 8px;
                pointer-events: none;
                z-index: 100;
            `;
            document.body.appendChild(weaponSlotsContainer);
        }
        
        // Clear existing slots
        weaponSlotsContainer.innerHTML = '';
        
        if (this.game.player && this.game.player.weapons) {
            // Add title
            const title = document.createElement('div');
            title.style.cssText = `
                color: #ff4444;
                font-family: monospace;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
                text-align: center;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
            `;
            title.textContent = `WEAPONS (${this.game.player.weapons.length}/${this.game.player.maxWeapons})`;
            weaponSlotsContainer.appendChild(title);
            
            // Add weapon slots
            this.game.player.weapons.forEach((weapon, index) => {
                const weaponData = this.game.weaponSystem.weaponTypes[weapon.type];
                if (!weaponData) return;
                
                const slot = document.createElement('div');
                slot.style.cssText = `
                    background: rgba(0, 0, 0, 0.7);
                    border: 2px solid ${weaponData.color || '#ff4444'};
                    border-radius: 5px;
                    padding: 8px;
                    min-width: 120px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                `;
                
                // Weapon icon (simple colored square)
                const icon = document.createElement('div');
                icon.style.cssText = `
                    width: 16px;
                    height: 16px;
                    background: ${weaponData.color || '#ff4444'};
                    border-radius: 2px;
                    flex-shrink: 0;
                `;
                slot.appendChild(icon);
                
                // Weapon info
                const info = document.createElement('div');
                info.style.cssText = `
                    color: ${weaponData.color || '#ff4444'};
                    font-family: monospace;
                    font-size: 12px;
                    line-height: 1.2;
                `;
                
                const name = document.createElement('div');
                name.style.fontWeight = 'bold';
                name.textContent = weaponData.name;
                info.appendChild(name);
                
                const stats = document.createElement('div');
                stats.style.opacity = '0.8';
                stats.textContent = `DMG: ${Math.round(weapon.damage)} | FR: ${weapon.fireRate.toFixed(1)}s`;
                info.appendChild(stats);
                
                slot.appendChild(info);
                weaponSlotsContainer.appendChild(slot);
            });
            
            // Add empty slots if not at max
            for (let i = this.game.player.weapons.length; i < this.game.player.maxWeapons; i++) {
                const emptySlot = document.createElement('div');
                emptySlot.style.cssText = `
                    background: rgba(0, 0, 0, 0.3);
                    border: 2px dashed rgba(255, 68, 68, 0.3);
                    border-radius: 5px;
                    padding: 8px;
                    min-width: 120px;
                    height: 40px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: rgba(255, 68, 68, 0.5);
                    font-family: monospace;
                    font-size: 12px;
                `;
                emptySlot.textContent = 'Empty Slot';
                weaponSlotsContainer.appendChild(emptySlot);
            }
        }
    }
    
    updateUpgradeDisplay() {
        // Get or create upgrade display container
        let upgradeDisplayContainer = document.getElementById('upgradeDisplay');
        if (!upgradeDisplayContainer) {
            upgradeDisplayContainer = document.createElement('div');
            upgradeDisplayContainer.id = 'upgradeDisplay';
            upgradeDisplayContainer.style.cssText = `
                position: absolute;
                top: 350px;
                right: 20px;
                display: flex;
                flex-direction: column;
                gap: 4px;
                pointer-events: none;
                z-index: 100;
                max-width: 200px;
            `;
            document.body.appendChild(upgradeDisplayContainer);
        }
        
        // Clear existing display
        upgradeDisplayContainer.innerHTML = '';
        
        if (this.game.player && this.game.player.collectedUpgrades && this.game.player.collectedUpgrades.length > 0) {
            // Add title
            const title = document.createElement('div');
            title.style.cssText = `
                color: #44ff44;
                font-family: monospace;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
                text-align: center;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
            `;
            title.textContent = `UPGRADES (${this.game.player.collectedUpgrades.length})`;
            upgradeDisplayContainer.appendChild(title);
            
            // Add upgrade list
            this.game.player.collectedUpgrades.forEach((upgradeKey, index) => {
                const upgrade = this.game.upgradeSystem.upgrades[upgradeKey];
                if (!upgrade) return;
                
                const upgradeItem = document.createElement('div');
                upgradeItem.style.cssText = `
                    background: rgba(0, 0, 0, 0.7);
                    border: 1px solid #44ff44;
                    border-radius: 3px;
                    padding: 4px 6px;
                    font-family: monospace;
                    font-size: 11px;
                    color: #44ff44;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    max-width: 200px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                `;
                
                // Upgrade type indicator
                const typeIndicator = document.createElement('div');
                typeIndicator.style.cssText = `
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    flex-shrink: 0;
                `;
                
                // Color code by upgrade type
                let indicatorColor = '#44ff44'; // Default green
                if (upgrade.description.includes('[WEAPON]')) {
                    indicatorColor = '#ff4444'; // Red for weapon upgrades
                } else if (upgrade.description.includes('[PASSIVE]')) {
                    indicatorColor = '#4444ff'; // Blue for passive upgrades
                } else if (upgrade.description.includes('[SPECIAL]')) {
                    indicatorColor = '#ff44ff'; // Magenta for special upgrades
                }
                typeIndicator.style.background = indicatorColor;
                upgradeItem.appendChild(typeIndicator);
                
                // Upgrade name
                const name = document.createElement('span');
                name.textContent = upgrade.name;
                name.style.overflow = 'hidden';
                name.style.textOverflow = 'ellipsis';
                upgradeItem.appendChild(name);
                
                upgradeDisplayContainer.appendChild(upgradeItem);
            });
        }
    }
}