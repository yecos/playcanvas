/**
 * CameraFollow - Cámara en 3ra persona que sigue a Alex
 * Soporta rotación con mouse/touch, zoom con rueda, y seguimiento suave.
 */
var CameraFollow = pc.createScript('cameraFollow');

CameraFollow.attributes.add('distance', { type: 'number', default: 8, title: 'Distancia al jugador' });
CameraFollow.attributes.add('height', { type: 'number', default: 4, title: 'Altura de la cámara' });
CameraFollow.attributes.add('lookAtHeight', { type: 'number', default: 1.5, title: 'Altura de mira' });
CameraFollow.attributes.add('followSpeed', { type: 'number', default: 5, title: 'Velocidad de seguimiento' });
CameraFollow.attributes.add('rotateSpeed', { type: 'number', default: 100, title: 'Velocidad de rotación' });
CameraFollow.attributes.add('minDistance', { type: 'number', default: 3, title: 'Distancia mínima (zoom)' });
CameraFollow.attributes.add('maxDistance', { type: 'number', default: 20, title: 'Distancia máxima (zoom)' });
CameraFollow.attributes.add('minPitch', { type: 'number', default: -20, title: 'Pitch mínimo (grados)' });
CameraFollow.attributes.add('maxPitch', { type: 'number', default: 60, title: 'Pitch máximo (grados)' });

CameraFollow.prototype.initialize = function () {
    // Target a seguir
    this.target = this.app.root.findByName('Player');
    if (!this.target) {
        console.warn('CameraFollow: No se encontró entidad Player');
    }

    // Ángulos de cámara
    this.yaw = 0;
    this.pitch = -20;

    // Estado de rotación con mouse
    this.isRotating = false;
    this.lastMousePos = { x: 0, y: 0 };

    // Posición actual de cámara (suavizado)
    this.currentPos = new pc.Vec3();

    // Eventos de mouse
    this.app.mouse.on(pc.EVENT_MOUSEDOWN, this.onMouseDown, this);
    this.app.mouse.on(pc.EVENT_MOUSEUP, this.onMouseUp, this);
    this.app.mouse.on(pc.EVENT_MOUSEMOVE, this.onMouseMove, this);
    this.app.mouse.on(pc.EVENT_MOUSEWHEEL, this.onMouseWheel, this);

    // Eventos de touch
    this.app.touch && this.app.touch.on(pc.EVENT_TOUCHSTART, this.onTouchStart, this);
    this.app.touch && this.app.touch.on(pc.EVENT_TOUCHMOVE, this.onTouchMove, this);
    this.app.touch && this.app.touch.on(pc.EVENT_TOUCHEND, this.onTouchEnd, this);

    // Touch tracking
    this.lastTouchPos = { x: 0, y: 0 };
    this.touchRotating = false;
    this.touchId = -1;

    // Inicializar posición
    if (this.target) {
        var targetPos = this.target.getPosition();
        this.currentPos.set(targetPos.x, targetPos.y + this.height, targetPos.z + this.distance);
    }

    // Desactivar cursor durante rotación
    this.app.mouse.disableContextMenu();
};

CameraFollow.prototype.update = function (dt) {
    if (!this.target) return;

    var targetPos = this.target.getPosition();

    // Calcular posición deseada de la cámara
    var yawRad = this.yaw * pc.math.DEG_TO_RAD;
    var pitchRad = this.pitch * pc.math.DEG_TO_RAD;

    // Offset basado en ángulos
    var offsetX = this.distance * Math.sin(yawRad) * Math.cos(pitchRad);
    var offsetY = this.distance * Math.sin(pitchRad);
    var offsetZ = this.distance * Math.cos(yawRad) * Math.cos(pitchRad);

    var desiredPos = new pc.Vec3(
        targetPos.x + offsetX,
        targetPos.y + this.height + offsetY,
        targetPos.z + offsetZ
    );

    // Suavizar movimiento
    this.currentPos.lerp(this.currentPos, desiredPos, Math.min(1, this.followSpeed * dt));

    // Aplicar posición
    this.entity.setPosition(this.currentPos);

    // Mirar al target
    var lookAt = new pc.Vec3(targetPos.x, targetPos.y + this.lookAtHeight, targetPos.z);
    this.entity.lookAt(lookAt);
};

