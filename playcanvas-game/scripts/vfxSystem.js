/**
 * VFXSystem - Sistema de efectos visuales para Arboleda
 * Partículas, efectos de habilidades, impactos, colecciones y ambiente.
 */
var VFXSystem = pc.createScript('vfxSystem');

VFXSystem.prototype.initialize = function () {
    this.particles = [];

    // Registrar eventos
    this.app.on('vfx:attack', this.onAttackVFX, this);
    this.app.on('vfx:enemyAttack', this.onEnemyAttackVFX, this);
    this.app.on('vfx:enemyHit', this.onEnemyHitVFX, this);
    this.app.on('vfx:enemyDeath', this.onEnemyDeathVFX, this);
    this.app.on('vfx:relicCollect', this.onRelicCollectVFX, this);
    this.app.on('vfx:ability:water', this.onWaterVFX, this);
    this.app.on('vfx:ability:fire', this.onFireVFX, this);
    this.app.on('vfx:ability:earth', this.onEarthVFX, this);
    this.app.on('vfx:ability:air', this.onAirVFX, this);
};

VFXSystem.prototype.update = function (dt) {
    // Actualizar partículas
    for (var i = this.particles.length - 1; i >= 0; i--) {
        var p = this.particles[i];
        p.life -= dt;

        if (p.life <= 0) {
            if (p.entity) {
                p.entity.destroy();
            }
            this.particles.splice(i, 1);
            continue;
        }

        // Mover partícula
        if (p.entity) {
            var pos = p.entity.getPosition();
            p.entity.setPosition(
                pos.x + p.velocity.x * dt,
                pos.y + p.velocity.y * dt,
                pos.z + p.velocity.z * dt
            );

            // Escala según vida
            var t = p.life / p.maxLife;
            var scale = t * p.scale;
            p.entity.setLocalScale(scale, scale, scale);

            // Opacidad
            if (p.entity.model && p.entity.model.model) {
                // No se puede cambiar opacidad fácilmente en PlayCanvas sin material dinámico
            }
        }
    }

    // Límite de partículas
    if (this.particles.length > 200) {
        var excess = this.particles.splice(0, this.particles.length - 200);
        for (var j = 0; j < excess.length; j++) {
            if (excess[j].entity) excess[j].entity.destroy();
        }
    }
};

VFXSystem.prototype.spawnParticle = function (position, velocity, color, scale, life) {
    var entity = new pc.Entity('particle');
    entity.setPosition(position.x, position.y, position.z);
    entity.setLocalScale(scale, scale, scale);

    entity.addComponent('model', {
        type: 'sphere'
    });

    var mat = new pc.StandardMaterial();
    mat.diffuse.set(color.r * 0.3, color.g * 0.3, color.b * 0.3);
    mat.emissive.set(color.r, color.g, color.b);
    mat.blendType = pc.BLEND_ADDITIVE;
    mat.update();
    entity.model.model.meshInstances[0].material = mat;

    this.app.root.addChild(entity);

    this.particles.push({
        entity: entity,
        velocity: velocity,
        scale: scale,
        life: life,
        maxLife: life
    });
};

VFXSystem.prototype.spawnBurst = function (position, color, count, radius, speed, scale, life) {
    for (var i = 0; i < count; i++) {
        var angle = Math.random() * Math.PI * 2;
        var elevation = (Math.random() - 0.3) * Math.PI;
        var spd = speed * (0.5 + Math.random() * 0.5);

        var velocity = new pc.Vec3(
            Math.cos(angle) * Math.cos(elevation) * spd,
            Math.sin(elevation) * spd + 1,
            Math.sin(angle) * Math.cos(elevation) * spd
        );

        var offset = new pc.Vec3(
            (Math.random() - 0.5) * radius,
            (Math.random() - 0.5) * radius * 0.5,
            (Math.random() - 0.5) * radius
        );

        var pos = new pc.Vec3().add2(position, offset);
        this.spawnParticle(pos, velocity, color, scale * (0.5 + Math.random()), life * (0.5 + Math.random() * 0.5));
    }
};

VFXSystem.prototype.onAttackVFX = function (position, direction) {
    this.spawnBurst(
        new pc.Vec3(position.x + direction.x, position.y + 1, position.z + direction.z),
        { r: 1, g: 0.9, b: 0.6 },
        8, 0.5, 3, 0.15, 0.4
    );
};

