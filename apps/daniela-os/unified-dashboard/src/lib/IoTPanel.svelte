<script>
  import { onMount } from 'svelte'

  let status = null
  let devices = []
  let inventory = null
  let busy = false
  let msg = ''

  async function j(url, opts) {
    const r = await fetch(url, opts)
    return r.json()
  }

  async function load() {
    try {
      const s = await j('/api/iot/status')
      status = s
      const d = await j('/api/iot/devices')
      devices = d.devices || []
      inventory = await j('/api/iot/inventory')
    } catch (e) {
      msg = 'hub no disponible: ' + e.message
    }
  }

  async function toggle(dev) {
    const action = dev.state === 'off' ? 'on' : 'off'
    try {
      const body = await j('/api/iot/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entity_id: dev.entity_id, action }),
      })
      msg = body.ok ? `${dev.entity_id}: ${action}` : `fallo: ${body.error || 'sin detalle'}`
    } catch (e) {
      msg = 'control: ' + e.message
    }
    await load()
  }

  async function scan() {
    busy = true
    msg = 'escaneando intranet...'
    try {
      const b = await j('/api/iot/discovery', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}',
      })
      if (b.ok) {
        inventory = b.inventory
        msg = `scan: ${b.inventory.host_count} hosts (${b.inventory.method}, ${b.inventory.scan_seconds}s)`
      } else {
        msg = `scan: ${b.error}`
      }
    } catch (e) {
      msg = 'scan: ' + e.message
    }
    busy = false
  }

  onMount(load)

  $: backends = (status && status.backends) || {}
  $: haOn = backends.homeassistant && backends.homeassistant.status === 'ok'
  $: mqttOn = backends.mqtt && backends.mqtt.broker_reachable
  $: esphOn = backends.esphome && backends.esphome.available
</script>

<section>
  <div class="iot-head">
    <h2 style="font-size: 14px; font-weight: 500; color: var(--text-dim); text-transform: uppercase;">
      IoT / Domotica
    </h2>
    <div class="iot-actions">
      <button on:click={load} disabled={busy}>refrescar</button>
      <button on:click={scan} disabled={busy}>escanear red</button>
    </div>
  </div>

  <div class="iot-backends">
    <span class="iot-pill" class:on={haOn}>HA {haOn ? 'online' : 'off'}</span>
    <span class="iot-pill" class:on={mqttOn}>MQTT {mqttOn ? 'online' : 'off'}</span>
    <span class="iot-pill" class:on={esphOn}>ESPHome {esphOn ? 'online' : 'off'}</span>
    <span class="iot-pill">{devices.length} dispositivos</span>
    <span class="iot-pill">{inventory && inventory.host_count ? inventory.host_count + ' hosts' : 'sin inventario'}</span>
  </div>

  {#if msg}
    <p class="iot-msg">{msg}</p>
  {/if}

  <div class="iot-grid">
    {#each devices as dev (dev.entity_id)}
      <div class="card iot-dev" class:on={dev.state !== 'off' && dev.state !== 'unavailable'}>
        <div>
          <div style="font-weight: 600; font-size: 13px;">{dev.friendly_name || dev.entity_id}</div>
          <div style="font-size: 11px; color: var(--text-dim);">{dev.domain} · {dev.entity_id}</div>
        </div>
        <div style="text-align: right;">
          <div style="font-size: 12px;">{dev.state}</div>
          <button class="iot-toggle" on:click={() => toggle(dev)}>
            {dev.state === 'off' ? 'ON' : 'OFF'}
          </button>
        </div>
      </div>
    {:else}
      <p style="font-size: 12px; color: var(--text-dim);">
        Sin dispositivos sincronizados — llama a <code>POST /api/iot/sync</code> (Home Assistant).
      </p>
    {/each}
  </div>

  {#if inventory && inventory.hosts && inventory.hosts.length}
    <details style="margin-top: 12px;">
      <summary style="font-size: 12px; color: var(--text-dim); cursor: pointer;">
        Inventario de intranet ({inventory.hosts.length} hosts, {inventory.method})
      </summary>
      <div style="font-size: 11px; margin-top: 8px; display: grid; gap: 4px;">
        {#each inventory.hosts as h (h.ip)}
          <div>
            <strong>{h.ip}</strong>
            {#if h.mac}{h.mac}{/if}
            {#if h.vendor}· {h.vendor}{/if}
            {#if h.fuente}· {h.fuente}{/if}
          </div>
        {/each}
      </div>
    </details>
  {/if}
</section>

<style>
  .iot-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  .iot-actions {
    display: flex;
    gap: 8px;
  }
  .iot-actions button {
    background: transparent;
    border: 1px solid var(--border);
    color: inherit;
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 11px;
    cursor: pointer;
  }
  .iot-actions button:disabled {
    opacity: 0.5;
    cursor: wait;
  }
  .iot-backends {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 12px;
  }
  .iot-pill {
    font-size: 10px;
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 3px 10px;
    color: var(--text-dim);
  }
  .iot-pill.on {
    border-color: var(--green);
    color: var(--green);
  }
  .iot-msg {
    font-size: 11px;
    color: var(--text-dim);
    margin-bottom: 8px;
  }
  .iot-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 10px;
  }
  .iot-dev {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
  }
  .iot-dev.on {
    border-color: var(--green);
  }
  .iot-toggle {
    margin-top: 6px;
    background: transparent;
    border: 1px solid var(--border);
    color: inherit;
    border-radius: 6px;
    font-size: 10px;
    padding: 3px 8px;
    cursor: pointer;
  }
</style>
