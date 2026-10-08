/**
 * Daniela OS — Jarvis Desktop Overlay
 * Mode 6: Geolocation
 * Globe with GPS position + geofence zones + real-time tracking
 */

class GeolocationMode {
  constructor(scene) {
    this.scene = scene;
    this.group = new THREE.Group();
    this.globe = null;
    this.userMarker = null;
    this.homeZone = null;
    this.zones = [];
    this.visible = false;
    this.time = 0;
    this.userPos = null;

    this.homeCoords = { lat: 40.4, lon: -3.7, radius: 5000 }; // Default: Madrid

    this.build();
  }

  latLonToVector3(lat, lon, radius) {
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);
    return new THREE.Vector3(
      -(radius * Math.sin(phi) * Math.cos(theta)),
      (radius * Math.sin(phi) * Math.sin(theta)),
      (radius * Math.cos(phi))
    );
  }

  build() {
    // Lights
    const ambient = new THREE.AmbientLight(0x404080, 0.3);
    const sun = new THREE.DirectionalLight(0xffffff, 1);
    sun.position.set(5, 3, 5);
    this.group.add(ambient, sun);

    // Globe
    const globeGeo = new THREE.SphereGeometry(1, 128, 128);
    const globeMat = new THREE.MeshPhongMaterial({
      color: 0x0a0a1a, emissive: 0x0a0a2a, specular: 0x0ea5e9, shininess: 100,
      opacity: 0.95, transparent: true
    });
    this.globe = new THREE.Mesh(globeGeo, globeMat);
    this.group.add(this.globe);

    // Wireframe
    const wireGeo = new THREE.SphereGeometry(1.005, 64, 64);
    const wireMat = new THREE.MeshBasicMaterial({ wireframe: true, color: 0x0ea5e9, opacity: 0.08, transparent: true });
    this.globe.add(new THREE.Mesh(wireGeo, wireMat));

    // Atmosphere
    const atmoGeo = new THREE.SphereGeometry(1.15, 64, 64);
    const atmoMat = new THREE.ShaderMaterial({
      vertexShader: `varying vec3 vNormal; void main() { vNormal = normalize(normalMatrix * normal); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
      fragmentShader: `varying vec3 vNormal; void main() { float intensity = pow(0.6 - dot(vNormal, vec3(0, 0, 1.0)), 2.0); gl_FragColor = vec4(0.05, 0.65, 0.91, 1.0) * intensity * 0.8; }`,
      side: THREE.BackSide, blending: THREE.AdditiveBlending, transparent: true
    });
    this.group.add(new THREE.Mesh(atmoGeo, atmoMat));

    // Home zone ring
    this.homeZone = this.createZoneRing(this.homeCoords.lat, this.homeCoords.lon, 0.05, 0x00ff66, 'HOME');
    this.globe.add(this.homeZone.ring);
    this.globe.add(this.homeZone.label);
    this.zones.push(this.homeZone);

    // User position marker
    this.userMarker = this.createUserMarker(this.homeCoords.lat, this.homeCoords.lon);
    this.globe.add(this.userMarker.mesh);
    this.globe.add(this.userMarker.pulse);
    this.globe.add(this.userMarker.label);

    // Stars
    const starCount = 1500;
    const starPos = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount; i++) {
      const i3 = i * 3;
      starPos[i3] = (Math.random() - 0.5) * 200;
      starPos[i3 + 1] = (Math.random() - 0.5) * 200;
      starPos[i3 + 2] = (Math.random() - 0.5) * 200;
    }
    const starGeo = new THREE.BufferGeometry();
    starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
    const starMat = new THREE.PointsMaterial({ color: 0xffffff, size: 0.05, transparent: true, opacity: 0.5 });
    this.stars = new THREE.Points(starGeo, starMat);
    this.scene.add(this.stars);

    this.scene.add(this.group);
    this.group.visible = false;
  }

  createZoneRing(lat, lon, radius, color, name) {
    const center = this.latLonToVector3(lat, lon, 1.01);

    // Ring as circle of points
    const points = [];
    for (let i = 0; i <= 64; i++) {
      const angle = (i / 64) * Math.PI * 2;
      const offsetLat = lat + (radius * 111000 * Math.cos(angle)) / 111000;
      const offsetLon = lon + (radius * 111000 * Math.sin(angle)) / (111000 * Math.cos(lat * Math.PI / 180));
      points.push(this.latLonToVector3(offsetLat, offsetLon, 1.015));
    }

    const ringGeo = new THREE.BufferGeometry().setFromPoints(points);
    const ringMat = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.5 });
    const ring = new THREE.Line(ringGeo, ringMat);

    // Label
    const canvas = document.createElement('canvas');
    canvas.width = 128;
    canvas.height = 32;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#' + color.toString(16).padStart(6, '0');
    ctx.font = 'bold 16px monospace';
    ctx.fillText(name, 4, 20);
    const tex = new THREE.CanvasTexture(canvas);
    const spriteMat = new THREE.SpriteMaterial({ map: tex, transparent: true, opacity: 0.7 });
    const label = new THREE.Sprite(spriteMat);
    const labelPos = center.clone().multiplyScalar(1.1);
    label.position.copy(labelPos);
    label.scale.set(0.3, 0.08, 1);

    return { ring, label, lat, lon, radius };
  }

  createUserMarker(lat, lon) {
    const pos = this.latLonToVector3(lat, lon, 1.02);

    // Main marker
    const geo = new THREE.SphereGeometry(0.03, 12, 12);
    const mat = new THREE.MeshBasicMaterial({ color: 0xff0055 });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(pos);

    // Pulse ring
    const pulseGeo = new THREE.RingGeometry(0.04, 0.06, 32);
    const pulseMat = new THREE.MeshBasicMaterial({ color: 0xff0055, transparent: true, opacity: 0.3, side: THREE.DoubleSide });
    const pulse = new THREE.Mesh(pulseGeo, pulseMat);
    pulse.position.copy(pos);
    pulse.lookAt(new THREE.Vector3(0, 0, 0));

    // Label
    const canvas = document.createElement('canvas');
    canvas.width = 128;
    canvas.height = 32;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#ff0055';
    ctx.font = 'bold 14px monospace';
    ctx.fillText('YOU', 4, 20);
    const tex = new THREE.CanvasTexture(canvas);
    const spriteMat = new THREE.SpriteMaterial({ map: tex, transparent: true, opacity: 0.8 });
    const label = new THREE.Sprite(spriteMat);
    label.position.copy(pos).multiplyScalar(1.15);
    label.scale.set(0.25, 0.06, 1);

    return { mesh, pulse, label };
  }

  updateUserPosition(lat, lon) {
    this.userPos = { lat, lon };
    const pos = this.latLonToVector3(lat, lon, 1.02);
    this.userMarker.mesh.position.copy(pos);
    this.userMarker.pulse.position.copy(pos);
    this.userMarker.pulse.lookAt(new THREE.Vector3(0, 0, 0));
    this.userMarker.label.position.copy(pos).multiplyScalar(1.15);
  }

  async fetchGPS() {
    try {
      const resp = await fetch('http://localhost:5000/api/pixel/sensors/live', { signal: AbortSignal.timeout(3000) });
      if (resp.ok) {
        const data = await resp.json();
        if (data.latitude && data.longitude) {
          this.updateUserPosition(data.latitude, data.longitude);
          return;
        }
      }
    } catch (e) {}

    // Try geofence config
    try {
      const resp = await fetch('http://localhost:5000/api/pixel/geofence/status', { signal: AbortSignal.timeout(3000) });
      if (resp.ok) {
        const data = await resp.json();
        if (data.current_lat && data.current_lon) {
          this.updateUserPosition(data.current_lat, data.current_lon);
        }
      }
    } catch (e) {}
  }

  show() {
    this.visible = true;
    this.group.visible = true;
    if (this.stars) this.stars.visible = true;
    this.fetchGPS();
    this.gpsInterval = setInterval(() => this.fetchGPS(), 5000);
  }

  hide() {
    this.visible = false;
    this.group.visible = false;
    if (this.stars) this.stars.visible = false;
    if (this.gpsInterval) clearInterval(this.gpsInterval);
  }

  update(time, mouse) {
    if (!this.visible) return;
    this.time = time;

    if (this.globe) {
      this.globe.rotation.y += 0.001;
      this.globe.rotation.x = mouse.y * 0.1;
    }

    this.group.rotation.y += (mouse.x * 0.2 - this.group.rotation.y) * 0.02;

    // Pulse user marker
    if (this.userMarker) {
      this.userMarker.pulse.scale.setScalar(1 + Math.sin(time * 3) * 0.3);
      this.userMarker.pulse.material.opacity = 0.2 + Math.sin(time * 3) * 0.15;
    }
  }
}

window.GeolocationMode = GeolocationMode;
