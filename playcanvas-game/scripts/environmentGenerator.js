/**
 * EnvironmentGenerator - Genera el entorno del Bosque Antiguo
 * Crea árboles, vegetación, rocas, hongos bioluminiscentes y elementos ambientales.
 */
var EnvironmentGenerator = pc.createScript('environmentGenerator');

EnvironmentGenerator.attributes.add('treeCount', { type: 'number', default: 40, title: 'Número de árboles' });
EnvironmentGenerator.attributes.add('rockCount', { type: 'number', default: 20, title: 'Número de rocas' });
EnvironmentGenerator.attributes.add('mushroomCount', { type: 'number', default: 15, title: 'Hongos bioluminiscentes' });
EnvironmentGenerator.attributes.add('groundSize', { type: 'number', default: 60, title: 'Tamaño del terreno' });
EnvironmentGenerator.attributes.add('clearingRadius', { type: 'number', default: 8, title: 'Radio del claro central' });

EnvironmentGenerator.prototype.initialize = function () {
    this.generateEnvironment();
    this.app.on('game:start', this.onGameStart, this);
};

EnvironmentGenerator.prototype.onGameStart = function () {
    // Regenerar si es necesario
};

EnvironmentGenerator.prototype.generateEnvironment = function () {
    // === SUELO ===
    this.createGround();

    // === ÁRBOLES ===
    for (var i = 0; i < this.treeCount; i++) {
        var pos = this.getRandomPosition(4);
        if (pos) {
            this.createTree(pos);
        }
    }

    // === ROCAS ===
    for (var j = 0; j < this.rockCount; j++) {
        var rpos = this.getRandomPosition(2);
        if (rpos) {
            this.createRock(rpos);
        }
    }

    // === HONGOS BIOLUMINISCENTES ===
    for (var k = 0; k < this.mushroomCount; k++) {
        var mpos = this.getRandomPosition(1.5);
        if (mpos) {
            this.createMushroom(mpos);
        }
    }

    // === LUCIÉRNAGAS (partículas ambientales) ===
    this.createFireflies();

    // === LÍMITES DEL MUNDO ===
    this.createWorldBoundary();
};

EnvironmentGenerator.prototype.getRandomPosition = function (minDistFromCenter) {
    for (var attempts = 0; attempts < 20; attempts++) {
        var x = (Math.random() - 0.5) * this.groundSize;
        var z = (Math.random() - 0.5) * this.groundSize;
        var distFromCenter = Math.sqrt(x * x + z * z);

        // Mantener claro central y posiciones de reliquias
        if (distFromCenter > this.clearingRadius && distFromCenter < this.groundSize * 0.45) {
            // Verificar distancia a posiciones de reliquias
            var relicPositions = [
                [15, 10], [-12, -15], [10, -18], [-18, 8]
            ];
            var tooClose = false;
            for (var i = 0; i < relicPositions.length; i++) {
                var dx = x - relicPositions[i][0];
                var dz = z - relicPositions[i][1];
                if (Math.sqrt(dx * dx + dz * dz) < 3) {
                    tooClose = true;
                    break;
                }
            }
            if (!tooClose) {
                return new pc.Vec3(x, 0, z);
            }
        }
    }
    return null;
};

EnvironmentGenerator.prototype.createGround = function () {
    var ground = new pc.Entity('Ground');
    ground.setPosition(0, -0.5, 0);
    ground.setLocalScale(this.groundSize, 1, this.groundSize);

    ground.addComponent('model', {
        type: 'box'
    });

    var groundMat = new pc.StandardMaterial();
    groundMat.diffuse.set(0.15, 0.25, 0.12);
    groundMat.emissive.set(0.02, 0.04, 0.02);
    groundMat.metalness = 0.0;
    groundMat.gloss = 0.3;
    groundMat.update();
    ground.model.model.meshInstances[0].material = groundMat;

    // Colisión
    ground.addComponent('collision', {
        type: 'box',
        halfExtents: new pc.Vec3(this.groundSize / 2, 0.5, this.groundSize / 2)
    });

    ground.addComponent('rigidbody', {
        type: 'static',
        friction: 0.8
    });

    this.app.root.addChild(ground);
};

