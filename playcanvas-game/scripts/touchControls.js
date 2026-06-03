/**
 * TouchControls - Controles táctiles para móvil (joystick + botones)
 * Crea overlay HTML con joystick virtual izquierdo y zona de rotación derecha.
 * Solo se muestra en dispositivos táctiles.
 */
var TouchControls = pc.createScript('touchControls');

TouchControls.attributes.add('joystickSize', { type: 'number', default: 120, title: 'Tamaño del joystick (px)' });
TouchControls.attributes.add('joystickDeadzone', { type: 'number', default: 0.15, title: 'Zona muerta del joystick' });
TouchControls.attributes.add('buttonSize', { type: 'number', default: 60, title: 'Tamaño de botones (px)' });

TouchControls.prototype.initialize = function () {
    this.isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);

    if (!this.isTouchDevice) {
        this.enabled = false;
        return;
    }

    this.createUI();
    this.joystickData = { x: 0, y: 0, active: false };
    this.joystickOrigin = null;
    this.joystickTouchId = -1;

    // Touch events
    this.app.touch.on(pc.EVENT_TOUCHSTART, this.onTouchStart, this);
    this.app.touch.on(pc.EVENT_TOUCHMOVE, this.onTouchMove, this);
    this.app.touch.on(pc.EVENT_TOUCHEND, this.onTouchEnd, this);
};

TouchControls.prototype.createUI = function () {
    // Crear estilos CSS
    var style = document.createElement('style');
    style.textContent = `
        .arboleda-touch-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 9999;
        }
        .arboleda-joystick-area {
            position: absolute;
            bottom: 20px;
            left: 20px;
            width: 180px;
            height: 180px;
            pointer-events: auto;
            touch-action: none;
        }
        .arboleda-joystick-base {
            position: absolute;
            width: ${this.joystickSize}px;
            height: ${this.joystickSize}px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.15);
            border: 2px solid rgba(255, 255, 255, 0.3);
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
        }
        .arboleda-joystick-thumb {
            position: absolute;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.5);
            border: 2px solid rgba(255, 255, 255, 0.7);
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            transition: transform 0.05s;
        }
        .arboleda-btn-area {
            position: absolute;
            bottom: 20px;
            right: 20px;
            pointer-events: auto;
            touch-action: none;
        }
        .arboleda-btn {
            width: ${this.buttonSize}px;
            height: ${this.buttonSize}px;
            border-radius: 50%;
            border: 2px solid rgba(255, 255, 255, 0.5);
            background: rgba(255, 255, 255, 0.15);
            color: rgba(255, 255, 255, 0.8);
            font-size: 14px;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 8px;
            user-select: none;
            -webkit-user-select: none;
        }
        .arboleda-btn-attack {
            background: rgba(255, 80, 80, 0.3);
            border-color: rgba(255, 80, 80, 0.6);
        }
        .arboleda-btn-dodge {
            background: rgba(80, 180, 255, 0.3);
            border-color: rgba(80, 180, 255, 0.6);
        }
        .arboleda-btn-ability {
            width: 44px;
            height: 44px;
            font-size: 11px;
            display: inline-flex;
        }
        .arboleda-ability-row {
            position: absolute;
            bottom: 140px;
            right: 10px;
            display: flex;
            gap: 4px;
            pointer-events: auto;
            touch-action: none;
        }
        .arboleda-btn-water { background: rgba(50, 150, 255, 0.3); border-color: rgba(50, 150, 255, 0.6); }
        .arboleda-btn-fire { background: rgba(255, 80, 30, 0.3); border-color: rgba(255, 80, 30, 0.6); }
        .arboleda-btn-earth { background: rgba(80, 200, 50, 0.3); border-color: rgba(80, 200, 50, 0.6); }
        .arboleda-btn-air { background: rgba(200, 200, 255, 0.3); border-color: rgba(200, 200, 255, 0.6); }
    `;
    document.head.appendChild(style);

    // Crear overlay
    var overlay = document.createElement('div');
    overlay.className = 'arboleda-touch-overlay';
    overlay.id = 'arboleda-overlay';

    // Joystick
    var joystickArea = document.createElement('div');
    joystickArea.className = 'arboleda-joystick-area';
    joystickArea.id = 'joystick-area';

    var joystickBase = document.createElement('div');
    joystickBase.className = 'arboleda-joystick-base';

    var joystickThumb = document.createElement('div');
    joystickThumb.className = 'arboleda-joystick-thumb';
    joystickThumb.id = 'joystick-thumb';

    joystickArea.appendChild(joystickBase);
    joystickArea.appendChild(joystickThumb);

    // Botones de acción
    var btnArea = document.createElement('div');
    btnArea.className = 'arboleda-btn-area';

    var attackBtn = document.createElement('div');
    attackBtn.className = 'arboleda-btn arboleda-btn-attack';
    attackBtn.textContent = '⚔';
    attackBtn.id = 'btn-attack';

    var dodgeBtn = document.createElement('div');
    dodgeBtn.className = 'arboleda-btn arboleda-btn-dodge';
    dodgeBtn.textContent = '↺';
    dodgeBtn.id = 'btn-dodge';

    btnArea.appendChild(attackBtn);
    btnArea.appendChild(dodgeBtn);

    // Botones de habilidades
    var abilityRow = document.createElement('div');
    abilityRow.className = 'arboleda-ability-row';
    abilityRow.id = 'ability-row';

    var abilities = [
        { type: 'water', label: '💧', cls: 'arboleda-btn-water' },
        { type: 'fire', label: '🔥', cls: 'arboleda-btn-fire' },
        { type: 'earth', label: '🌿', cls: 'arboleda-btn-earth' },
        { type: 'air', label: '💨', cls: 'arboleda-btn-air' }
    ];

    for (var i = 0; i < abilities.length; i++) {
        var abilBtn = document.createElement('div');
        abilBtn.className = 'arboleda-btn arboleda-btn-ability ' + abilities[i].cls;
        abilBtn.textContent = abilities[i].label;
        abilBtn.dataset.type = abilities[i].type;
        abilityRow.appendChild(abilBtn);
    }

    overlay.appendChild(joystickArea);
    overlay.appendChild(btnArea);
    overlay.appendChild(abilityRow);

    document.body.appendChild(overlay);

    // Event listeners para botones
    this.setupButtonListeners();
};

