/**
 * GameManager - Controlador principal del juego Arboleda
 * Gestiona estados del juego, puntuación, timer y eventos globales.
 *
 * Estados: 'menu' | 'playing' | 'paused' | 'gameover' | 'victory'
 */
var GameManager = pc.createScript('gameManager');

// Atributos configurables desde el Editor
GameManager.attributes.add('gameDuration', { type: 'number', default: 600, title: 'Duración del juego (seg)', description: 'Tiempo límite para completar la misión' });
GameManager.attributes.add('maxHealth', { type: 'number', default: 100, title: 'Vida máxima de Alex' });
GameManager.attributes.add('relicsRequired', { type: 'number', default: 4, title: 'Reliquias necesarias para ganar' });
GameManager.attributes.add('introDelay', { type: 'number', default: 2, title: 'Delay antes de iniciar (seg)' });

GameManager.prototype.initialize = function () {
    // Estado del juego
    this.gameState = 'menu';
    this.score = 0;
    this.health = this.maxHealth;
    this.relicsCollected = 0;
    this.relicsData = {
        water: { collected: false, name: 'Lágrima del Río', element: 'Agua' },
        fire: { collected: false, name: 'Semilla Ignea', element: 'Fuego' },
        earth: { collected: false, name: 'Raíz Ancestral', element: 'Tierra' },
        air: { collected: false, name: 'Pluma del Viento', element: 'Aire' }
    };
    this.timeRemaining = this.gameDuration;
    this.isDaytime = true;
    this.dayNightCycle = 0; // 0-1 donde 0.5 es medianoche

    // Registrar eventos
    this.app.on('game:start', this.startGame, this);
    this.app.on('game:pause', this.pauseGame, this);
    this.app.on('game:resume', this.resumeGame, this);
    this.app.on('game:over', this.gameOver, this);
    this.app.on('crystal:collect', this.onCrystalCollect, this);
    this.app.on('relic:collect', this.onRelicCollect, this);
    this.app.on('player:damage', this.onPlayerDamage, this);
    this.app.on('player:heal', this.onPlayerHeal, this);
    this.app.on('enemy:defeated', this.onEnemyDefeated, this);

    // Emitir estado inicial
    this.app.fire('ui:updateState', this.getStateData());

    // Iniciar ciclo día/noche
    this.dayNightSpeed = 1 / (this.gameDuration * 0.5); // Un ciclo completo en mitad del juego

    this.app.fire('game:ready');
};

GameManager.prototype.update = function (dt) {
    if (this.gameState !== 'playing') return;

    // Actualizar timer
    this.timeRemaining -= dt;
    if (this.timeRemaining <= 0) {
        this.timeRemaining = 0;
        this.app.fire('game:over', { reason: 'time' });
        return;
    }

    // Actualizar ciclo día/noche
    this.dayNightCycle += this.dayNightSpeed * dt;
    if (this.dayNightCycle >= 1) this.dayNightCycle -= 1;
    this.isDaytime = this.dayNightCycle < 0.25 || this.dayNightCycle > 0.75;

    // Emitir actualizaciones periódicas
    this.app.fire('timer:update', this.timeRemaining);
    this.app.fire('daynight:update', this.dayNightCycle);
};

GameManager.prototype.startGame = function () {
    this.gameState = 'playing';
    this.score = 0;
    this.health = this.maxHealth;
    this.relicsCollected = 0;
    this.timeRemaining = this.gameDuration;
    this.dayNightCycle = 0;

    // Resetear reliquias
    var keys = Object.keys(this.relicsData);
    for (var i = 0; i < keys.length; i++) {
        this.relicsData[keys[i]].collected = false;
    }

    this.app.fire('ui:updateState', this.getStateData());
    this.app.fire('game:started');
};

GameManager.prototype.pauseGame = function () {
    if (this.gameState === 'playing') {
        this.gameState = 'paused';
        this.app.fire('ui:updateState', this.getStateData());
    }
};

GameManager.prototype.resumeGame = function () {
    if (this.gameState === 'paused') {
        this.gameState = 'playing';
        this.app.fire('ui:updateState', this.getStateData());
    }
};

GameManager.prototype.gameOver = function (data) {
    this.gameState = 'gameover';
    this.app.fire('ui:updateState', this.getStateData());
    this.app.fire('game:ended', { victory: false, reason: data ? data.reason : 'unknown' });
};

GameManager.prototype.onCrystalCollect = function (points) {
    if (this.gameState !== 'playing') return;
    this.score += (points || 10);
    this.app.fire('score:update', this.score);
};

GameManager.prototype.onRelicCollect = function (relicType) {
    if (this.gameState !== 'playing') return;
    if (this.relicsData[relicType] && !this.relicsData[relicType].collected) {
        this.relicsData[relicType].collected = true;
        this.relicsCollected++;
        this.app.fire('relic:acquired', { type: relicType, data: this.relicsData[relicType] });
        this.app.fire('ui:updateRelic', relicType, true);

        // Verificar victoria
        if (this.relicsCollected >= this.relicsRequired) {
            this.gameState = 'victory';
            this.app.fire('game:ended', { victory: true, score: this.score, time: this.gameDuration - this.timeRemaining });
        }
    }
};

GameManager.prototype.onPlayerDamage = function (amount) {
    if (this.gameState !== 'playing') return;
    this.health = Math.max(0, this.health - amount);
    this.app.fire('health:update', this.health, this.maxHealth);

    if (this.health <= 0) {
        this.app.fire('game:over', { reason: 'health' });
    }
};

GameManager.prototype.onPlayerHeal = function (amount) {
    if (this.gameState !== 'playing') return;
    this.health = Math.min(this.maxHealth, this.health + amount);
    this.app.fire('health:update', this.health, this.maxHealth);
};

GameManager.prototype.onEnemyDefeated = function (points) {
    this.score += (points || 25);
    this.app.fire('score:update', this.score);
};

GameManager.prototype.getStateData = function () {
    return {
        state: this.gameState,
        score: this.score,
        health: this.health,
        maxHealth: this.maxHealth,
        relicsCollected: this.relicsCollected,
        relicsRequired: this.relicsRequired,
        relicsData: this.relicsData,
        timeRemaining: this.timeRemaining,
        isDaytime: this.isDaytime,
        dayNightCycle: this.dayNightCycle
    };
};

GameManager.prototype.destroy = function () {
    this.app.off('game:start', this.startGame, this);
    this.app.off('game:pause', this.pauseGame, this);
    this.app.off('game:resume', this.resumeGame, this);
    this.app.off('game:over', this.gameOver, this);
    this.app.off('crystal:collect', this.onCrystalCollect, this);
    this.app.off('relic:collect', this.onRelicCollect, this);
    this.app.off('player:damage', this.onPlayerDamage, this);
    this.app.off('player:heal', this.onPlayerHeal, this);
    this.app.off('enemy:defeated', this.onEnemyDefeated, this);
};