EnvironmentGenerator.prototype.createTree = function (position) {
    var scale = 0.8 + Math.random() * 0.6;
    var treeGroup = new pc.Entity('Tree');
    treeGroup.setPosition(position);

    // Tronco
    var trunk = new pc.Entity('Trunk');
    trunk.setPosition(0, 2 * scale, 0);
    trunk.setLocalScale(0.4 * scale, 4 * scale, 0.4 * scale);
    trunk.addComponent('model', { type: 'cylinder' });

    var trunkMat = new pc.StandardMaterial();
    trunkMat.diffuse.set(0.25, 0.15, 0.08);
    trunkMat.emissive.set(0.02, 0.01, 0.005);
    trunkMat.roughness = 0.9;
    trunkMat.update();
    trunk.model.model.meshInstances[0].material = trunkMat;
    treeGroup.addChild(trunk);

    // Copa
    var canopy = new pc.Entity('Canopy');
    canopy.setPosition(0, 5 * scale, 0);
    canopy.setLocalScale(3 * scale, 3 * scale, 3 * scale);
    canopy.addComponent('model', { type: 'sphere' });

    var canopyMat = new pc.StandardMaterial();
    var greenVar = 0.1 + Math.random() * 0.15;
    canopyMat.diffuse.set(0.05, 0.2 + greenVar, 0.05);
    canopyMat.emissive.set(0.01, 0.03, 0.01);
    canopyMat.roughness = 0.8;
    canopyMat.update();
    canopy.model.model.meshInstances[0].material = canopyMat;
    treeGroup.addChild(canopy);

    // Colisión del tronco
    treeGroup.addComponent('collision', {
        type: 'cylinder',
        radius: 0.3 * scale,
        height: 4 * scale
    });
    treeGroup.addComponent('rigidbody', {
        type: 'static',
        friction: 0.8
    });

    this.app.root.addChild(treeGroup);
};

EnvironmentGenerator.prototype.createRock = function (position) {
    var scale = 0.3 + Math.random() * 0.8;
    var rock = new pc.Entity('Rock');
    rock.setPosition(position.x, scale * 0.4, position.z);
    rock.setLocalScale(
        scale * (0.8 + Math.random() * 0.4),
        scale * (0.6 + Math.random() * 0.4),
        scale * (0.8 + Math.random() * 0.4)
    );
    rock.setEulerAngles(0, Math.random() * 360, 0);

    rock.addComponent('model', { type: 'box' });

    var rockMat = new pc.StandardMaterial();
    var grayVar = 0.2 + Math.random() * 0.15;
    rockMat.diffuse.set(grayVar, grayVar * 0.95, grayVar * 0.9);
    rockMat.emissive.set(0.01, 0.01, 0.01);
    rockMat.roughness = 0.95;
    rockMat.update();
    rock.model.model.meshInstances[0].material = rockMat;

    this.app.root.addChild(rock);
};

EnvironmentGenerator.prototype.createMushroom = function (position) {
    var scale = 0.2 + Math.random() * 0.3;
    var mushroomGroup = new pc.Entity('Mushroom');
    mushroomGroup.setPosition(position);

    // Tallo
    var stem = new pc.Entity('MushroomStem');
    stem.setPosition(0, scale * 0.5, 0);
    stem.setLocalScale(0.08 * scale, scale, 0.08 * scale);
    stem.addComponent('model', { type: 'cylinder' });

    var stemMat = new pc.StandardMaterial();
    stemMat.diffuse.set(0.9, 0.85, 0.7);
    stemMat.update();
    stem.model.model.meshInstances[0].material = stemMat;
    mushroomGroup.addChild(stem);

    // Sombrero
    var cap = new pc.Entity('MushroomCap');
    cap.setPosition(0, scale * 1.1, 0);
    cap.setLocalScale(0.3 * scale, 0.15 * scale, 0.3 * scale);
    cap.addComponent('model', { type: 'sphere' });

    // Color aleatorio bioluminiscente
    var capMat = new pc.StandardMaterial();
    var glowColors = [
        { r: 0.1, g: 0.5, b: 0.8 },  // Azul
        { r: 0.1, g: 0.8, b: 0.5 },  // Verde azulado
        { r: 0.4, g: 0.2, b: 0.8 },  // Púrpura
        { r: 0.1, g: 0.7, b: 0.3 }   // Verde
    ];
    var glowColor = glowColors[Math.floor(Math.random() * glowColors.length)];
    capMat.diffuse.set(glowColor.r * 0.3, glowColor.g * 0.3, glowColor.b * 0.3);
    capMat.emissive.set(glowColor.r, glowColor.g, glowColor.b);
    capMat.update();
    cap.model.model.meshInstances[0].material = capMat;
    mushroomGroup.addChild(cap);

    // Luz tenue
    mushroomGroup.addComponent('light', {
        type: 'point',
        color: new pc.Color(glowColor.r, glowColor.g, glowColor.b),
        intensity: 0.5,
        range: 3,
        castShadows: false
    });

    this.app.root.addChild(mushroomGroup);
};

