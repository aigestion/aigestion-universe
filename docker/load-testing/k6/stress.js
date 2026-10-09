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
const vusGauge = new Gauge('current_vus');
const degradationGauge = new Gauge('degradation_factor');
const breakingPointGauge = new Gauge('breaking_point_reached');

const weightedEngines = new SharedArray('weighted_engines', function () {
  const arr = [];
  for (const [engine, weight] of Object.entries(ENGINE_WEIGHTS)) {
    for (let i = 0; i < weight; i++) {
      arr.push(engine);
    }
  }
  return arr;
});

let baselineLatency = null;
let degradationDetected = false;

export const options = {
  scenarios: {
    stress_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 10 },
        { duration: '2m', target: 50 },
        { duration: '2m', target: 100 },
        { duration: '2m', target: 150 },
        { duration: '3m', target: 200 },
        { duration: '2m', target: 200 },
        { duration: '3m', target: 0 },
      ],
      gracefulRampDown: '1m',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<3000', 'p(99)<5000'],
    http_req_failed: ['rate<0.10'],
    errors: ['rate<0.10'],
  },
  noConnectionReuse: false,
  userAgent: 'aig-StressTest/1.0',
  discardResponseBodies: true,
  summaryTrendStats: ['min', 'med', 'avg', 'p(90)', 'p(95)', 'p(99)', 'p(99.9)', 'max'],
};

function testEndpoint(engine, baseUrl, endpoint, currentVUs) {
  const url = `${baseUrl}${endpoint}`;
  const startTime = new Date();
  
  const res = http.get(url, {
    timeout: '30s',
    tags: { engine, vu_count: currentVUs.toString() },
  });
  
  const latency = new Date() - startTime;
  latencyTrend.add(latency, { engine });
  requestCounter.add(1, { engine });
  vusGauge.add(currentVUs);
  
  const success = check(res, {
    [`${engine}: status 200`]: (r) => r.status === 200,
    [`${engine}: response time < 5000ms`]: (r) => r.timings.duration < 5000,
  }, { engine });
  
  errorRate.add(!success, { engine });
  
  if (baselineLatency && currentVUs >= 50) {
    const degradation = latency / baselineLatency;
    degradationGauge.add(degradation, { engine });
    
    if (degradation > 5 && !degradationDetected) {
      degradationDetected = true;
      breakingPointGauge.add(1, { engine });
      console.log(`[BREAKING POINT] ${engine}: ${degradation.toFixed(2)}x degradation at ${currentVUs} VUs`);
    }
  }
  
  return { success, latency, status: res.status };
}

export function setup() {
  console.log('[STRESS SETUP] Establishing baseline latency...');
  const baselines = {};
  
  for (const [engine, baseUrl] of Object.entries(BASE_URLS)) {
    const endpoint = ENDPOINTS[engine];
    const url = `${baseUrl}${endpoint}`;
    
    const res = http.get(url, { timeout: '10s' });
    if (res.status === 200) {
      baselines[engine] = res.timings.duration;
    }
  }
  
  const avgBaseline = Object.values(baselines).reduce((a, b) => a + b, 0) / Object.keys(baselines).length;
  baselineLatency = avgBaseline;
  console.log(`[STRESS SETUP] Baseline latency: ${baselineLatency.toFixed(2)}ms`);
  
  return { baselineLatency: avgBaseline };
}

export default function (data) {
  if (data?.baselineLatency) {
    baselineLatency = data.baselineLatency;
  }
  
  const currentVUs = __VU;
  const engine = weightedEngines[Math.floor(Math.random() * weightedEngines.length)];
  const baseUrl = BASE_URLS[engine];
  const endpoint = ENDPOINTS[engine];
  
  testEndpoint(engine, baseUrl, endpoint, currentVUs);
  
  sleep(Math.random() * 1 + 0.2);
}

export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    test: 'stress',
    baseline_latency: baselineLatency,
    breaking_points: {},
    degradation_analysis: {},
    metrics: {
      http_req_duration: data.metrics.http_req_duration?.values,
      http_req_failed: data.metrics.http_req_failed?.values,
      checks: data.metrics.checks?.values,
      vus: data.metrics.vus?.values,
      vus_max: data.metrics.vus_max?.values,
      degradation_factor: data.metrics.degradation_factor?.values,
      breaking_point_reached: data.metrics.breaking_point_reached?.values,
    },
    by_engine: {},
    stages: [],
  };
  
  for (const [engine, baseUrl] of Object.entries(BASE_URLS)) {
    const tagData = data.metrics.http_req_duration?.valuesByTag?.['engine:' + engine];
    const errorData = data.metrics.http_req_failed?.valuesByTag?.['engine:' + engine];
    const degData = data.metrics.degradation_factor?.valuesByTag?.['engine:' + engine];
    const bpData = data.metrics.breaking_point_reached?.valuesByTag?.['engine:' + engine];
    
    if (tagData) {
      summary.by_engine[engine] = {
        p50: tagData['p(50)'],
        p90: tagData['p(90)'],
        p95: tagData['p(95)'],
        p99: tagData['p(99)'],
        p999: tagData['p(99.9)'],
        max: tagData['max'],
        mean: tagData['mean'],
        count: tagData['count'],
        error_rate: errorData?.rate || 0,
        avg_degradation: degData?.mean || 1,
        breaking_point: bpData?.count > 0,
      };
      
      if (bpData?.count > 0) {
        summary.breaking_points[engine] = true;
      }
    }
  }
  
  const stageMetrics = data.metrics.http_req_duration?.valuesByTag;
  if (stageMetrics) {
    for (const [tag, values] of Object.entries(stageMetrics)) {
      if (tag.startsWith('vu_count:')) {
        const vuCount = tag.split(':')[1];
        summary.stages.push({
          vus: parseInt(vuCount),
          p95: values['p(95)'],
          p99: values['p(99)'],
          mean: values['mean'],
          error_rate: data.metrics.http_req_failed?.valuesByTag?.[tag]?.rate || 0,
        });
      }
    }
    summary.stages.sort((a, b) => a.vus - b.vus);
  }
  
  return {
    'stdout': JSON.stringify(summary, null, 2),
    'C:\\Users\\Alejandro\\aig\\load-testing\\k6\\reports\\stress-summary.json': JSON.stringify(summary, null, 2),
  };
}