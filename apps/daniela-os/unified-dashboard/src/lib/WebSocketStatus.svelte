<script>
  import { wsConnected, lastUpdate } from '../lib/stores.js'
</script>

<div class="flex items-center gap-2" style="font-size: 12px;">
  <span class="flex items-center gap-2">
    <span class="w-2 h-2 rounded-full" class:animate-pulse={$wsConnected} 
          style="background: {$wsConnected ? 'var(--green)' : 'var(--red)'};"></span>
    <span>{$wsConnected ? 'Live' : 'Polling'}</span>
  </span>
  {#if $lastUpdate}
    <span style="color: var(--text-dim);">Updated: {$lastUpdate.toLocaleTimeString()}</span>
  {/if}
  <button class="btn" style="padding: 4px 8px; font-size: 10px;" on:click={refresh}>Refresh</button>
</div>

<style>
  button { margin-left: auto; }
</style>