VFXSystem.prototype.onEnemyAttackVFX = function (position, enemyType) {
    var color = { r: 0.5, g: 0, b: 0.5 }; // Púrpura por defecto
    if (enemyType === 'golem') color = { r: 0.6, g: 0.4, b: 0.2 };
    this.spawnBurst(position, color, 6, 0.8, 2, 0.12, 0.5);
};

VFXSystem.prototype.onEnemyHitVFX = function (position) {
    this.spawnBurst(
        new pc.Vec3(position.x, position.y + 1, position.z),
        { r: 1, g: 1, b: 1 },
        5, 0.3, 4, 0.1, 0.3
    );
};

VFXSystem.prototype.onEnemyDeathVFX = function (position, enemyType) {
    // Explosión de partículas oscuras
    this.spawnBurst(
        new pc.Vec3(position.x, position.y + 0.5, position.z),
        { r: 0.5, g: 0, b: 0.5 },
        20, 1.5, 5, 0.2, 1.0
    );
    // Partículas brillantes
    this.spawnBurst(
        new pc.Vec3(position.x, position.y + 0.5, position.z),
        { r: 0.8, g: 0.6, b: 1 },
        10, 0.5, 3, 0.08, 0.8
    );
};

VFXSystem.prototype.onRelicCollectVFX = function (position, type) {
    var colors = {
        water: { r: 0.2, g: 0.5, b: 1 },
        fire: { r: 1, g: 0.3, b: 0.1 },
        earth: { r: 0.3, g: 0.8, b: 0.2 },
        air: { r: 0.9, g: 0.9, b: 1 }
    };

    var color = colors[type] || { r: 1, g: 1, b: 1 };

    // Explosión grande
    this.spawnBurst(position, color, 30, 2, 6, 0.25, 1.5);

    // Anillo ascendente
    for (var i = 0; i < 16; i++) {
        var angle = (i / 16) * Math.PI * 2;
        var velocity = new pc.Vec3(
            Math.cos(angle) * 3,
            4,
            Math.sin(angle) * 3
        );
        this.spawnParticle(
            new pc.Vec3(position.x, position.y + 0.5, position.z),
            velocity, color, 0.15, 1.2
        );
    }
};

VFXSystem.prototype.onWaterVFX = function (position) {
    this.spawnBurst(position, { r: 0.2, g: 0.5, b: 1 }, 15, 1.5, 3, 0.15, 1.0);
};

VFXSystem.prototype.onFireVFX = function (position, direction) {
    var pos = new pc.Vec3(position.x + direction.x * 2, position.y + 1, position.z + direction.z * 2);
    this.spawnBurst(pos, { r: 1, g: 0.4, b: 0 }, 20, 1, 4, 0.2, 0.8);
};

VFXSystem.prototype.onEarthVFX = function (position) {
    this.spawnBurst(position, { r: 0.4, g: 0.7, b: 0.2 }, 12, 2, 2, 0.2, 1.2);
};

VFXSystem.prototype.onAirVFX = function (position, direction) {
    var pos = new pc.Vec3(position.x + direction.x * 3, position.y + 1.5, position.z + direction.z * 3);
    this.spawnBurst(pos, { r: 0.8, g: 0.8, b: 1 }, 15, 2, 5, 0.1, 0.6);
};

VFXSystem.prototype.destroy = function () {
    this.app.off('vfx:attack', this.onAttackVFX, this);
    this.app.off('vfx:enemyAttack', this.onEnemyAttackVFX, this);
    this.app.off('vfx:enemyHit', this.onEnemyHitVFX, this);
    this.app.off('vfx:enemyDeath', this.onEnemyDeathVFX, this);
    this.app.off('vfx:relicCollect', this.onRelicCollectVFX, this);
    this.app.off('vfx:ability:water', this.onWaterVFX, this);
    this.app.off('vfx:ability:fire', this.onFireVFX, this);
    this.app.off('vfx:ability:earth', this.onEarthVFX, this);
    this.app.off('vfx:ability:air', this.onAirVFX, this);

    // Limpiar partículas
    for (var i = 0; i < this.particles.length; i++) {
        if (this.particles[i].entity) {
            this.particles[i].entity.destroy();
        }
    }
    this.particles = [];
};
