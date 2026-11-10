import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

const api = __ENV.QA_API_URL || 'http://127.0.0.1:5000/api';
const web = __ENV.QA_WEB_URL || 'http://127.0.0.1:4200';
for (const value of [api, web]) {
  if (!/^http:\/\/(127\.0\.0\.1|localhost|backend|frontend)(:\d+)?(\/|$)/.test(value)) throw new Error('k6 solo puede apuntar al entorno local o a servicios internos de QA');
}

const profile = __ENV.QA_LOAD_PROFILE || 'smoke';
const profiles = {
  smoke: { vus: 1, duration: '30s' },
  baseline: { vus: 3, duration: '2m' },
  moderate: { vus: 8, duration: '3m' },
  stress: {
    scenarios: {
      progressive_stress: {
        executor: 'ramping-vus', startVUs: 0,
        stages: [
          { duration: '1m', target: 100 },
          { duration: '1m', target: 300 },
          { duration: '1m', target: 600 },
          { duration: '1m', target: 0 },
        ],
        gracefulRampDown: '30s',
      },
    },
  },
  spike: {
    scenarios: {
      sudden_spike: {
        executor: 'ramping-vus', startVUs: 0,
        stages: [
          { duration: '10s', target: 1000 },
          { duration: '30s', target: 1000 },
          { duration: '10s', target: 0 },
        ],
        gracefulRampDown: '10s',
      },
    },
  },
  sustained: { vus: 100, duration: '10m' },
};
if (!profiles[profile]) throw new Error('Perfil desconocido');
export const options = {
  ...profiles[profile],
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
  thresholds: {
    api_latency: ['p(95)<2000'],
    page_latency: ['p(95)<3000'],
    api_errors: ['rate<0.05'],
    page_errors: ['rate<0.05'],
    request_errors: ['rate<0.05'],
  },
};
const apiLatency = new Trend('api_latency', true);
const pageLatency = new Trend('page_latency', true);
const apiErrors = new Rate('api_errors');
const pageErrors = new Rate('page_errors');
const errors = new Rate('request_errors');

export default function () {
  const products = http.get(`${api}/productos`, { tags: { case: 'TC-NF-REN-002' } });
  apiLatency.add(products.timings.duration);
  apiErrors.add(products.status !== 200);
  errors.add(products.status !== 200);
  check(products, { 'CNF-REN-02 API responde 200': r => r.status === 200 });

  const page = http.get(`${web}/productos`, { headers: { Accept: 'text/html' }, tags: { case: 'TC-NF-REN-001' } });
  if (__ENV.QA_DEBUG === '1' && __VU === 1 && __ITER === 0) console.log(`API HTTP ${products.status}; página HTTP ${page.status}`);
  pageLatency.add(page.timings.duration);
  pageErrors.add(page.status !== 200);
  errors.add(page.status !== 200);
  check(page, { 'CNF-REN-01 página responde 200': r => r.status === 200 });
  sleep(1);
}

export function handleSummary(data) {
  return { [__ENV.QA_K6_SUMMARY || 'artifacts/k6-summary.json']: JSON.stringify(data, null, 2) };
}
