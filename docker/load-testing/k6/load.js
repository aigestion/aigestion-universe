import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
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

const ENGINE_CATEGORIES = {
  core: ['epic_pc', 'daniela', 'hermes', 'dashboard'],
  frontend: ['frontend_v1', 'frontend_v2'],
  ai: ['optimization', 'infra_opt', 'agent_mobile'],
  intel: ['intel_engine', 'auto_engine', 'data_engine', 'secure_engine'],
  devops: ['devtools_engine', 'ecosystem_engine', 'ux_engine', 'scale_engine'],
  cross: ['security', 'perf'],
};

const errorRate = new Rate('errors');
const latencyTrend = new Trend('latency');
const requestCounter = new Counter('total_requests');
const categoryLatency = new Trend('category_latency');

const weightedEngines = new SharedArray('weighted_engines', function () {
  const arr = [];
  for (const [engine, weight] of Object.entries(ENGINE_WEIGHTS)) {
    for (let i = 0; i < weight; i++) {
      arr.push(engine);
    }
  }
  return arr;
});

export const options = {
  scenarios: {
    load_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },
        { duration: '5m', target: 50 },
        { duration: '2m', target: 0 },
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<1000', 'p(99)<2000'],
    http_req_failed: ['rate<0.02'],
    errors: ['rate<0.02'],
    'checks{engine:epic_pc}': ['rate>0.98'],
    'checks{engine:daniela}': ['rate>0.98'],
    'checks{engine:hermes}': ['rate>0.98'],
  },
  noConnectionReuse: false,
  userAgent: 'aig-LoadTest/1.0',
  discardResponseBodies: false,
};

function getCategory(engine) {
  for (const [category, engines] of Object.entries(ENGINE_CATEGORIES)) {
    if (engines.includes(engine)) return category;
  }
  return 'unknown';
}

function testEndpoint(engine, baseUrl, endpoint) {
  const url = `${baseUrl}${endpoint}`;
  const startTime = new Date();
  const category = getCategory(engine);
  
  const res = http.get(url, {
    timeout: '15s',
    tags: { engine, category },
  });
  
  const latency = new Date() - startTime;
  latencyTrend.add(latency, { engine, category });
  categoryLatency.add(latency, { category });
  requestCounter.add(1, { engine, category });
  
  const success = check(res, {
    [`${engine}: status 200`]: (r) => r.status === 200,
    [`${engine}: response time < 1000ms`]: (r) => r.timings.duration < 1000,
    [`${engine}: has body`]: (r) => r.body && r.body.length > 0,
  }, { engine, category });
  
  errorRate.add(!success, { engine, category });
  
  if (!success) {
    console.log(`[LOAD FAIL] ${engine} (${category}): status=${res.status}, duration=${res.timings.duration}ms`);
  }
  
  return success;
}

export default function () {
  const engine = weightedEngines[Math.floor(Math.random() * weightedEngines.length)];
  const baseUrl = BASE_URLS[engine];
  const endpoint = ENDPOINTS[engine];
  
  testEndpoint(engine, baseUrl, endpoint);
  
  sleep(Math.random() * 2 + 0.5);
}

export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    test: 'load',
    passed: data.metrics.http_req_failed?.values?.rate < 0.02,
    duration: data.state?.testRunDurationMs,
    metrics: {
      http_req_duration: data.metrics.http_req_duration?.values,
      http_req_failed: data.metrics.http_req_failed?.values,
      checks: data.metrics.checks?.values,
      vus: data.metrics.vus?.values,
      vus_max: data.metrics.vus_max?.values,
    },
    by_engine: {},
    by_category: {},
  };
  
  for (const [engine, baseUrl] of Object.entries(BASE_URLS)) {
    const tagData = data.metrics.http_req_duration?.valuesByTag?.['engine:' + engine];
    if (tagData) {
      summary.by_engine[engine] = {
        p50: tagData['p(50)'],
        p90: tagData['p(90)'],
        p95: tagData['p(95)'],
        p99: tagData['p(99)'],
        mean: tagData['mean'],
        max: tagData['max'],
        count: tagData['count'],
        error_rate: data.metrics.http_req_failed?.valuesByTag?.['engine:' + engine]?.rate || 0,
      };
    }
  }
  
  for (const category of Object.keys(ENGINE_CATEGORIES)) {
    const tagData = data.metrics.category_latency?.valuesByTag?.['category:' + category];
    if (tagData) {
      summary.by_category[category] = {
        p50: tagData['p(50)'],
        p90: tagData['p(90)'],
        p95: tagData['p(95)'],
        p99: tagData['p(99)'],
        mean: tagData['mean'],
        count: tagData['count'],
      };
    }
  }
  
  return {
    'stdout': JSON.stringify(summary, null, 2),
    'C:\\Users\\Alejandro\\aig\\load-testing\\k6\\reports\\load-summary.json': JSON.stringify(summary, null, 2),
  };
}