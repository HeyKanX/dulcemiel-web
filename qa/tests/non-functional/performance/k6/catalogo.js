import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

const api = __ENV.QA_API_URL || 'http://127.0.0.1:5000/api';
const web = __ENV.QA_WEB_URL || 'http://127.0.0.1:4200';
for (const value of [api, web]) {
  if (!/^https?:\/\/(127\.0\.0\.1|localhost)(:\d+)?(\/|$)/.test(value)) throw new Error('k6 solo puede apuntar al entorno local');
}

const profile = __ENV.QA_LOAD_PROFILE || 'smoke';
const profiles = {
  smoke: { vus: 1000, duration: '30s' }, // 1000 usuarios virtuales durante 30 segundos.
  baseline: { vus: 500, duration: '2m' }, // 500 usuarios virtuales durante 2 minutos.
  moderate: { vus: 100, duration: '3m' }, // 100 usuarios virtuales durante 3 minutos.
};
if (!profiles[profile]) throw new Error('Perfil desconocido');
export const options = {
  ...profiles[profile],
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
  thresholds: {
    api_latency: ['p(95)<2000'],
    page_latency: ['p(95)<3000'],
    request_errors: ['rate<0.05'],
  },
};
const apiLatency = new Trend('api_latency', true);
const pageLatency = new Trend('page_latency', true);
const errors = new Rate('request_errors');

export default function () {
  const products = http.get(`${api}/productos`, { tags: { case: 'TC-NF-REN-002' } });
  apiLatency.add(products.timings.duration);
  errors.add(products.status !== 200);
  check(products, { 'TC-NF-REN-002 API responde 200': r => r.status === 200 });

  const page = http.get(`${web}/productos`, { headers: { Accept: 'text/html' }, tags: { case: 'TC-NF-REN-001' } });
  if (__ENV.QA_DEBUG === '1' && __VU === 1 && __ITER === 0) console.log(`API HTTP ${products.status}; página HTTP ${page.status}`);
  pageLatency.add(page.timings.duration);
  errors.add(page.status !== 200);
  check(page, { 'TC-NF-REN-001 página responde 200': r => r.status === 200 });
  sleep(1);
}

export function handleSummary(data) {
  const format = value => Number.isFinite(value) ? value.toFixed(2) : 'N/D';
  const api = data.metrics.api_latency?.values || {};
  const page = data.metrics.page_latency?.values || {};
  const errors = data.metrics.request_errors?.values || {};
  const checks = data.metrics.checks?.values || {};
  const lines = [
    '\nResumen de rendimiento k6',
    `Solicitudes: ${data.metrics.http_reqs?.values?.count ?? 0}`,
    `API (ms): promedio ${format(api.avg)} | p95 ${format(api['p(95)'])} | máximo ${format(api.max)}`,
    `Página (ms): promedio ${format(page.avg)} | p95 ${format(page['p(95)'])} | máximo ${format(page.max)}`,
    `Errores de solicitud: ${format((errors.rate ?? 0) * 100)} %`,
    `Aserciones aprobadas: ${checks.passes ?? 0}/${(checks.passes ?? 0) + (checks.fails ?? 0)}`,
  ];
  const outputs = { stdout: `${lines.join('\n')}\n` };
  if (__ENV.QA_K6_SUMMARY) outputs[__ENV.QA_K6_SUMMARY] = JSON.stringify(data, null, 2);
  return outputs;
}
