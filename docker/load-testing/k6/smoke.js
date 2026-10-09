import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

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

const errorRate = new Rate('errors');
const latencyTrend = new Trend('latency');

export const options = {
  scenarios: {
    smoke: {
      executor: 'constant-vus',
      vus: 1,
      duration: '30s',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
    errors: ['rate<0.01'],
  },
  noConnectionReuse: false,
  userAgent: 'aig-SmokeTest/1.0',
};

function testEndpoint(engine, baseUrl, endpoint) {
  const url = `${baseUrl}${endpoint}`;
  const startTime = new Date();
  
  const res = http.get(url, {
    timeout: '10s',
    tags: { engine, endpoint },
  });
  
  const latency = new Date() - startTime;
  latencyTrend.add(latency);
  
  const success = check(res, {
    [`${engine}: status 200`]: (r) => r.status === 200,
    [`${engine}: response time < 500ms`]: (r) => r.timings.duration < 500,
    [`${engine}: has body`]: (r) => r.body && r.body.length > 0,
  });
  
  errorRate.add(!success);
  
  if (!success) {
    console.log(`[SMOKE FAIL] ${engine} (${url}): status=${res.status}, duration=${res.timings.duration}ms, error=${res.error}`);
  }
  
  return success;
}

export default function () {
  const results = [];
  
  for (const [engine, baseUrl] of Object.entries(BASE_URLS)) {
    const endpoint = ENDPOINTS[engine];
    const success = testEndpoint(engine, baseUrl, endpoint);
    results.push({ engine, success });
  }
  
  const failed = results.filter(r => !r.success).map(r => r.engine);
  if (failed.length > 0) {
    console.log(`[SMOKE SUMMARY] Failed engines: ${failed.join(', ')}`);
  } else {
    console.log('[SMOKE SUMMARY] All 19 engines responded successfully');
  }
  
  sleep(1);
}

export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    test: 'smoke',
    passed: data.metrics.http_req_failed?.values?.rate < 0.01,
    metrics: {
      http_req_duration: data.metrics.http_req_duration?.values,
      http_req_failed: data.metrics.http_req_failed?.values,
      checks: data.metrics.checks?.values,
    },
    engines: {},
  };
  
  for (const [engine, baseUrl] of Object.entries(BASE_URLS)) {
    const endpoint = ENDPOINTS[engine];
    const tagData = data.metrics.http_req_duration?.valuesByTag?.['engine:' + engine];
    if (tagData) {
      summary.engines[engine] = {
        p95: tagData['p(95)'],
        p99: tagData['p(99)'],
        mean: tagData['mean'],
        max: tagData['max'],
      };
    }
  }
  
  return {
    'stdout': JSON.stringify(summary, null, 2),
    'C:\\Users\\Alejandro\\aig\\load-testing\\k6\\reports\\smoke-summary.json': JSON.stringify(summary, null, 2),
  };
}