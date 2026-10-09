import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter, Gauge } from 'k6/metrics';
import { SharedArray } from 'k6/data';

const BASE_URLS = {
  epic_pc: 'http://localhost:5020',
  daniela: 'http://localhost:9200',
  hermes: 'http://localhost:9300',
  optimization: 'http://localhost:9400',
  frontend_v1: 'http://localhost:9500',
  frontend_v2: 'http://localhost:9600',
  infra_opt: 'http://localhost:9700',
  agent_mobile: 'http://localhost:9800',
  security: 'http://localhost:9999',
  perf: 'http://localhost:9998',
  dashboard: 'http://localhost:9997',
  intel_engine: 'http://localhost:9850',
  auto_engine: 'http://localhost:9860',
  data_engine: 'http://localhost:9870',
  secure_engine: 'http://localhost:9880',
  devtools_engine: 'http://localhost:9890',
  ecosystem_engine: 'http://localhost:9840',
  ux_engine: 'http://localhost:9830',
  scale_engine: 'http://localhost:9820',
};

const ENDPOINTS = {
  epic_pc: '/api/status',
  daniela: '/api/status',
  hermes: '/api/status',
  optimization: '/api/opt/status',
  frontend_v1: '/api/frontend/status',
  frontend_v2: '/api/frontend2/status',
  infra_opt: '/api/infra/status',
  agent_mobile: '/api/agent/status',
  security: '/api/secure/status',
  perf: '/api/perf/status',
  dashboard: '/api/status',
  intel_engine: '/api/intel/status',
  auto_engine: '/api/auto/status',
  data_engine: '/api/data/status',
  secure_engine: '/api/secure_engine/status',
  devtools_engine: '/api/devtools/status',
  ecosystem_engine: '/api/ecosystem/status',
  ux_engine: '/api/ux/status',
  scale_engine: '/api/scale/status',
};

const ENGINE_WEIGHTS = {
  epic_pc: 10,
  daniela: 8,
  hermes: 8,
  optimization: 6,
  frontend_v1: 7,
  frontend_v2: 7,
  infra_opt: 5,
  agent_mobile: 5,
  security: 4,
  perf: 4,
  dashboard: 6,
  intel_engine: 6,
  auto_engine: 5,
  data_engine: 5,
  secure_engine: 4,
  devtools_engine: 3,
  ecosystem_engine: 3,
  ux_engine: 4,
  scale_engine: 3,
};

const CRITICAL_ENGINES = ['epic_pc', 'daniela', 'hermes', 'dashboard', 'security', 'perf'];

const errorRate = new Rate('errors');
const latencyTrend = new Trend('latency');
const requestCounter = new Counter('total_requests');
const spikeLatencyGauge = new Gauge('spike_latency');
const recoveryGauge = new Gauge('recovery_time');
const circuitBreakerGauge = new Gauge('circuit_breaker_triggered');
const autoscalingGauge = new Gauge('autoscaling_triggered');

const weightedEngines = new SharedArray('weighted_engines', function () {
  const arr = [];
  for (const [engine, weight] of Object.entries(ENGINE_WEIGHTS)) {
    for (let i = 0; i < weight; i++) {
      arr.push(engine);
    }
  }
  return arr;
});

let baselineLatencies = {};
let spikeStartTime = null;
let spikeEndTime = null;
let inSpike = false;
let recoveryStartTime = null;
let recoveryMeasured = false;

