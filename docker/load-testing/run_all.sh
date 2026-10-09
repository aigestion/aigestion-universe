#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K6_DIR="${SCRIPT_DIR}/k6"
REPORTS_DIR="${K6_DIR}/reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "${REPORTS_DIR}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

check_k6() {
    if ! command -v k6 &> /dev/null; then
        log_error "k6 not found. Install with: brew install k6 (macOS) or download from https://k6.io"
        return 1
    fi
    log_info "k6 version: $(k6 version)"
    return 0
}

check_services() {
    log_info "Checking service availability..."
    local services=(
        "epic_pc:5020"
        "daniela:9200"
        "hermes:9300"
        "optimization:9400"
        "frontend_v1:9500"
        "frontend_v2:9600"
        "infra_opt:9700"
        "agent_mobile:9800"
        "security:9999"
        "perf:9998"
        "dashboard:9997"
        "intel_engine:9850"
        "auto_engine:9860"
        "data_engine:9870"
        "secure_engine:9880"
        "devtools_engine:9890"
        "ecosystem_engine:9840"
        "ux_engine:9830"
        "scale_engine:9820"
    )
    
    local failed=0
    for svc in "${services[@]}"; do
        name="${svc%%:*}"
        port="${svc##*:}"
        if nc -z localhost "${port}" 2>/dev/null; then
            log_success "  ${name} (port ${port}) - UP"
        else
            log_warn "  ${name} (port ${port}) - DOWN"
            ((failed++))
        fi
    done
    
    if [[ ${failed} -gt 0 ]]; then
        log_warn "${failed} services are not reachable. Tests may fail."
        return 1
    fi
    return 0
}

run_k6_test() {
    local test_name="$1"
    local script="$2"
    local output_file="${REPORTS_DIR}/${test_name}-${TIMESTAMP}.json"
    local html_report="${REPORTS_DIR}/${test_name}-${TIMESTAMP}.html"
    
    log_info "Running ${test_name} test..."
    log_info "  Script: ${script}"
    log_info "  Output: ${output_file}"
    
    local start_time=$(date +%s)
    
    if k6 run \
        --out json="${output_file}" \
        --summary-export="${REPORTS_DIR}/${test_name}-summary-${TIMESTAMP}.json" \
        "${script}"; then
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_success "${test_name} completed in ${duration}s"
        
        if command -v k6-reporter &> /dev/null; then
            k6-reporter "${output_file}" --output "${html_report}" --title "aig ${test_name^} Test"
            log_info "HTML report: ${html_report}"
        fi
        
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_error "${test_name} failed after ${duration}s"
        return 1
    fi
}

