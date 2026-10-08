<script>
  import { getStatusClass, getStatusLabel, getServiceUrl } from '../lib/stores.js'
  
  export let service = {}
  export let status = {}
  export let metrics = {}
  export let expanded = false
  
  function toggleExpand() {
    expanded = !expanded
  }
  
  function openService() {
    window.open(getServiceUrl(service), '_blank')
  }
</script>

<div class="card" class:critical={statusClass === 'offline'} class:warning={statusClass === 'degraded'} class:healthy={statusClass === 'online'}>
  <div class="flex justify-between items-center">
    <div class="flex items-center gap-2">
      <h3>{service.name}</h3>
      <span class="badge" class:{statusClass}>{statusLabel}</span>
    </div>
    <button class="btn" on:click={openService}>Open</button>
  </div>
  
  <div class="flex justify-between gap-4 mt-4" style="font-size: 12px;">
    <div class="stat">
      <div class="stat-value">{status.port || '-'}</div>
      <div class="stat-label">Port</div>
    </div>
    <div class="stat">
      <div class="stat-value">{status.modules || status.total_ideas || '-'}</div>
      <div class="stat-label">Modules</div>
    </div>
    <div class="stat">
      <div class="stat-value">{status.version || '-'}</div>
      <div class="stat-label">Version</div>
    </div>
  </div>
  
  {#if expanded && status}
    <details open class="mt-4">
      <summary class="flex justify-between cursor-pointer" style="font-size: 11px; color: var(--text-dim);">
        Details
      </summary>
      <pre class="mt-2" style="font-size: 10px; background: var(--bg); padding: 12px; border-radius: 8px; overflow: auto; max-height: 200px;">
        {JSON.stringify(status, null, 2)}
      </pre>
    </details>
  {/if}
</div>

<style>
  .card { transition: all 0.2s; }
  details summary { list-style: none; }
  details summary::-webkit-details-marker { display: none; }
  details summary::before { content: '▶'; display: inline-block; margin-right: 8px; transition: transform 0.2s; }
  details[open] summary::before { transform: rotate(90deg); }
</style>