export const options = {
  scenarios: {
    spike_test: {
      executor: 'ramping-vus',
      startVUs: 10,
      stages: [
        { duration: '30s', target: 10 },
        { duration: '10s', target: 100 },
        { duration: '1m', target: 100 },
        { duration: '10s', target: 10 },
        { duration: '2m', target: 10 },
        { duration: '10s', target: 100 },
        { duration: '30s', target: 100 },
        { duration: '10s', target: 10 },
        { duration: '2m', target: 10 },
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<5000', 'p(99)<10000'],
    http_req_failed: ['rate<0.15'],
    errors: ['rate<0.15'],
    'checks{engine:epic_pc}': ['rate>0.85'],
    'checks{engine:security}': ['rate>0.85'],
  },
  noConnectionReuse: false,
  userAgent: 'aig-SpikeTest/1.0',
  discardResponseBodies: true,
  summaryTrendStats: ['min', 'med', 'avg', 'p(90)', 'p(95)', 'p(99)', 'p(99.9)', 'max'],
};

function testEndpoint(engine, baseUrl, endpoint, currentVUs) {
  const url = `${baseUrl}${endpoint}`;
  const startTime = new Date();
  
  const res = http.get(url, {
    timeout: '20s',
    tags: { engine, vu_count: currentVUs.toString(), critical: CRITICAL_ENGINES.includes(engine).toString() },
  });
  
  const latency = new Date() - startTime;
  latencyTrend.add(latency, { engine });
  requestCounter.add(1, { engine });
  
  const success = check(res, {
    [`${engine}: status 200`]: (r) => r.status === 200,
    [`${engine}: response time < 10000ms`]: (r) => r.timings.duration < 10000,
  }, { engine, critical: CRITICAL_ENGINES.includes(engine) });
  
  errorRate.add(!success, { engine });
  
  if (inSpike && currentVUs >= 100) {
    spikeLatencyGauge.add(latency, { engine });
    
    if (baselineLatencies[engine] && latency > baselineLatencies[engine] * 10) {
      circuitBreakerGauge.add(1, { engine });
      console.log(`[CIRCUIT BREAKER] ${engine}: latency ${latency}ms > 10x baseline ${baselineLatencies[engine]}ms`);
    }
  }
  
  if (!inSpike && currentVUs <= 10 && !recoveryMeasured && recoveryStartTime) {
    const recoveryTime = Date.now() - recoveryStartTime;
    recoveryGauge.add(recoveryTime, { engine });
    console.log(`[RECOVERY] ${engine}: recovered in ${recoveryTime}ms after spike`);
    recoveryMeasured = true;
  }
  
  return { success, latency, status: res.status };
}

export function setup() {
  console.log('[SPIKE SETUP] Establishing baseline latencies...');
  const baselines = {};
  
  for (const [engine, baseUrl] of Object.entries(BASE_URLS)) {
    const endpoint = ENDPOINTS[engine];
    const url = `${baseUrl}${endpoint}`;
    
    let total = 0;
    let count = 0;
    for (let i = 0; i < 5; i++) {
      const res = http.get(url, { timeout: '10s' });
      if (res.status === 200) {
        total += res.timings.duration;
        count++;
      }
      sleep(0.1);
    }
    if (count > 0) {
      baselines[engine] = total / count;
    }
  }
  
  console.log('[SPIKE SETUP] Baselines established:', JSON.stringify(baselines));
  return { baselines };
}

export default function (data) {
  if (data?.baselines) {
    baselineLatencies = data.baselines;
  }
  
  const currentVUs = __VU;
  const engine = weightedEngines[Math.floor(Math.random() * weightedEngines.length)];
  const baseUrl = BASE_URLS[engine];
  const endpoint = ENDPOINTS[engine];
  
  const prevInSpike = inSpike;
  inSpike = currentVUs >= 50;
  
  if (!prevInSpike && inSpike && spikeStartTime === null) {
    spikeStartTime = Date.now();
    console.log('[SPIKE] Spike phase STARTED');
    autoscalingGauge.add(1);
  }
  
  if (prevInSpike && !inSpike && spikeEndTime === null) {
    spikeEndTime = Date.now();
    recoveryStartTime = Date.now();
    recoveryMeasured = false;
    console.log('[SPIKE] Spike phase ENDED, recovery phase STARTED');
  }
  
  testEndpoint(engine, baseUrl, endpoint, currentVUs);
  
  sleep(Math.random() * 0.5 + 0.1);
}

export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    test: 'spike',
    spike_phases: 2,
    baseline_latencies: baselineLatencies,
    spike_start_time: spikeStartTime,
    spike_end_time: spikeEndTime,
    recovery_time_ms: recoveryStartTime ? Date.now() - recoveryStartTime : null,
    metrics: {
      http_req_duration: data.metrics.http_req_duration?.values,
      http_req_failed: data.metrics.http_req_failed?.values,
      checks: data.metrics.checks?.values,
      vus: data.metrics.vus?.values,
      vus_max: data.metrics.vus_max?.values,
      spike_latency: data.metrics.spike_latency?.values,
      recovery_time: data.metrics.recovery_time?.values,
      circuit_breaker_triggered: data.metrics.circuit_breaker_triggered?.values,
      autoscaling_triggered: data.metrics.autoscaling_triggered?.values,
    },
    by_engine: {},
    critical_engines: {},
    spike_analysis: {},
  };
  
  for (const [engine, baseUrl] of Object.entries(BASE_URLS)) {
    const tagData = data.metrics.http_req_duration?.valuesByTag?.['engine:' + engine];
    const errorData = data.metrics.http_req_failed?.valuesByTag?.['engine:' + engine];
    const spikeData = data.metrics.spike_latency?.valuesByTag?.['engine:' + engine];
    const cbData = data.metrics.circuit_breaker_triggered?.valuesByTag?.['engine:' + engine];
    const recData = data.metrics.recovery_time?.valuesByTag?.['engine:' + engine];
    
    if (tagData) {
      const engineSummary = {
        p50: tagData['p(50)'],
        p90: tagData['p(90)'],
        p95: tagData['p(95)'],
        p99: tagData['p(99)'],
        max: tagData['max'],
        mean: tagData['mean'],
        count: tagData['count'],
        error_rate: errorData?.rate || 0,
        baseline: baselineLatencies[engine] || 0,
        spike_p95: spikeData?.['p(95)'] || 0,
        circuit_breaker_triggered: (cbData?.count || 0) > 0,
        recovery_time: recData?.mean || 0,
      };
      
      summary.by_engine[engine] = engineSummary;
      
      if (CRITICAL_ENGINES.includes(engine)) {
        summary.critical_engines[engine] = engineSummary;
      }
    }
  }
  
  const vuTags = Object.keys(data.metrics.http_req_duration?.valuesByTag || {}).filter(t => t.startsWith('vu_count:'));
  const spikeAnalysis = [];
  
  for (const tag of vuTags) {
    const vuCount = parseInt(tag.split(':')[1]);
    const values = data.metrics.http_req_duration?.valuesByTag?.[tag];
    const errors = data.metrics.http_req_failed?.valuesByTag?.[tag];
    
    if (values && vuCount >= 50) {
      spikeAnalysis.push({
        vus: vuCount,
        p95: values['p(95)'],
        p99: values['p(99)'],
        mean: values['mean'],
        error_rate: errors?.rate || 0,
      });
    }
  }
  
  summary.spike_analysis = spikeAnalysis.sort((a, b) => a.vus - b.vus);
  
  return {
    'stdout': JSON.stringify(summary, null, 2),
    'C:\\Users\\Alejandro\\aig\\load-testing\\k6\\reports\\spike-summary.json': JSON.stringify(summary, null, 2),
  };
}