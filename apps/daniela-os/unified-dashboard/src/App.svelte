<script>
  import { onMount } from 'svelte'
  import { SERVICES, serviceStatus, fetchAllStatuses, startPolling, getStatusClass, getStatusLabel } from './lib/stores.js'
  import ServiceCard from './lib/ServiceCard.svelte'
  import WebSocketStatus from './lib/WebSocketStatus.svelte'
  import IoTPanel from './lib/IoTPanel.svelte'
  
  let expandedService = null
  let pollingTimer = null
  
  function refresh() {
    fetchAllStatuses()
  }
  
  function toggleExpand(id) {
    expandedService = expandedService === id ? null : id
  }
  
  onMount(() => {
    fetchAllStatuses()
    pollingTimer = startPolling(5000)
  })
  
  $: serviceGroups = {
    Core: SERVICES.filter(s => s.category === 'Core'),
    AI: SERVICES.filter(s => s.category === 'AI'),
    Infra: SERVICES.filter(s => s.category === 'Infra'),
    Frontend: SERVICES.filter(s => s.category === 'Frontend'),
    Security: SERVICES.filter(s => s.category === 'Security'),
    Perf: SERVICES.filter(s => s.category === 'Perf')
  }
  
  $: onlineCount = Object.values($serviceStatus).filter(s => s.status === 'online' || s.status === 'alive').length
  $: totalCount = SERVICES.length
</script>

<div class="min-h-screen p-4" style="max-width: 1400px; margin: 0 auto;">
  <!-- Header -->
  <header class="flex justify-between items-center mb-8 pb-4 border-b" style="border-color: var(--border);">
    <div>
      <h1 style="font-size: 24px; font-weight: 700;">aig Unified Dashboard</h1>
      <p style="font-size: 12px; color: var(--text-dim); margin-top: 4px;">
        {onlineCount} / {totalCount} services online
      </p>
    </div>
    <WebSocketStatus bind:refresh />
  </header>

  <!-- Stats Overview -->
  <section class="grid grid-4 mb-8">
    <div class="card stat">
      <div class="stat-value" style="color: var(--green);">{onlineCount}</div>
      <div class="stat-label">Online</div>
    </div>
    <div class="card stat">
      <div class="stat-value" style="color: var(--red);">{totalCount - onlineCount}</div>
      <div class="stat-label">Offline</div>
    </div>
    <div class="card stat">
      <div class="stat-value">{SERVICES.length}</div>
      <div class="stat-label">Total Services</div>
    </div>
    <div class="card stat">
      <div class="stat-value">{Math.round((onlineCount / totalCount) * 100)}%</div>
      <div class="stat-label">Uptime</div>
    </div>
  </section>

  <!-- IoT -->
  <section class="card mb-8" style="margin-bottom: 32px; padding: 16px;">
    <IoTPanel />
  </section>

  <!-- Service Categories -->
  <section class="space-y-8">
    {#each Object.entries(serviceGroups) as [category, services]}
      {#if services.length > 0}
        <div>
          <h2 style="font-size: 14px; font-weight: 500; color: var(--text-dim); margin-bottom: 12px; text-transform: uppercase;">
            {category}
          </h2>
          <div class="grid grid-3">
            {#each services as svc}
              <ServiceCard
                service={svc}
                status={$serviceStatus[svc.id] || {}}
                expanded={expandedService === svc.id}
                on:click={() => toggleExpand(svc.id)}
              />
            {/each}
          </div>
        </div>
      {/if}
    {/each}
  </section>

  <!-- Footer -->
  <footer class="mt-12 pt-8 border-t" style="border-color: var(--border); text-align: center; font-size: 10px; color: var(--text-dim);">
    <p>aig Unified Dashboard • {new Date().toLocaleString()}</p>
    <p>Services: {SERVICES.map(s => s.name).join(', ')}</p>
  </footer>
</div>

<style>
  :global(body) { padding: 0; }
</style>