EnvironmentGenerator.prototype.createFireflies = function () {
    // Crear varias luciérnagas como pequeñas esferas con luz
    for (var i = 0; i < 20; i++) {
        var firefly = new pc.Entity('Firefly');
        var x = (Math.random() - 0.5) * this.groundSize * 0.8;
        var y = 1 + Math.random() * 4;
        var z = (Math.random() - 0.5) * this.groundSize * 0.8;
        firefly.setPosition(x, y, z);
        firefly.setLocalScale(0.05, 0.05, 0.05);

        firefly.addComponent('model', { type: 'sphere' });

        var mat = new pc.StandardMaterial();
        mat.diffuse.set(0.3, 0.5, 0.1);
        mat.emissive.set(0.8, 1, 0.3);
        mat.blendType = pc.BLEND_ADDITIVE;
        mat.update();
        firefly.model.model.meshInstances[0].material = mat;

        firefly.addComponent('light', {
            type: 'point',
            color: new pc.Color(0.8, 1, 0.3),
            intensity: 0.3,
            range: 2,
            castShadows: false
        });

        // Script simple de movimiento flotante
        firefly._basePos = new pc.Vec3(x, y, z);
        firefly._speed = 0.5 + Math.random() * 1;
        firefly._offset = Math.random() * Math.PI * 2;

        this.app.root.addChild(firefly);
    }

    // Actualizar luciérnagas en el update
    this._fireflyUpdate = true;
};

EnvironmentGenerator.prototype.update = function (dt) {
    if (!this._fireflyUpdate) return;

    var time = this.app.time.totalTime;
    var fireflies = this.app.root.children;
    for (var i = 0; i < fireflies.length; i++) {
        var f = fireflies[i];
        if (f.name === 'Firefly' && f._basePos) {
            var ox = Math.sin(time * f._speed + f._offset) * 0.5;
            var oy = Math.cos(time * f._speed * 0.7 + f._offset) * 0.3;
            var oz = Math.cos(time * f._speed * 0.5 + f._offset + 1) * 0.5;

            f.setPosition(
                f._basePos.x + ox,
                f._basePos.y + oy,
                f._basePos.z + oz
            );

            // Pulsar luz
            if (f.light) {
                f.light.intensity = 0.15 + Math.sin(time * 3 + f._offset) * 0.15;
            }
        }
    }
};

EnvironmentGenerator.prototype.createWorldBoundary = function () {
    // Paredes invisibles en los límites
    var halfSize = this.groundSize / 2;
    var wallHeight = 5;

    var walls = [
        { pos: [0, wallHeight / 2, -halfSize], scale: [this.groundSize, wallHeight, 1] },
        { pos: [0, wallHeight / 2, halfSize], scale: [this.groundSize, wallHeight, 1] },
        { pos: [-halfSize, wallHeight / 2, 0], scale: [1, wallHeight, this.groundSize] },
        { pos: [halfSize, wallHeight / 2, 0], scale: [1, wallHeight, this.groundSize] }
    ];

    for (var i = 0; i < walls.length; i++) {
        var w = walls[i];
        var wall = new pc.Entity('Wall_' + i);
        wall.setPosition(w.pos[0], w.pos[1], w.pos[2]);
        wall.setLocalScale(w.scale[0], w.scale[1], w.scale[2]);

        wall.addComponent('collision', {
            type: 'box',
            halfExtents: new pc.Vec3(w.scale[0] / 2, w.scale[1] / 2, w.scale[2] / 2)
        });

        wall.addComponent('rigidbody', {
            type: 'static'
        });

        this.app.root.addChild(wall);
    }
};

EnvironmentGenerator.prototype.destroy = function () {
    this.app.off('game:start', this.onGameStart, this);
};
