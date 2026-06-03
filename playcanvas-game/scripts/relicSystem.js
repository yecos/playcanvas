/**
 * RelicSystem - Sistema de reliquias elementales de Arboleda
 * Gestiona las 4 reliquias (Agua, Fuego, Tierra, Aire) como objetos coleccionables
 * con pedestales activables y efectos visuales.
 */
var RelicSystem = pc.createScript('relicSystem');

RelicSystem.attributes.add('relicTypes', {
    type: 'json',
    title: 'Configuración de reliquias',
    schema: [
        { name: 'waterPos', type: 'vec3', default: [15, 0, 10] },
        { name: 'firePos', type: 'vec3', default: [-12, 0, -15] },
        { name: 'earthPos', type: 'vec3', default: [10, 0, -18] },
        { name: 'airPos', type: 'vec3', default: [-18, 0, 8] }
    ]
});

RelicSystem.attributes.add('collectRadius', { type: 'number', default: 2.5, title: 'Radio de colección' });
RelicSystem.attributes.add('glowIntensity', { type: 'number', default: 2, title: 'Intensidad del brillo' });
RelicSystem.attributes.add('rotationSpeed', { type: 'number', default: 45, title: 'Velocidad de rotación' });
RelicSystem.attributes.add('bobSpeed', { type: 'number', default: 1.5, title: 'Velocidad de flotación' });
RelicSystem.attributes.add('bobHeight', { type: 'number', default: 0.5, title: 'Altura de flotación' });

RelicSystem.prototype.initialize = function () {
    // Colores de cada reliquia
    this.relicColors = {
        water: { r: 0.2, g: 0.5, b: 1.0, hex: '#3399ff', name: 'Lágrima del Río' },
        fire: { r: 1.0, g: 0.3, b: 0.1, hex: '#ff4d1a', name: 'Semilla Ígnea' },
        earth: { r: 0.3, g: 0.8, b: 0.2, hex: '#4dcc33', name: 'Raíz Ancestral' },
        air: { r: 0.9, g: 0.9, b: 1.0, hex: '#e6e6ff', name: 'Pluma del Viento' }
    };

    // Crear entidades de reliquias
    this.relics = {};
    this.createRelics();

    // Pedestal de activación (requiere orden correcto para el ritual)
    this.pedestalOrder = ['water', 'fire', 'earth', 'air'];
    this.activatedPedestals = [];

    // Registrar eventos
    this.app.on('game:start', this.onGameStart, this);
    this.app.on('game:ended', this.onGameEnd, this);
};

RelicSystem.prototype.createRelics = function () {
    var types = ['water', 'fire', 'earth', 'air'];
    var positions = [
        this.relicTypes.waterPos,
        this.relicTypes.firePos,
        this.relicTypes.earthPos,
        this.relicTypes.airPos
    ];

    for (var i = 0; i < types.length; i++) {
        var type = types[i];
        var pos = positions[i];
        var color = this.relicColors[type];

        // Crear entidad de reliquia
        var relicEntity = new pc.Entity(type + '_relic');
        relicEntity.setPosition(pos.x, pos.y + 1.5, pos.z);

        // Modelo (cristal)
        relicEntity.addComponent('model', {
            type: 'sphere'
        });

        // Crear material emisivo
        var material = new pc.StandardMaterial();
        material.diffuse.set(color.r * 0.5, color.g * 0.5, color.b * 0.5);
        material.emissive.set(color.r * this.glowIntensity, color.g * this.glowIntensity, color.b * this.glowIntensity);
        material.update();
        relicEntity.model.model.meshInstances[0].material = material;

        // Luz puntual
        relicEntity.addComponent('light', {
            type: 'point',
            color: new pc.Color(color.r, color.g, color.b),
            intensity: 2,
            range: 8,
            castShadows: false
        });

        // Tag
        if (relicEntity.tags) {
            relicEntity.tags.add('relic');
        }

        // Crear pedestal debajo
        var pedestal = new pc.Entity(type + '_pedestal');
        pedestal.setPosition(pos.x, pos.y + 0.5, pos.z);
        pedestal.addComponent('model', {
            type: 'cylinder'
        });
        pedestal.setLocalScale(1.2, 1, 1.2);

        var pedestalMat = new pc.StandardMaterial();
        pedestalMat.diffuse.set(0.4, 0.35, 0.3);
        pedestalMat.emissive.set(0.05, 0.04, 0.03);
        pedestalMat.update();
        pedestal.model.model.meshInstances[0].material = pedestalMat;

        // Guardar referencia
        this.relics[type] = {
            entity: relicEntity,
            pedestal: pedestal,
            collected: false,
            baseY: pos.y + 1.5,
            color: color
        };

        // Añadir al root
        this.app.root.addChild(relicEntity);
        this.app.root.addChild(pedestal);
    }
};

