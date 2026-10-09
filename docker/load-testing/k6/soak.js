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

const errorRate = new Rate('errors');
const latencyTrend = new Trend('latency');
const requestCounter = new Counter('total_requests');
const connectionErrors = new Counter('connection_errors');
const timeoutErrors = new Counter('timeout_errors');
const driftGauge = new Gauge('performance_drift');
const memoryLeakGauge = new Gauge('memory_leak_indicator');
const connectionLeakGauge = new Gauge('connection_leak_indicator');

const weightedEngines = new SharedArray('weighted_engines', function () {
  const arr = [];
  for (const [engine, weight] of Object.entries(ENGINE_WEIGHTS)) {
    for (let i = 0; i < weight; i++) {
      arr.push(engine);
    }
  }
  return arr;
});

let intervalStart = Date.now();
let intervalRequestCount = 0;
let intervalErrorCount = 0;
let intervalLatencies = [];
let baselineLatency = null;
let driftHistory = [];
let leakCheckInterval = 0;

export const options = {
  scenarios: {
    soak_test: {
      executor: 'constant-vus',
      vus: 50,
      duration: '1h',
      gracefulStop: '2m',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<2000', 'p(99)<4000'],
    http_req_failed: ['rate<0.05'],
    errors: ['rate<0.05'],
    'performance_drift': ['value<2.0'],
  },
  noConnectionReuse: false,
  userAgent: 'aig-SoakTest/1.0',
  discardResponseBodies: true,
  summaryTrendStats: ['min', 'med', 'avg', 'p(90)', 'p(95)', 'p(99)', 'p(99.9)', 'max', 'count'],
};

function testEndpoint(engine, baseUrl, endpoint) {
  const url = `${baseUrl}${endpoint}`;
  const startTime = new Date();
  
  const res = http.get(url, {
    timeout: '30s',
    tags: { engine },
  });
  
  const latency = new Date() - startTime;
  latencyTrend.add(latency, { engine });
  requestCounter.add(1, { engine });
  intervalRequestCount++;
  intervalLatencies.push(latency);
  
  const success = check(res, {
    [`${engine}: status 200`]: (r) => r.status === 200,
    [`${engine}: response time < 5000ms`]: (r) => r.timings.duration < 5000,
  }, { engine });
  
  if (!success) {
    intervalErrorCount++;
    errorRate.add(true, { engine });
    
    if (res.error && res.error.includes('connection')) {
      connectionErrors.add(1, { engine });
    }
    if (res.error && res.error.includes('timeout')) {
      timeoutErrors.add(1, { engine });
    }
  } else {
    errorRate.add(false, { engine });
  }
  
  return { success, latency, status: res.status, error: res.error };
}

export function setup() {
  console.log('[SOAK SETUP] Establishing baseline...');
  const baselines = {};
  
  for (const [engine, baseUrl] of Object.entries(BASE_URLS)) {
    const endpoint = ENDPOINTS[engine];
    const url = `${baseUrl}${endpoint}`;
    
    let total = 0;
    let count = 0;
    for (let i = 0; i < 10; i++) {
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
  
  const avgBaseline = Object.values(baselines).reduce((a, b) => a + b, 0) / Object.keys(baselines).length;
  baselineLatency = avgBaseline;
  console.log(`[SOAK SETUP] Baseline latency: ${baselineLatency.toFixed(2)}ms`);
  
  return { baselineLatency: avgBaseline, baselines };
}

function checkDriftAndLeaks(data) {
  const now = Date.now();
  const intervalDuration = (now - intervalStart) / 1000 / 60;
  
  if (intervalDuration >= 5) {
    const avgLatency = intervalLatencies.reduce((a, b) => a + b, 0) / intervalLatencies.length;
    const errorRateVal = intervalRequestCount > 0 ? intervalErrorCount / intervalRequestCount : 0;
    
    if (baselineLatency && avgLatency > baselineLatency) {
      const drift = avgLatency / baselineLatency;
      driftGauge.add(drift);
      driftHistory.push({ time: now, drift, avgLatency, baselineLatency, errorRate: errorRateVal });
      
      if (drift > 1.5) {
        console.log(`[SOAK DRIFT] Performance drift detected: ${drift.toFixed(2)}x (avg: ${avgLatency.toFixed(0)}ms vs baseline: ${baselineLatency.toFixed(0)}ms)`);
      }
      
      if (driftHistory.length > 12) {
        const recent = driftHistory.slice(-12);
        const slope = (recent[recent.length - 1].drift - recent[0].drift) / recent.length;
        if (slope > 0.02) {
          memoryLeakGauge.add(slope * 100);
          console.log(`[SOAK LEAK WARNING] Potential memory leak: drift slope = ${slope.toFixed(4)} per interval`);
        }
      }
    }
    
    const connErrorRate = data.metrics.connection_errors?.values?.count / intervalRequestCount || 0;
    if (connErrorRate > 0.01) {
      connectionLeakGauge.add(connErrorRate * 100);
      console.log(`[SOAK LEAK WARNING] Connection leak indicator: ${(connErrorRate * 100).toFixed(2)}%`);
    }
    
    console.log(`[SOAK INTERVAL] ${intervalDuration.toFixed(0)}min: reqs=${intervalRequestCount}, errors=${intervalErrorCount}, avg_latency=${avgLatency.toFixed(0)}ms, drift=${baselineLatency ? (avgLatency/baselineLatency).toFixed(2) : 'N/A'}`);
    
    intervalStart = now;
    intervalRequestCount = 0;
    intervalErrorCount = 0;
    intervalLatencies = [];
    leakCheckInterval++;
  }
}

export default function (data) {
  if (data?.baselineLatency) {
    baselineLatency = data.baselineLatency;
  }
  
  const engine = weightedEngines[Math.floor(Math.random() * weightedEngines.length)];
  const baseUrl = BASE_URLS[engine];
  const endpoint = ENDPOINTS[engine];
  
  testEndpoint(engine, baseUrl, endpoint);
  
  checkDriftAndLeaks(data);
  
  sleep(Math.random() * 2 + 1);
}

export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    test: 'soak',
    duration_hours: 1,
    baseline_latency: baselineLatency,
    drift_history: driftHistory,
    leak_indicators: {
      memory_leak_slope: driftHistory.length > 1 ? 
        (driftHistory[driftHistory.length - 1].drift - driftHistory[0].drift) / driftHistory.length : 0,
      connection_error_trend: data.metrics.connection_errors?.values?.rate || 0,
      timeout_error_trend: data.metrics.timeout_errors?.values?.rate || 0,
    },
    metrics: {
      http_req_duration: data.metrics.http_req_duration?.values,
      http_req_failed: data.metrics.http_req_failed?.values,
      checks: data.metrics.checks?.values,
      connection_errors: data.metrics.connection_errors?.values,
      timeout_errors: data.metrics.timeout_errors?.values,
      performance_drift: data.metrics.performance_drift?.values,
      memory_leak_indicator: data.metrics.memory_leak_indicator?.values,
      connection_leak_indicator: data.metrics.connection_leak_indicator?.values,
    },
    by_engine: {},
    hourly_summary: {},
  };
  
  for (const [engine, baseUrl] of Object.entries(BASE_URLS)) {
    const tagData = data.metrics.http_req_duration?.valuesByTag?.['engine:' + engine];
    const errorData = data.metrics.http_req_failed?.valuesByTag?.['engine:' + engine];
    const connErrorData = data.metrics.connection_errors?.valuesByTag?.['engine:' + engine];
    const timeoutData = data.metrics.timeout_errors?.valuesByTag?.['engine:' + engine];
    
    if (tagData) {
      summary.by_engine[engine] = {
        p50: tagData['p(50)'],
        p90: tagData['p(90)'],
        p95: tagData['p(95)'],
        p99: tagData['p(99)'],
        max: tagData['max'],
        mean: tagData['mean'],
        count: tagData['count'],
        error_rate: errorData?.rate || 0,
        connection_error_rate: connErrorData?.rate || 0,
        timeout_error_rate: timeoutData?.rate || 0,
      };
    }
  }
  
  return {
    'stdout': JSON.stringify(summary, null, 2),
    'C:\\Users\\Alejandro\\aig\\load-testing\\k6\\reports\\soak-summary.json': JSON.stringify(summary, null, 2),
  };
}