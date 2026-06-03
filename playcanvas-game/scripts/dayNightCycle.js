/**
 * DayNightCycle - Ciclo día/noche dinámico para Arboleda
 * Cambia iluminación, cielo y ambiente según el ciclo.
 * Afecta comportamiento de enemigos y accesibilidad de áreas secretas.
 */
var DayNightCycle = pc.createScript('dayNightCycle');

DayNightCycle.attributes.add('cycleDuration', { type: 'number', default: 300, title: 'Duración del ciclo completo (seg)' });
DayNightCycle.attributes.add('dayAmbient', { type: 'rgb', default: [0.4, 0.4, 0.5], title: 'Color ambiente de día' });
DayNightCycle.attributes.add('nightAmbient', { type: 'rgb', default: [0.05, 0.05, 0.15], title: 'Color ambiente de noche' });
DayNightCycle.attributes.add('daySkyColor', { type: 'rgb', default: [0.5, 0.7, 0.9], title: 'Color del cielo de día' });
DayNightCycle.attributes.add('nightSkyColor', { type: 'rgb', default: [0.02, 0.02, 0.08], title: 'Color del cielo de noche' });
DayNightCycle.attributes.add('fogDensity', { type: 'number', default: 0.02, title: 'Densidad de niebla nocturna' });

DayNightCycle.prototype.initialize = function () {
    this.cycleProgress = 0; // 0-1 (0 = mediodía, 0.5 = medianoche)
    this.sunLight = this.app.root.findByName('DirectionalLight');
    this.ambientLight = this.app.root.findByName('AmbientLight');

    // Registrar eventos
    this.app.on('daynight:setTime', this.setTime, this);
    this.app.on('game:start', this.onGameStart, this);
};

DayNightCycle.prototype.onGameStart = function () {
    this.cycleProgress = 0;
};

DayNightCycle.prototype.update = function (dt) {
    // Avanzar ciclo
    this.cycleProgress += dt / this.cycleDuration;
    if (this.cycleProgress >= 1) this.cycleProgress -= 1;

    // Calcular factor de día (1 = pleno día, 0 = plena noche)
    var dayFactor = Math.cos(this.cycleProgress * Math.PI * 2) * 0.5 + 0.5;

    // Interpolar color del cielo
    var skyColor = new pc.Color();
    skyColor.r = pc.math.lerp(this.nightSkyColor.r, this.daySkyColor.r, dayFactor);
    skyColor.g = pc.math.lerp(this.nightSkyColor.g, this.daySkyColor.g, dayFactor);
    skyColor.b = pc.math.lerp(this.nightSkyColor.b, this.daySkyColor.b, dayFactor);

    // Aplicar al cielo de la escena
    this.app.scene.skybox && (this.app.scene.skybox = null);
    this.app.scene.fogColor = skyColor;

    // Ajustar luz direccional (sol/luna)
    if (this.sunLight && this.sunLight.light) {
        this.sunLight.light.intensity = pc.math.lerp(0.1, 1.5, dayFactor);

        // Ángulo del sol
        var sunAngle = this.cycleProgress * 360;
        this.sunLight.setEulerAngles(
            pc.math.lerp(-20, 70, dayFactor),
            sunAngle,
            0
        );

        // Color de la luz
        var sunColor = new pc.Color();
        sunColor.r = pc.math.lerp(0.3, 1.0, dayFactor);
        sunColor.g = pc.math.lerp(0.3, 0.95, dayFactor);
        sunColor.b = pc.math.lerp(0.5, 0.85, dayFactor);
        this.sunLight.light.color = sunColor;
    }

    // Ajustar luz ambiente
    if (this.ambientLight && this.ambientLight.light) {
        var ambColor = new pc.Color();
        ambColor.r = pc.math.lerp(this.nightAmbient.r, this.dayAmbient.r, dayFactor);
        ambColor.g = pc.math.lerp(this.nightAmbient.g, this.dayAmbient.g, dayFactor);
        ambColor.b = pc.math.lerp(this.nightAmbient.b, this.dayAmbient.b, dayFactor);
        this.ambientLight.light.color = ambColor;
        this.ambientLight.light.intensity = pc.math.lerp(0.2, 0.6, dayFactor);
    }

    // Niebla nocturna
    if (this.app.scene.fog) {
        this.app.scene.fogDensity = pc.math.lerp(this.fogDensity, 0.001, dayFactor);
    }

    // Emitir estado para otros sistemas
    this.app.fire('daynight:factor', dayFactor);
    this.app.fire('daynight:isNight', dayFactor < 0.3);
};

DayNightCycle.prototype.setTime = function (progress) {
    this.cycleProgress = pc.math.clamp(progress, 0, 1);
};

DayNightCycle.prototype.destroy = function () {
    this.app.off('daynight:setTime', this.setTime, this);
    this.app.off('game:start', this.onGameStart, this);
};
