# Crimson Eclipse - Browser Survivor Game Design

## Theme & Setting
**Crimson Eclipse** is a vampire survivors-style browser game set in a dark fantasy world during an eternal eclipse. Players control a lone survivor fighting endless waves of supernatural creatures drawn by the cursed red moon.

## Core Gameplay Loop
1. **Survive** waves of increasingly difficult enemies
2. **Collect** experience orbs from defeated enemies 
3. **Level up** and choose from randomized ability upgrades
4. **Progress** through different areas with unique enemy types
5. **Unlock** new characters, weapons, and passive abilities

## Technical Architecture

### Engine Structure
```
Game/
├── Core/
│   ├── GameEngine.js      # Main game loop and state management
│   ├── EntityManager.js   # Handle all game entities
│   ├── InputManager.js    # Keyboard/mouse input handling
│   ├── AudioManager.js    # Sound effects and music
│   └── AssetLoader.js     # Image and resource loading
├── Entities/
│   ├── Player.js          # Player character logic
│   ├── Enemy.js           # Base enemy class
│   ├── Projectile.js      # Weapons and attacks
│   └── Pickup.js          # Experience orbs and items
├── Systems/
│   ├── CollisionSystem.js # Handle all collision detection
│   ├── RenderSystem.js    # Canvas rendering
│   ├── SpawnSystem.js     # Enemy spawn management
│   ├── UpgradeSystem.js   # Level up mechanics
│   └── ProgressSystem.js  # Game progression and unlocks
└── UI/
    ├── HUD.js            # Health, experience, timer
    ├── UpgradeMenu.js    # Level up selection screen
    ├── MainMenu.js       # Start screen and settings
    └── GameOver.js       # Death screen and stats
```

### Scalability Features
- **Component-based entity system** for easy addition of new enemies/weapons
- **Data-driven configuration** for easy balancing without code changes
- **Modular upgrade system** allowing complex ability combinations
- **Flexible spawn patterns** supporting various enemy types and behaviors
- **Save/load system** for player progression persistence

## Player Character

### Base Stats
- **Health**: 100 HP (upgradeable)
- **Speed**: 150 pixels/second (upgradeable)  
- **Recovery**: 1 second invincibility after damage
- **Experience**: Levels 1-100+ with exponential scaling

### Movement
- **WASD** or **Arrow Keys** for 8-directional movement
- Smooth acceleration/deceleration for responsive feel
- Screen boundaries prevent leaving play area

## Weapon System ✅ IMPLEMENTED

### Starting Weapon: Crimson Bolt
- Auto-firing red energy projectiles
- Base damage: 10
- Fire rate: 2.5 shots/second
- Range: 300 pixels

### Available Weapon Types ✅
1. **Crimson Bolt** (Starting weapon)
   - Basic red energy projectiles
   - Reliable damage and range

2. **Blood Whip** 
   - Close-range sweeping attack
   - Wide hitbox, pierces multiple enemies
   - Lower range but higher damage

3. **Shadow Blade**
   - Fast piercing projectiles
   - High speed, moderate damage
   - Can hit 2+ enemies in a line

4. **Eclipse Orb**
   - Slow but explosive projectiles
   - Area of effect damage on impact
   - High damage potential

5. **Void Scythe**
   - Spinning projectiles that return to player
   - Unique returning mechanic
   - Can hit enemies twice

### Weapon Evolution System ✅
```
Crimson Bolt → Blood Whip / Shadow Blade
Blood Whip → Eclipse Orb
Shadow Blade → Void Scythe  
Eclipse Orb → Void Scythe
```

### Passive Abilities
- **Vampire's Vigor**: Health regeneration
- **Shadow Step**: Movement speed bonus
- **Blood Frenzy**: Damage increases with kills
- **Eclipse Shield**: Temporary invincibility ability
- **Soul Harvest**: Increased experience gain

## Enemy Design

### Enemy Types
1. **Shadow Wraith** (Basic)
   - HP: 20, Speed: 100, Damage: 15
   - Moves toward player in straight line

2. **Blood Bat** (Fast/Weak)
   - HP: 5, Speed: 200, Damage: 8
   - Erratic movement pattern, spawns in groups

3. **Bone Golem** (Tank)
   - HP: 100, Speed: 50, Damage: 30
   - Slow but high health and damage