RelicSystem.prototype.update = function (dt) {
    var player = this.app.root.findByName('Player');
    if (!player) return;

    var playerPos = player.getPosition();

    // Actualizar cada reliquia
    var types = Object.keys(this.relics);
    for (var i = 0; i < types.length; i++) {
        var type = types[i];
        var relic = this.relics[type];

        if (relic.collected) continue;

        var relicPos = relic.entity.getPosition();

        // Rotación y flotación
        relic.entity.rotate(0, this.rotationSpeed * dt, 0);
        var newY = relic.baseY + Math.sin(this.app.time.totalTime * this.bobSpeed) * this.bobHeight;
        relic.entity.setPosition(relicPos.x, newY, relicPos.z);

        // Pulso de luz
        if (relic.entity.light) {
            relic.entity.light.intensity = 1.5 + Math.sin(this.app.time.totalTime * 3) * 0.5;
        }

        // Verificar colección
        var distToPlayer = playerPos.distance(relicPos);
        if (distToPlayer < this.collectRadius) {
            this.collectRelic(type);
        }
    }
};

RelicSystem.prototype.collectRelic = function (type) {
    var relic = this.relics[type];
    if (!relic || relic.collected) return;

    relic.collected = true;

    // Animación de colección (escala hacia arriba y desaparecer)
    var self = this;
    var entity = relic.entity;
    var startTime = this.app.time.totalTime;
    var duration = 0.8;

    var animateCollect = function () {
        var elapsed = self.app.time.totalTime - startTime;
        var t = Math.min(elapsed / duration, 1);

        // Escala decreciente
        var scale = 1 - t;
        entity.setLocalScale(scale, scale, scale);

        // Subir
        var pos = entity.getPosition();
        entity.setPosition(pos.x, pos.y + t * 3 * 0.016, pos.z);

        if (t < 1) {
            requestAnimationFrame(animateCollect);
        } else {
            // Desactivar
            entity.enabled = false;
            if (entity.light) entity.light.enabled = false;

            // Activar brillo del pedestal
            var pedestalMat = new pc.StandardMaterial();
            pedestalMat.diffuse.set(relic.color.r, relic.color.g, relic.color.b);
            pedestalMat.emissive.set(relic.color.r * 0.5, relic.color.g * 0.5, relic.color.b * 0.5);
            pedestalMat.update();
            relic.pedestal.model.model.meshInstances[0].material = pedestalMat;
        }
    };

    // Efecto VFX
    this.app.fire('vfx:relicCollect', entity.getPosition(), type);

    // Iniciar animación
    animateCollect();

    // Notificar al GameManager
    this.app.fire('relic:collect', type);
    this.app.fire('ui:notification', '¡' + relic.color.name + ' adquirida!', 'relic');
};

RelicSystem.prototype.onGameStart = function () {
    // Resetear reliquias
    var types = Object.keys(this.relics);
    for (var i = 0; i < types.length; i++) {
        var relic = this.relics[types[i]];
        relic.collected = false;
        relic.entity.enabled = true;
        if (relic.entity.light) relic.entity.light.enabled = true;
        relic.entity.setLocalScale(1, 1, 1);
    }
};

RelicSystem.prototype.onGameEnd = function () {
    // Limpieza si es necesario
};

RelicSystem.prototype.destroy = function () {
    this.app.off('game:start', this.onGameStart, this);
    this.app.off('game:ended', this.onGameEnd, this);
};
