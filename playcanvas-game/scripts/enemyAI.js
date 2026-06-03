/**
 * EnemyAI - Inteligencia artificial de enemigos (Lobos Sombra y criaturas)
 * Patrulla, persecución, ataque y retorno a punto de origen.
 */
var EnemyAI = pc.createScript('enemyAI');

EnemyAI.attributes.add('patrolRadius', { type: 'number', default: 8, title: 'Radio de patrulla' });
EnemyAI.attributes.add('detectionRadius', { type: 'number', default: 10, title: 'Radio de detección' });
EnemyAI.attributes.add('attackRadius', { type: 'number', default: 1.8, title: 'Radio de ataque' });
EnemyAI.attributes.add('moveSpeed', { type: 'number', default: 3, title: 'Velocidad de movimiento' });
EnemyAI.attributes.add('chaseSpeed', { type: 'number', default: 5, title: 'Velocidad de persecución' });
EnemyAI.attributes.add('attackDamage', { type: 'number', default: 10, title: 'Daño de ataque' });
EnemyAI.attributes.add('attackCooldown', { type: 'number', default: 1.5, title: 'Cooldown de ataque (seg)' });
EnemyAI.attributes.add('maxHealth', { type: 'number', default: 60, title: 'Vida máxima' });
EnemyAI.attributes.add('patrolWaitTime', { type: 'number', default: 2, title: 'Tiempo de espera en patrulla (seg)' });
EnemyAI.attributes.add('returnSpeed', { type: 'number', default: 2.5, title: 'Velocidad de retorno al origen' });
EnemyAI.attributes.add('enemyType', { type: 'string', default: 'wolf', title: 'Tipo de enemigo (wolf, golem, shadow)' });

EnemyAI.prototype.initialize = function () {
    // Posición de origen
    this.originPos = this.entity.getPosition().clone();

    // Estado: 'patrol', 'chase', 'attack', 'return', 'dead'
    this.state = 'patrol';

    // Salud
    this.health = this.maxHealth;
    this.isDead = false;

    // Patrulla
    this.patrolTarget = this.getRandomPatrolPoint();
    this.patrolWaitTimer = 0;
    this.isWaiting = false;

    // Ataque
    this.canAttack = true;
    this.attackTimer = 0;

    // Persecución
    this.lastKnownPlayerPos = null;
    this.chaseTimer = 0;
    this.maxChaseTime = 8; // Abandonar persecución después de X seg sin ver al jugador

    // Tag para ser encontrado por PlayerController
    if (this.entity.tags) {
        this.entity.tags.add('enemy');
    }

    // Registrar eventos
    this.app.on('enemy:damage', this.onDamage, this);
    this.app.on('game:start', this.onGameStart, this);
    this.app.on('game:ended', this.onGameEnd, this);

    this.gameActive = false;
};

EnemyAI.prototype.onGameStart = function () {
    this.gameActive = true;
};

EnemyAI.prototype.onGameEnd = function () {
    this.gameActive = false;
    this.state = 'patrol';
};

EnemyAI.prototype.update = function (dt) {
    if (!this.gameActive || this.isDead) return;

    var player = this.app.root.findByName('Player');
    if (!player) return;

    var playerPos = player.getPosition();
    var myPos = this.entity.getPosition();
    var distToPlayer = myPos.distance(playerPos);
    var distToOrigin = myPos.distance(this.originPos);

    // Máquina de estados
    switch (this.state) {
        case 'patrol':
            this.updatePatrol(dt);
            // Transición a persecución
            if (distToPlayer < this.detectionRadius) {
                this.state = 'chase';
                this.lastKnownPlayerPos = playerPos.clone();
                this.chaseTimer = 0;
            }
            break;

        case 'chase':
            this.updateChase(dt, playerPos);
            this.chaseTimer += dt;
            // Transición a ataque
            if (distToPlayer < this.attackRadius) {
                this.state = 'attack';
            }
            // Transición a retorno si pierde al jugador
            if (distToPlayer > this.detectionRadius * 1.5 || this.chaseTimer > this.maxChaseTime) {
                this.state = 'return';
            }
            // Actualizar última posición conocida
            if (distToPlayer < this.detectionRadius) {
                this.lastKnownPlayerPos = playerPos.clone();
                this.chaseTimer = 0;
            }
            break;

        case 'attack':
            this.updateAttack(dt, playerPos);
            // Transición si el jugador se aleja
            if (distToPlayer > this.attackRadius * 1.5) {
                this.state = 'chase';
            }
            break;

        case 'return':
            this.updateReturn(dt);
            // Transición a patrulla al llegar al origen
            if (distToOrigin < 1) {
                this.state = 'patrol';
                this.patrolTarget = this.getRandomPatrolPoint();
            }
            // Transición a persecución si ve al jugador de camino
            if (distToPlayer < this.detectionRadius * 0.8) {
                this.state = 'chase';
                this.lastKnownPlayerPos = playerPos.clone();
                this.chaseTimer = 0;
            }
            break;
    }
};