4. **Eclipse Cultist** (Ranged)
   - HP: 35, Speed: 80, Damage: 20
   - Shoots projectiles at player

5. **Crimson Lord** (Boss)
   - HP: 500+, Multiple phases
   - Spawns every 10 minutes

### Spawn Mechanics
- **Time-based scaling**: Enemy health/damage increases over time
- **Population control**: Maximum enemy count prevents lag
- **Smart positioning**: Enemies spawn off-screen edges
- **Wave patterns**: Special formations every few minutes

## Progression System ✅ IMPLEMENTED

### Experience & Leveling ✅
- Experience orbs automatically collected when near player
- Each level offers choice of 3 random upgrades from available pool
- Higher levels require exponentially more experience  
- No level cap - infinite progression potential

### Upgrade Categories ✅
1. **Weapon Upgrades**: Damage, fire rate, projectile speed/range
2. **Weapon Evolution**: Transform weapons into new types with unique mechanics
3. **Passive Abilities**: Health, speed, regeneration, magnetism
4. **Special Powers**: Multi-shot, piercing, critical hits, explosions
5. **Defensive Upgrades**: Shields, reduced invulnerability time

### Available Upgrades ✅
- **Crimson Power**: +5 weapon damage
- **Rapid Fire**: +15% fire rate  
- **Velocity Boost**: +20% projectile speed
- **Long Shot**: +50% projectile range
- **Twin Bolts**: Fire additional projectile
- **Vampire's Vigor**: +25 max health
- **Shadow Step**: +20% movement speed
- **Blood Regeneration**: Regenerate health over time
- **Soul Harvest**: +50% XP pickup range
- **Piercing Shot**: Projectiles pierce enemies
- **Eclipse Burst**: Projectiles explode on impact
- **Blood Frenzy**: 15% critical hit chance
- **Eclipse Shield**: Reduced invulnerability time

## Pickup System ✅ IMPLEMENTED

### Pickup Types ✅
1. **Experience Orbs** (Blue)
   - Primary progression currency
   - Automatically attracted to player within range
   - Magnetic range can be upgraded

2. **Health Pickups** (Red Cross)
   - Restore 25-50 health points
   - Only spawn when player health is below 80%
   - Spawn every 15+ seconds

3. **Power-up Items** (Green Star)
   - Temporary boost effects lasting 5-15 seconds
   - Random effects: damage boost, speed boost, rapid fire, shield, enhanced magnetism
   - Spawn randomly every 15+ seconds

### Power-up Effects ✅
- **Damage Boost**: +50% damage for 10 seconds
- **Speed Boost**: +30% movement speed for 8 seconds  
- **Rapid Fire**: +30% fire rate for 12 seconds
- **Eclipse Shield**: Temporary invulnerability for 5 seconds
- **Soul Magnet**: 3x magnetism range for 15 seconds

### Meta Progression ✅ ENHANCED
- **Character Unlocks**: New starting characters with different abilities
- **Permanent Upgrades**: 12 different soul essence upgrades that persist between runs ✅ EXPANDED
  - **Vampire Vitality**: +10 max health per level (5 levels)
  - **Crimson Power**: +2 starting damage per level (5 levels)  
  - **Shadow Stride**: +10% movement speed per level (3 levels)
  - **Soul Attraction**: +20 pickup range per level (3 levels)
  - **Arcane Knowledge**: +10% XP gain per level (5 levels)
  - **Soul Resonance**: +10% essence gain per level (5 levels)
  - **Rapid Reflexes**: +10% fire rate per level (3 levels) ✅ NEW
  - **Fortune's Favor**: +5% crit chance per level (3 levels) ✅ NEW
  - **Eagle Eye**: +15% projectile range per level (3 levels) ✅ NEW
  - **Eternal Vigor**: Start with regeneration per level (3 levels) ✅ NEW
  - **Essence Mastery**: +20% power-up duration per level (4 levels) ✅ NEW
  - **Soul Reaper**: +25% essence from bosses per level (3 levels) ✅ NEW
- **Achievements**: Unlock new content and bragging rights

## Visual Design

### Art Style
- **Pixel art** aesthetic with smooth animations
- **Dark color palette** with red/purple accent colors
- **Particle effects** for impacts, deaths, and special abilities
- **Screen shake** and visual feedback for satisfying combat