CameraFollow.prototype.onMouseDown = function (e) {
    // Botón derecho o medio para rotar
    if (e.button === pc.MOUSEBUTTON_RIGHT || e.button === pc.MOUSEBUTTON_MIDDLE) {
        this.isRotating = true;
        this.lastMousePos.x = e.x;
        this.lastMousePos.y = e.y;
    }
};

CameraFollow.prototype.onMouseUp = function (e) {
    if (e.button === pc.MOUSEBUTTON_RIGHT || e.button === pc.MOUSEBUTTON_MIDDLE) {
        this.isRotating = false;
    }
};

CameraFollow.prototype.onMouseMove = function (e) {
    if (!this.isRotating) return;

    var dx = e.x - this.lastMousePos.x;
    var dy = e.y - this.lastMousePos.y;

    this.yaw -= dx * this.rotateSpeed * 0.01;
    this.pitch += dy * this.rotateSpeed * 0.01;
    this.pitch = pc.math.clamp(this.pitch, this.minPitch, this.maxPitch);

    this.lastMousePos.x = e.x;
    this.lastMousePos.y = e.y;
};

CameraFollow.prototype.onMouseWheel = function (e) {
    this.distance += e.wheel * -0.5;
    this.distance = pc.math.clamp(this.distance, this.minDistance, this.maxDistance);
};

CameraFollow.prototype.onTouchStart = function (e) {
    // Usar el segundo toque para rotar la cámara
    if (e.touches.length === 2) {
        this.touchRotating = true;
        this.touchId = e.touches[1].id;
        this.lastTouchPos.x = e.touches[1].x;
        this.lastTouchPos.y = e.touches[1].y;
        e.event.preventDefault();
    }
};

CameraFollow.prototype.onTouchMove = function (e) {
    if (!this.touchRotating) return;

    for (var i = 0; i < e.changedTouches.length; i++) {
        if (e.changedTouches[i].id === this.touchId) {
            var dx = e.changedTouches[i].x - this.lastTouchPos.x;
            var dy = e.changedTouches[i].y - this.lastTouchPos.y;

            this.yaw -= dx * this.rotateSpeed * 0.02;
            this.pitch += dy * this.rotateSpeed * 0.02;
            this.pitch = pc.math.clamp(this.pitch, this.minPitch, this.maxPitch);

            this.lastTouchPos.x = e.changedTouches[i].x;
            this.lastTouchPos.y = e.changedTouches[i].y;
            break;
        }
    }
    e.event.preventDefault();
};

CameraFollow.prototype.onTouchEnd = function (e) {
    if (e.touches.length < 2) {
        this.touchRotating = false;
        this.touchId = -1;
    }
};

CameraFollow.prototype.destroy = function () {
    this.app.mouse.off(pc.EVENT_MOUSEDOWN, this.onMouseDown, this);
    this.app.mouse.off(pc.EVENT_MOUSEUP, this.onMouseUp, this);
    this.app.mouse.off(pc.EVENT_MOUSEMOVE, this.onMouseMove, this);
    this.app.mouse.off(pc.EVENT_MOUSEWHEEL, this.onMouseWheel, this);
    this.app.touch && this.app.touch.off(pc.EVENT_TOUCHSTART, this.onTouchStart, this);
    this.app.touch && this.app.touch.off(pc.EVENT_TOUCHMOVE, this.onTouchMove, this);
    this.app.touch && this.app.touch.off(pc.EVENT_TOUCHEND, this.onTouchEnd, this);
};
