/**
 * PlayerController - Control del personaje Alex en 3ra persona
 * Movimiento WASD, correr con Shift, ataque con bastón, habilidades elementales.
 * Compatible con teclado/ratón y controles táctiles.
 */
var PlayerController = pc.createScript('playerController');

PlayerController.attributes.add('moveSpeed', { type: 'number', default: 4, title: 'Velocidad de caminar' });
PlayerController.attributes.add('runMultiplier', { type: 'number', default: 1.8, title: 'Multiplicador de correr' });
PlayerController.attributes.add('rotationSpeed', { type: 'number', default: 10, title: 'Velocidad de rotación' });
PlayerController.attributes.add('attackCooldown', { type: 'number', default: 0.6, title: 'Cooldown de ataque (seg)' });
PlayerController.attributes.add('attackRange', { type: 'number', default: 2.5, title: 'Rango de ataque' });
PlayerController.attributes.add('attackDamage', { type: 'number', default: 20, title: 'Daño de ataque' });
PlayerController.attributes.add('dodgeSpeed', { type: 'number', default: 8, title: 'Velocidad de esquiva' });
PlayerController.attributes.add('dodgeDuration', { type: 'number', default: 0.4, title: 'Duración de esquiva (seg)' });
PlayerController.attributes.add('dodgeCooldown', { type: 'number', default: 1.0, title: 'Cooldown de esquiva (seg)' });
PlayerController.attributes.add('groundY', { type: 'number', default: 0, title: 'Altura del suelo' });

PlayerController.prototype.initialize = function () {
    // Referencia a componentes
    this.rigidbody = this.entity.rigidbody;
    this.animation = this.entity.animation;

    // Estado del jugador
    this.isRunning = false;
    this.isAttacking = false;
    this.isDodging = false;
    this.isUsingAbility = false;
    this.canAttack = true;
    this.canDodge = true;
    this.currentAbility = null; // 'water', 'fire', 'earth', 'air'

    // Input del joystick virtual
    this.joystickInput = { x: 0, y: 0 };
    this.joystickActive = false;

    // Velocidad actual
    this.currentSpeed = 0;

    // Registrar eventos
    this.app.on('joystick:move', this.onJoystickMove, this);
    this.app.on('joystick:release', this.onJoystickRelease, this);
    this.app.on('input:attack', this.onAttack, this);
    this.app.on('input:dodge', this.onDodge, this);
    this.app.on('input:ability', this.onUseAbility, this);
    this.app.on('relic:acquired', this.onRelicAcquired, this);

    // Habilidades desbloqueadas
    this.abilities = {
        water: false,
        fire: false,
        earth: false,
        air: false
    };

    // Teclas
    this.keys = {};
    this.app.keyboard.on(pc.EVENT_KEYDOWN, this.onKeyDown, this);
    this.app.keyboard.on(pc.EVENT_KEYUP, this.onKeyUp, this);

    // Animación inicial
    this.setAnimation('idle');
};

PlayerController.prototype.onKeyDown = function (e) {
    this.keys[e.key] = true;

    // Ataque: clic izquierdo o J
    if (e.key === pc.KEY_J || e.key === pc.MOUSEBUTTON_LEFT) {
        this.app.fire('input:attack');
    }
    // Esquiva: Space
    if (e.key === pc.KEY_SPACE) {
        this.app.fire('input:dodge');
    }
    // Habilidades: 1-4
    if (e.key === pc.KEY_1) this.app.fire('input:ability', 'water');
    if (e.key === pc.KEY_2) this.app.fire('input:ability', 'fire');
    if (e.key === pc.KEY_3) this.app.fire('input:ability', 'earth');
    if (e.key === pc.KEY_4) this.app.fire('input:ability', 'air');
};

PlayerController.prototype.onKeyUp = function (e) {
    this.keys[e.key] = false;
};