### UI Design
- **Minimalist HUD** showing health, experience, timer
- **Clean upgrade menus** with clear ability descriptions
- **Responsive design** works on desktop and tablet browsers

## Audio Design

### Sound Effects
- Satisfying weapon firing sounds
- Impactful enemy death audio
- Experience collection "ding"
- Level up fanfare
- Screen shake with audio emphasis

### Music
- Atmospheric dark ambient background track
- Intensity increases with enemy density
- Boss encounter music changes
- Audio cues for important events

## Performance Optimization

### Rendering
- **Object pooling** for frequently created/destroyed entities
- **Spatial partitioning** for efficient collision detection
- **Culling** of off-screen entities
- **Canvas optimization** techniques

### Memory Management
- Reuse enemy/projectile objects instead of creating new ones
- Limit particle effects and clean up old ones
- Efficient sprite management and caching

## Future Expansion Plans

### Phase 1: Core Features ✅ COMPLETED
- Basic player movement and combat ✅
- Simple enemy types and spawning ✅
- Experience and leveling system ✅
- Essential upgrades and weapons ✅
- **NEW**: Interactive upgrade system with choice menus ✅
- **NEW**: Multiple weapon types and evolutions ✅
- **NEW**: Health and power-up pickups ✅

### Phase 2: Enhanced Content
- Additional enemy types and bosses
- More weapon varieties and evolutions
- Advanced passive abilities
- Multiple areas/backgrounds

### Phase 3: Meta Features  
- Character selection and unlocks
- Achievement system
- Statistics tracking
- Local storage save system

### Phase 4: Polish & Balance ⏳ IN PROGRESS
- ✅ Game pause functionality (P key)
- ✅ Fixed piercing projectiles bug
- ✅ Enhanced upgrade system descriptions  
- ✅ Stage/map progression system with win conditions
- Visual effects and juice
- Audio implementation
- Performance optimization
- Difficulty curve refinement

## Stage Progression System ✅ IMPLEMENTED

### Stage Structure
The game now features 8 progressive stages, each with unique themes, enemies, and challenges:

1. **Crimson Fields** (5 min) - Tutorial stage with basic enemies
2. **Bone Gardens** (7 min) - Cemetery with golems added
3. **Cultist Sanctum** (8 min) - Dark temple with ranged cultists
4. **Elite Wraith Domain** (9 min) - Enhanced spirits and shadow lords
5. **Crimson Lord's Throne** (10 min) - First major boss encounter
6. **Nightmare Depths** (11 min) - Abyss realm with extreme difficulty ✅ NEW
7. **Void Sanctum** (12 min) - Floating temple in the void ✅ NEW
8. **Eclipse's Heart** (15 min) - Final boss and ultimate challenge ✅ NEW

### Win Conditions
- **Survival Stages**: Survive for the required duration to unlock next stage
- **Boss Stages**: Defeat the stage boss to advance
- **Final Victory**: Complete all 8 stages to achieve full victory

### Stage Features ✅
- **Progressive Difficulty**: Each stage increases spawn rates and enemy health
- **Stage-Specific Enemies**: Enemies unlock as player progresses
- **Visual Variety**: Each stage has unique background colors and themes
- **Reward System**: Soul Essence bonuses for completing stages
- **Persistent Progression**: Unlocked stages save between game sessions

## Game Controls & Features ✅

### Enhanced Controls
- **WASD/Arrow Keys**: 8-directional movement
- **P Key**: Pause/resume game during play
- **ESC Key**: Resume from pause menu
- **1, 2, 3 Keys**: Quick upgrade selection

### Quality of Life Features ✅ ENHANCED
- **Improved Upgrade Descriptions**: Clear categorization with [WEAPON], [PASSIVE], [SPECIAL] tags
- **Fixed Piercing System**: Projectiles now properly pierce the correct number of enemies
- **Smart Upgrade Filtering**: Prevents duplicate single-use upgrades like Blood Fury, Homing, etc. ✅ NEW
- **Enhanced Homing Projectiles**: Projectiles now actively track and curve toward enemies within range ✅ NEW
- **Pause Menu**: Professional pause overlay with resume and main menu options
- **Stage Progression**: Clear objectives and completion rewards
- **Extended Content**: 8 total stages with increasing difficulty and rewards ✅ NEW