generate_html_report() {
    local test_name="$1"
    local json_file="${REPORTS_DIR}/${test_name}-${TIMESTAMP}.json"
    local html_file="${REPORTS_DIR}/${test_name}-${TIMESTAMP}.html"
    
    if [[ -f "${json_file}" ]]; then
        cat > "${html_file}" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>aig ${test_name^} Test Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #1a1a2e; border-bottom: 3px solid #16213e; padding-bottom: 10px; }
        .metric { display: inline-block; background: #16213e; color: white; padding: 15px 25px; margin: 10px; border-radius: 6px; min-width: 180px; }
        .metric.pass { background: #27ae60; }
        .metric.fail { background: #e74c3c; }
        .metric.warn { background: #f39c12; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #1a1a2e; color: white; }
        tr:hover { background: #f8f9fa; }
        .chart-container { margin: 30px 0; height: 400px; }
        .engine-card { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 6px; border-left: 4px solid #16213e; }
        .engine-card.warning { border-left-color: #f39c12; }
        .engine-card.danger { border-left-color: #e74c3c; }
    </style>
</head>
<body>
    <div class="container">
        <h1>aig ${test_name^} Load Test Report</h1>
        <p>Generated: $(date)</p>
        <p>Test: ${test_name} | Duration: ${duration}s</p>
        <div id="summary"></div>
        <div class="chart-container">
            <canvas id="latencyChart"></canvas>
        </div>
        <h2>Engine Details</h2>
        <div id="engines"></div>
    </div>
    <script>
        fetch('${test_name}-${TIMESTAMP}.json')
            .then(r => r.json())
            .then(data => {
                document.getElementById('summary').innerHTML = \`
                    <div class="metric \${data.passed ? 'pass' : 'fail'}">Status: \${data.passed ? 'PASSED' : 'FAILED'}</div>
                    <div class="metric">Duration: \${data.duration}ms</div>
                    <div class="metric">P95 Latency: \${data.metrics.http_req_duration?.values?.['p(95)']?.toFixed(2) || 'N/A'}ms</div>
                    <div class="metric">Error Rate: \${(data.metrics.http_req_failed?.values?.rate * 100 || 0).toFixed(2)}%</div>
                \`;
                
                const enginesDiv = document.getElementById('engines');
                if (data.by_engine) {
                    for (const [engine, metrics] of Object.entries(data.by_engine)) {
                        const cardClass = metrics.error_rate > 0.05 ? 'danger' : (metrics.error_rate > 0.01 ? 'warning' : '');
                        enginesDiv.innerHTML += \`
                            <div class="engine-card \${cardClass}">
                                <h3>\${engine}</h3>
                                <p>P50: \${metrics.p50?.toFixed(2)}ms | P95: \${metrics.p95?.toFixed(2)}ms | P99: \${metrics.p99?.toFixed(2)}ms</p>
                                <p>Error Rate: \${(metrics.error_rate * 100).toFixed(2)}% | Requests: \${metrics.count}</p>
                            </div>
                        \`;
                    }
                }
            });
    </script>
</body>
</html>
EOF
        log_info "Basic HTML report generated: ${html_file}"
    fi
}

print_summary() {
    echo
    echo "=========================================="
    echo "  aig Load Test Suite Summary"
    echo "=========================================="
    echo "Timestamp: $(date)"
    echo "Reports: ${REPORTS_DIR}"
    echo
    for test in smoke load stress spike; do
        summary_file="${REPORTS_DIR}/${test}-summary-${TIMESTAMP}.json"
        if [[ -f "${summary_file}" ]]; then
            passed=$(jq -r '.passed // false' "${summary_file}" 2>/dev/null || echo "unknown")
            duration=$(jq -r '.duration // 0' "${summary_file}" 2>/dev/null || echo "0")
            p95=$(jq -r '.metrics.http_req_duration.values["p(95)"] // 0' "${summary_file}" 2>/dev/null || echo "0")
            error_rate=$(jq -r '.metrics.http_req_failed.values.rate // 0' "${summary_file}" 2>/dev/null || echo "0")
            
            status_icon="✓"
            [[ "${passed}" == "true" ]] && status_icon="✓" || status_icon="✗"
            
            printf "  %-10s %s  P95: %8.0fms  Errors: %5.2f%%  Duration: %ds\n" \
                "${test^}" "${status_icon}" "${p95}" "$(echo "${error_rate} * 100" | bc -l)" "${duration}"
        fi
    done
    echo "=========================================="
}

main() {
    local run_smoke=true
    local run_load=true
    local run_stress=true
    local run_spike=true
    local run_soak=false
    local skip_checks=false
    local only_test=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --smoke-only) only_test="smoke"; shift ;;
            --load-only) only_test="load"; shift ;;
            --stress-only) only_test="stress"; shift ;;
            --spike-only) only_test="spike"; shift ;;
            --soak) run_soak=true; shift ;;
            --skip-checks) skip_checks=true; shift ;;
            --no-smoke) run_smoke=false; shift ;;
            --no-load) run_load=false; shift ;;
            --no-stress) run_stress=false; shift ;;
            --no-spike) run_spike=false; shift ;;
            -h|--help)
                cat << EOF
Usage: $0 [options]

Options:
  --smoke-only      Run only smoke test
  --load-only       Run only load test
  --stress-only     Run only stress test
  --spike-only      Run only spike test
  --soak            Also run soak test (1 hour)
  --skip-checks     Skip service availability checks
  --no-smoke        Skip smoke test
  --no-load         Skip load test
  --no-stress       Skip stress test
  --no-spike        Skip spike test
  -h, --help        Show this help

Default: Runs smoke -> load -> stress -> spike in sequence
EOF
                exit 0
                ;;
            *) log_error "Unknown option: $1"; exit 1 ;;
        esac
    done
    
    log_info "aig Load Testing Suite"
    log_info "Timestamp: ${TIMESTAMP}"
    log_info "Reports directory: ${REPORTS_DIR}"
    
    if ! check_k6; then
        exit 1
    fi
    
    if [[ "${skip_checks}" != "true" ]]; then
        check_services || true
    fi
    
    local overall_status=0
    local tests_to_run=()
    
    if [[ -n "${only_test}" ]]; then
        tests_to_run=("${only_test}")
    else
        [[ "${run_smoke}" == "true" ]] && tests_to_run+=("smoke")
        [[ "${run_load}" == "true" ]] && tests_to_run+=("load")
        [[ "${run_stress}" == "true" ]] && tests_to_run+=("stress")
        [[ "${run_spike}" == "true" ]] && tests_to_run+=("spike")
        [[ "${run_soak}" == "true" ]] && tests_to_run+=("soak")
    fi
    
    for test in "${tests_to_run[@]}"; do
        case "${test}" in
            smoke)
                run_k6_test "smoke" "${K6_DIR}/smoke.js" || overall_status=1
                generate_html_report "smoke"
                ;;
            load)
                run_k6_test "load" "${K6_DIR}/load.js" || overall_status=1
                generate_html_report "load"
                ;;
            stress)
                run_k6_test "stress" "${K6_DIR}/stress.js" || overall_status=1
                generate_html_report "stress"
                ;;
            spike)
                run_k6_test "spike" "${K6_DIR}/spike.js" || overall_status=1
                generate_html_report "spike"
                ;;
            soak)
                log_warn "Soak test will run for 1 hour..."
                run_k6_test "soak" "${K6_DIR}/soak.js" || overall_status=1
                generate_html_report "soak"
                ;;
        esac
        
        if [[ ${overall_status} -ne 0 && "${test}" != "soak" ]]; then
            log_error "Test ${test} failed. Stopping suite."
            break
        fi
        
        sleep 5
    done
    
    print_summary
    
    if [[ ${overall_status} -eq 0 ]]; then
        log_success "All tests passed!"
    else
        log_error "Some tests failed."
    fi
    
    exit ${overall_status}
}

main "$@"