PlayerController.prototype.update = function (dt) {
    if (this.isAttacking || this.isDodging || this.isUsingAbility) return;

    // Calcular dirección de movimiento
    var moveDir = this.getMovementDirection();
    var isMoving = moveDir.length() > 0.1;

    // Verificar si está corriendo
    this.isRunning = this.keys[pc.KEY_SHIFT] && isMoving;
    var speed = this.isRunning ? this.moveSpeed * this.runMultiplier : this.moveSpeed;
    this.currentSpeed = isMoving ? speed : 0;

    if (isMoving) {
        // Normalizar dirección
        moveDir.normalize();

        // Rotar personaje hacia la dirección de movimiento
        var targetAngle = Math.atan2(moveDir.x, moveDir.z) * pc.math.RAD_TO_DEG;
        var currentAngle = this.entity.getEulerAngles().y;
        var angleDiff = pc.math.wrapAngleSubtract(targetAngle, currentAngle);
        var newAngle = currentAngle + angleDiff * Math.min(1, this.rotationSpeed * dt);
        this.entity.setEulerAngles(0, newAngle, 0);

        // Aplicar movimiento
        var velocity = new pc.Vec3(
            moveDir.x * speed,
            this.rigidbody ? this.rigidbody.linearVelocity.y : 0,
            moveDir.z * speed
        );

        if (this.rigidbody) {
            this.rigidbody.linearVelocity = velocity;
        } else {
            this.entity.translate(moveDir.x * speed * dt, 0, moveDir.z * speed * dt);
        }

        // Animación
        this.setAnimation(this.isRunning ? 'run' : 'walk');
    } else {
        // Frenar
        if (this.rigidbody) {
            var vel = this.rigidbody.linearVelocity;
            this.rigidbody.linearVelocity = new pc.Vec3(0, vel.y, 0);
        }
        this.setAnimation('idle');
    }

    // Mantener sobre el suelo
    var pos = this.entity.getPosition();
    if (pos.y < this.groundY) {
        this.entity.setPosition(pos.x, this.groundY, pos.z);
    }
};

PlayerController.prototype.getMovementDirection = function () {
    var dir = new pc.Vec3(0, 0, 0);

    // Input de teclado
    if (this.keys[pc.KEY_W] || this.keys[pc.KEY_UP]) dir.z -= 1;
    if (this.keys[pc.KEY_S] || this.keys[pc.KEY_DOWN]) dir.z += 1;
    if (this.keys[pc.KEY_A] || this.keys[pc.KEY_LEFT]) dir.x -= 1;
    if (this.keys[pc.KEY_D] || this.keys[pc.KEY_RIGHT]) dir.x += 1;

    // Input de joystick virtual
    if (this.joystickActive) {
        dir.x += this.joystickInput.x;
        dir.z -= this.joystickInput.y;
    }

    // Obtener dirección relativa a la cámara
    var camera = this.app.root.findByName('Camera');
    if (camera) {
        var camForward = camera.forward;
        var camRight = camera.right;
        camForward.y = 0;
        camRight.y = 0;
        camForward.normalize();
        camRight.normalize();

        var worldDir = new pc.Vec3();
        worldDir.addScale(camForward, -dir.z);
        worldDir.addScale(camRight, dir.x);
        return worldDir;
    }

    return dir;
};

PlayerController.prototype.onJoystickMove = function (x, y) {
    this.joystickInput.x = x;
    this.joystickInput.y = y;
    this.joystickActive = true;
};

PlayerController.prototype.onJoystickRelease = function () {
    this.joystickInput.x = 0;
    this.joystickInput.y = 0;
    this.joystickActive = false;
};

PlayerController.prototype.onAttack = function () {
    if (!this.canAttack || this.isAttacking) return;

    this.isAttacking = true;
    this.canAttack = false;
    this.setAnimation('attack');

    // Detectar enemigos en rango
    this.performAttackCheck();

    // Cooldown
    var self = this;
    setTimeout(function () {
        self.isAttacking = false;
    }, 400);

    setTimeout(function () {
        self.canAttack = true;
    }, this.attackCooldown * 1000);
};