EnemyAI.prototype.updatePatrol = function (dt) {
    if (this.isWaiting) {
        this.patrolWaitTimer += dt;
        if (this.patrolWaitTimer >= this.patrolWaitTime) {
            this.isWaiting = false;
            this.patrolTarget = this.getRandomPatrolPoint();
        }
        return;
    }

    var myPos = this.entity.getPosition();
    var distToTarget = myPos.distance(this.patrolTarget);

    if (distToTarget < 0.5) {
        this.isWaiting = true;
        this.patrolWaitTimer = 0;
        return;
    }

    // Mover hacia el punto de patrulla
    this.moveTowards(this.patrolTarget, this.moveSpeed, dt);
};

EnemyAI.prototype.updateChase = function (dt, playerPos) {
    this.moveTowards(playerPos, this.chaseSpeed, dt);
};

EnemyAI.prototype.updateAttack = function (dt, playerPos) {
    // Mirar al jugador
    this.lookAt(playerPos);

    // Atacar si puede
    if (this.canAttack) {
        this.performAttack();
        this.canAttack = false;
        this.attackTimer = 0;
    }

    // Cooldown de ataque
    this.attackTimer += dt;
    if (this.attackTimer >= this.attackCooldown) {
        this.canAttack = true;
    }
};

EnemyAI.prototype.updateReturn = function (dt) {
    this.moveTowards(this.originPos, this.returnSpeed, dt);
};

EnemyAI.prototype.moveTowards = function (target, speed, dt) {
    var myPos = this.entity.getPosition();
    var direction = new pc.Vec3().sub2(target, myPos);
    direction.y = 0;
    direction.normalize();

    // Mover
    var movement = direction.scale(speed * dt);
    this.entity.setPosition(
        myPos.x + movement.x,
        myPos.y,
        myPos.z + movement.z
    );

    // Rotar hacia el movimiento
    this.lookAt(target);
};

EnemyAI.prototype.lookAt = function (target) {
    var myPos = this.entity.getPosition();
    var dx = target.x - myPos.x;
    var dz = target.z - myPos.z;
    var angle = Math.atan2(dx, dz) * pc.math.RAD_TO_DEG;
    this.entity.setEulerAngles(0, angle, 0);
};

EnemyAI.prototype.performAttack = function () {
    // Efecto visual
    this.app.fire('vfx:enemyAttack', this.entity.getPosition(), this.enemyType);

    // Daño al jugador
    this.app.fire('player:damage', this.attackDamage);
};

EnemyAI.prototype.onDamage = function (enemy, amount) {
    if (enemy !== this.entity || this.isDead) return;

    this.health -= amount;

    // Efecto visual de daño
    this.app.fire('vfx:enemyHit', this.entity.getPosition());

    // Forzar estado de persecución si estaba patrullando
    if (this.state === 'patrol' || this.state === 'return') {
        var player = this.app.root.findByName('Player');
        if (player) {
            this.lastKnownPlayerPos = player.getPosition().clone();
            this.state = 'chase';
            this.chaseTimer = 0;
        }
    }

    // Muerte
    if (this.health <= 0) {
        this.die();
    }
};

EnemyAI.prototype.die = function () {
    this.isDead = true;
    this.state = 'dead';

    // Notificar al GameManager
    this.app.fire('enemy:defeated', 25);

    // Efecto visual de muerte
    this.app.fire('vfx:enemyDeath', this.entity.getPosition(), this.enemyType);

    // Desactivar entidad (o destruir después de animación)
    var self = this;
    setTimeout(function () {
        self.entity.enabled = false;
    }, 500);
};

EnemyAI.prototype.getRandomPatrolPoint = function () {
    var angle = Math.random() * Math.PI * 2;
    var radius = Math.random() * this.patrolRadius;
    return new pc.Vec3(
        this.originPos.x + Math.cos(angle) * radius,
        this.originPos.y,
        this.originPos.z + Math.sin(angle) * radius
    );
};

EnemyAI.prototype.destroy = function () {
    this.app.off('enemy:damage', this.onDamage, this);
    this.app.off('game:start', this.onGameStart, this);
    this.app.off('game:ended', this.onGameEnd, this);
};