TouchControls.prototype.setupButtonListeners = function () {
    var self = this;

    // Botón de ataque
    var attackBtn = document.getElementById('btn-attack');
    if (attackBtn) {
        attackBtn.addEventListener('touchstart', function (e) {
            e.preventDefault();
            self.app.fire('input:attack');
        });
    }

    // Botón de esquiva
    var dodgeBtn = document.getElementById('btn-dodge');
    if (dodgeBtn) {
        dodgeBtn.addEventListener('touchstart', function (e) {
            e.preventDefault();
            self.app.fire('input:dodge');
        });
    }

    // Botones de habilidades
    var abilityRow = document.getElementById('ability-row');
    if (abilityRow) {
        abilityRow.addEventListener('touchstart', function (e) {
            e.preventDefault();
            var target = e.target;
            if (target.dataset.type) {
                self.app.fire('input:ability', target.dataset.type);
            }
        });
    }

    // Joystick
    var joystickArea = document.getElementById('joystick-area');
    if (joystickArea) {
        joystickArea.addEventListener('touchstart', function (e) {
            e.preventDefault();
            var touch = e.changedTouches[0];
            self.joystickTouchId = touch.identifier;
            var rect = joystickArea.getBoundingClientRect();
            self.joystickOrigin = {
                x: rect.left + rect.width / 2,
                y: rect.top + rect.height / 2
            };
        });

        joystickArea.addEventListener('touchmove', function (e) {
            e.preventDefault();
            for (var i = 0; i < e.changedTouches.length; i++) {
                if (e.changedTouches[i].identifier === self.joystickTouchId) {
                    var touch = e.changedTouches[i];
                    var dx = touch.clientX - self.joystickOrigin.x;
                    var dy = touch.clientY - self.joystickOrigin.y;
                    var maxDist = self.joystickSize / 2;

                    // Normalizar
                    var dist = Math.sqrt(dx * dx + dy * dy);
                    var nx = dx / maxDist;
                    var ny = dy / maxDist;

                    // Clamp
                    if (dist > maxDist) {
                        nx = (dx / dist);
                        ny = (dy / dist);
                    }

                    // Deadzone
                    if (Math.abs(nx) < self.joystickDeadzone) nx = 0;
                    if (Math.abs(ny) < self.joystickDeadzone) ny = 0;

                    self.joystickData.x = nx;
                    self.joystickData.y = ny;
                    self.joystickData.active = true;

                    // Actualizar thumb visual
                    var thumb = document.getElementById('joystick-thumb');
                    if (thumb) {
                        thumb.style.transform = 'translate(calc(-50% + ' + (nx * maxDist * 0.5) + 'px), calc(-50% + ' + (ny * maxDist * 0.5) + 'px))';
                    }

                    // Emitir a PlayerController
                    self.app.fire('joystick:move', nx, ny);
                    break;
                }
            }
        });

        joystickArea.addEventListener('touchend', function (e) {
            for (var i = 0; i < e.changedTouches.length; i++) {
                if (e.changedTouches[i].identifier === self.joystickTouchId) {
                    self.joystickTouchId = -1;
                    self.joystickData.x = 0;
                    self.joystickData.y = 0;
                    self.joystickData.active = false;

                    // Reset thumb
                    var thumb = document.getElementById('joystick-thumb');
                    if (thumb) {
                        thumb.style.transform = 'translate(-50%, -50%)';
                    }

                    self.app.fire('joystick:release');
                    break;
                }
            }
        });
    }
};

TouchControls.prototype.destroy = function () {
    this.app.touch.off(pc.EVENT_TOUCHSTART, this.onTouchStart, this);
    this.app.touch.off(pc.EVENT_TOUCHMOVE, this.onTouchMove, this);
    this.app.touch.off(pc.EVENT_TOUCHEND, this.onTouchEnd, this);

    var overlay = document.getElementById('arboleda-overlay');
    if (overlay) {
        overlay.parentNode.removeChild(overlay);
    }
};