PlayerController.prototype.performAttackCheck = function () {
    var playerPos = this.entity.getPosition();
    var playerForward = this.entity.forward;

    // Buscar enemigos
    var enemies = this.app.root.findByTag('enemy');
    for (var i = 0; i < enemies.length; i++) {
        var enemy = enemies[i];
        var enemyPos = enemy.getPosition();
        var distance = playerPos.distance(enemyPos);

        if (distance <= this.attackRange) {
            // Verificar ángulo (dentro de 90 grados del frente)
            var toEnemy = new pc.Vec3().sub2(enemyPos, playerPos).normalize();
            var dot = playerForward.dot(toEnemy);
            if (dot > 0.3) {
                this.app.fire('enemy:damage', enemy, this.attackDamage);
            }
        }
    }

    // Efecto visual de ataque
    this.app.fire('vfx:attack', playerPos, playerForward);
};

PlayerController.prototype.onDodge = function () {
    if (!this.canDodge || this.isDodging) return;

    this.isDodging = true;
    this.canDodge = false;

    // Dirección de esquiva
    var moveDir = this.getMovementDirection();
    if (moveDir.length() < 0.1) {
        moveDir = this.entity.forward.clone().scale(-1); // Retroceder si no hay input
    }
    moveDir.normalize();

    var velocity = new pc.Vec3(
        moveDir.x * this.dodgeSpeed,
        this.rigidbody ? this.rigidbody.linearVelocity.y : 0,
        moveDir.z * this.dodgeSpeed
    );

    if (this.rigidbody) {
        this.rigidbody.linearVelocity = velocity;
    }

    this.setAnimation('dodge');

    var self = this;
    setTimeout(function () {
        self.isDodging = false;
    }, this.dodgeDuration * 1000);

    setTimeout(function () {
        self.canDodge = true;
    }, this.dodgeCooldown * 1000);
};

PlayerController.prototype.onUseAbility = function (abilityType) {
    if (!this.abilities[abilityType] || this.isUsingAbility) return;

    this.isUsingAbility = true;
    this.currentAbility = abilityType;

    // Efecto según habilidad
    switch (abilityType) {
        case 'water':
            this.app.fire('ability:water', this.entity.getPosition());
            break;
        case 'fire':
            this.app.fire('ability:fire', this.entity.getPosition(), this.entity.forward);
            break;
        case 'earth':
            this.app.fire('ability:earth', this.entity.getPosition());
            break;
        case 'air':
            this.app.fire('ability:air', this.entity.getPosition(), this.entity.forward);
            break;
    }

    var self = this;
    setTimeout(function () {
        self.isUsingAbility = false;
        self.currentAbility = null;
    }, 800);
};

PlayerController.prototype.onRelicAcquired = function (data) {
    if (this.abilities.hasOwnProperty(data.type)) {
        this.abilities[data.type] = true;
    }
};

PlayerController.prototype.setAnimation = function (animName) {
    if (this.animation) {
        // Mapeo de nombres de animación a clips del modelo
        var animMap = {
            'idle': 'Survey',
            'walk': 'Walk',
            'run': 'Run',
            'attack': 'Walk', // Fallback si no hay animación de ataque
            'dodge': 'Run',
            'ability': 'Survey'
        };

        var clip = animMap[animName] || 'Survey';
        if (this.animation.currAnim !== clip) {
            this.animation.play(clip, 0.2);
        }
    }

    // Emitir para otros sistemas
    this.app.fire('player:anim', animName);
};

PlayerController.prototype.destroy = function () {
    this.app.off('joystick:move', this.onJoystickMove, this);
    this.app.off('joystick:release', this.onJoystickRelease, this);
    this.app.off('input:attack', this.onAttack, this);
    this.app.off('input:dodge', this.onDodge, this);
    this.app.off('input:ability', this.onUseAbility, this);
    this.app.off('relic:acquired', this.onRelicAcquired, this);
    this.app.keyboard.off(pc.EVENT_KEYDOWN, this.onKeyDown, this);
    this.app.keyboard.off(pc.EVENT_KEYUP, this.onKeyUp, this);
};
