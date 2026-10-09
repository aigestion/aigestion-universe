import random

from locust import HttpUser, LoadTestShape, between, events, task

ENGINES = {
    "core": {
        "epic_pc": {"host": "http://localhost:5020", "endpoint": "/api/status", "weight": 10},
        "daniela": {"host": "http://localhost:9200", "endpoint": "/api/status", "weight": 8},
        "hermes": {"host": "http://localhost:9300", "endpoint": "/api/status", "weight": 8},
        "dashboard": {"host": "http://localhost:9997", "endpoint": "/api/status", "weight": 6},
    },
    "frontend": {
        "frontend_v1": {"host": "http://localhost:9500", "endpoint": "/api/frontend/status", "weight": 7},
        "frontend_v2": {"host": "http://localhost:9600", "endpoint": "/api/frontend2/status", "weight": 7},
    },
    "ai": {
        "optimization": {"host": "http://localhost:9400", "endpoint": "/api/opt/status", "weight": 6},
        "infra_opt": {"host": "http://localhost:9700", "endpoint": "/api/infra/status", "weight": 5},
        "agent_mobile": {"host": "http://localhost:9800", "endpoint": "/api/agent/status", "weight": 5},
    },
    "intel": {
        "intel_engine": {"host": "http://localhost:9850", "endpoint": "/api/intel/status", "weight": 6},
        "auto_engine": {"host": "http://localhost:9860", "endpoint": "/api/auto/status", "weight": 5},
        "data_engine": {"host": "http://localhost:9870", "endpoint": "/api/data/status", "weight": 5},
        "secure_engine": {"host": "http://localhost:9880", "endpoint": "/api/secure_engine/status", "weight": 4},
    },
    "devops": {
        "devtools_engine": {"host": "http://localhost:9890", "endpoint": "/api/devtools/status", "weight": 3},
        "ecosystem_engine": {"host": "http://localhost:9840", "endpoint": "/api/ecosystem/status", "weight": 3},
        "ux_engine": {"host": "http://localhost:9830", "endpoint": "/api/ux/status", "weight": 4},
        "scale_engine": {"host": "http://localhost:9820", "endpoint": "/api/scale/status", "weight": 3},
    },
    "cross": {
        "security": {"host": "http://localhost:9999", "endpoint": "/api/secure/status", "weight": 4},
        "perf": {"host": "http://localhost:9998", "endpoint": "/api/perf/status", "weight": 4},
    },
}

ALL_ENGINES = {}
for category, engines in ENGINES.items():
    for name, config in engines.items():
        ALL_ENGINES[name] = {**config, "category": category}

CRITICAL_ENGINES = ["epic_pc", "daniela", "hermes", "dashboard", "security", "perf"]


class EngineUser(HttpUser):
    abstract = True
    wait_time = between(0.5, 2.0)
    host = "http://localhost:5020"

    def on_start(self):
        self.engine_name = self.__class__.__name__.replace("User", "").lower()
        self.engine_config = ALL_ENGINES.get(self.engine_name, {})
        self.host = self.engine_config.get("host", "http://localhost:5020")
        self.endpoint = self.engine_config.get("endpoint", "/api/status")
        self.category = self.engine_config.get("category", "unknown")
        self.weight = self.engine_config.get("weight", 1)

    def make_request(self, name=None):
        request_name = name or f"{self.engine_name}_status"
        with self.client.get(
            self.endpoint,
            name=request_name,
            catch_response=True,
            timeout=15,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")


class CoreEngineUser(EngineUser):
    weight = 35

    @task(10)
    def epic_pc_status(self):
        self.engine_name = "epic_pc"
        self.engine_config = ALL_ENGINES["epic_pc"]
        self.host = self.engine_config["host"]
        self.endpoint = self.engine_config["endpoint"]
        self.make_request()

    @task(8)
    def daniela_status(self):
        self.engine_name = "daniela"
        self.engine_config = ALL_ENGINES["daniela"]
        self.host = self.engine_config["host"]
        self.endpoint = self.engine_config["endpoint"]
        self.make_request()

    @task(8)
    def hermes_status(self):
        self.engine_name = "hermes"
        self.engine_config = ALL_ENGINES["hermes"]
        self.host = self.engine_config["host"]
        self.endpoint = self.engine_config["endpoint"]
        self.make_request()

    @task(6)
    def dashboard_status(self):
        self.engine_name = "dashboard"
        self.engine_config = ALL_ENGINES["dashboard"]
        self.host = self.engine_config["host"]
        self.endpoint = self.engine_config["endpoint"]
        self.make_request()


class FrontendEngineUser(EngineUser):
    weight = 15

    @task(7)
    def frontend_v1_status(self):
        self.engine_name = "frontend_v1"
        self.engine_config = ALL_ENGINES["frontend_v1"]
        self.host = self.engine_config["host"]
        self.endpoint = self.engine_config["endpoint"]
        self.make_request()

    @task(7)
    def frontend_v2_status(self):
        self.engine_name = "frontend_v2"
        self.engine_config = ALL_ENGINES["frontend_v2"]
        self.host = self.engine_config["host"]
        self.endpoint = self.engine_config["endpoint"]
        self.make_request()


class AIEngineUser(EngineUser):
    weight = 15

    @task(6)
    def optimization_status(self):
        self.engine_name = "optimization"
        self.engine_config = ALL_ENGINES["optimization"]
        self.host = self.engine_config["host"]
        self.endpoint = self.engine_config["endpoint"]
        self.make_request()

    @task(5)
    def infra_opt_status(self):
        self.engine_name = "infra_opt"
        self.engine_config = ALL_ENGINES["infra_opt"]
        self.host = self.engine_config["host"]
        self.endpoint = self.engine_config["endpoint"]
        self.make_request()

    @task(5)
    def agent_mobile_status(self):
        self.engine_name = "agent_mobile"
        self.engine_config = ALL_ENGINES["agent_mobile"]
        self.host = self.engine_config["host"]
        self.endpoint = self.engine_config["endpoint"]
        self.make_request()


class IntelEngineUser(EngineUser):
    weight = 20

    @task(6)
    def intel_engine_status(self):
        self.engine_name = "intel_engine"
        self.engine_config = ALL_ENGINES["intel_engine"]
        self.host = self.engine_config["host"]
        self.endpoint = self.engine_config["endpoint"]
        self.make_request()

    @task(5)
    def auto_engine_status(self):
        self.engine_name = "auto_engine"
        self.engine_config = ALL_ENGINES["auto_engine"]
        self.host = self.engine_config["host"]
        self.endpoint = self.engine_config["endpoint"]
        self.make_request()

    @task(5)
    def data_engine_status(self):
        self.engine_name = "data_engine"
        self.engine_config = ALL_ENGINES["data_engine"]
        self.host = self.engine_config["host"]
        self.endpoint = self.engine_config["endpoint"]
        self.make_request()

    @task(4)
    def secure_engine_status(self):
        self.engine_name = "secure_engine"
        self.engine_config = ALL_ENGINES["secure_engine"]
        self.host = self.engine_config["host"]
        self.endpoint = self.engine_config["endpoint"]
        self.make_request()


class DevOpsEngineUser(EngineUser):
    weight = 10

    @task(3)
    def devtools_engine_status(self):
        self.engine_name = "devtools_engine"
        self.engine_config = ALL_ENGINES["devtools_engine"]
        self.host = self.engine_config["host"]
        self.endpoint = self.engine_config["endpoint"]
        self.make_request()

    @task(3)
    def ecosystem_engine_status(self):
        self.engine_name = "ecosystem_engine"
        self.engine_config = ALL_ENGINES["ecosystem_engine"]
        self.host = self.engine_config["host"]
        self.endpoint = self.engine_config["endpoint"]
        self.make_request()

    @task(4)
    def ux_engine_status(self):
        self.engine_name = "ux_engine"
        self.engine_config = ALL_ENGINES["ux_engine"]
        self.host = self.engine_config["host"]
        self.endpoint = self.engine_config["endpoint"]
        self.make_request()

    @task(3)
    def scale_engine_status(self):
        self.engine_name = "scale_engine"
        self.engine_config = ALL_ENGINES["scale_engine"]
        self.host = self.engine_config["host"]
        self.endpoint = self.engine_config["endpoint"]
        self.make_request()


class CrossCuttingUser(EngineUser):
    weight = 5

    @task(4)
    def security_status(self):
        self.engine_name = "security"
        self.engine_config = ALL_ENGINES["security"]
        self.host = self.engine_config["host"]
        self.endpoint = self.engine_config["endpoint"]
        self.make_request()

    @task(4)
    def perf_status(self):
        self.engine_name = "perf"
        self.engine_config = ALL_ENGINES["perf"]
        self.host = self.engine_config["host"]
        self.endpoint = self.engine_config["endpoint"]
        self.make_request()


class MixedEngineUser(EngineUser):
    weight = 1
    wait_time = between(0.2, 1.0)

    def on_start(self):
        pass

    @task
    def random_engine_status(self):
        engine_name = random.choices(
            list(ALL_ENGINES.keys()),
            weights=[ALL_ENGINES[e]["weight"] for e in ALL_ENGINES.keys()],
            k=1
        )[0]

        self.engine_name = engine_name
        self.engine_config = ALL_ENGINES[engine_name]
        self.host = self.engine_config["host"]
        self.endpoint = self.engine_config["endpoint"]
        self.category = self.engine_config["category"]

        self.make_request(f"{engine_name}_status")


class SpikeUser(HttpUser):
    wait_time = between(0.05, 0.2)
    weight = 0

    def on_start(self):
        self.spike_mode = False

    @task
    def spike_request(self):
        engine_name = random.choices(
            list(ALL_ENGINES.keys()),
            weights=[ALL_ENGINES[e]["weight"] for e in ALL_ENGINES.keys()],
            k=1
        )[0]

        engine_config = ALL_ENGINES[engine_name]
        with self.client.get(
            engine_config["endpoint"],
            base_url=engine_config["host"],
            name=f"spike_{engine_name}",
            catch_response=True,
            timeout=10,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")


class StagesShape(LoadTestShape):
    stages = [
        {"duration": 60, "users": 10, "spawn_rate": 2},
        {"duration": 120, "users": 50, "spawn_rate": 5},
        {"duration": 300, "users": 50, "spawn_rate": 0},
        {"duration": 120, "users": 100, "spawn_rate": 10},
        {"duration": 60, "users": 100, "spawn_rate": 0},
        {"duration": 120, "users": 10, "spawn_rate": -10},
    ]

    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        return None


class SpikeShape(LoadTestShape):
    stages = [
        {"duration": 30, "users": 10, "spawn_rate": 2},
        {"duration": 10, "users": 100, "spawn_rate": 20},
        {"duration": 60, "users": 100, "spawn_rate": 0},
        {"duration": 10, "users": 10, "spawn_rate": -20},
        {"duration": 120, "users": 10, "spawn_rate": 0},
        {"duration": 10, "users": 100, "spawn_rate": 20},
        {"duration": 30, "users": 100, "spawn_rate": 0},
        {"duration": 10, "users": 10, "spawn_rate": -20},
        {"duration": 120, "users": 10, "spawn_rate": 0},
    ]

    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        return None


class SoakShape(LoadTestShape):
    stages = [
        {"duration": 3600, "users": 50, "spawn_rate": 1},
    ]

    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        return None


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("[LOCUST] Test starting...")
    print(f"[LOCUST] Target engines: {list(ALL_ENGINES.keys())}")
    print(f"[LOCUST] Categories: { {e['category'] for e in ALL_ENGINES.values()} }")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("[LOCUST] Test completed")
    stats = environment.stats
    print(f"[LOCUST] Total requests: {stats.total.num_requests}")
    print(f"[LOCUST] Total failures: {stats.total.num_failures}")
    print(f"[LOCUST] Avg response time: {stats.total.avg_response_time:.2f}ms")
    print(f"[LOCUST] 95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    if exception:
        print(f"[LOCUST ERROR] {name}: {exception}")


@events.report_to_master.add_listener
def on_report_to_master(client_id, data):
    pass


@events.worker_report.add_listener
def on_worker_report(client_id, data):
    pass


if __name__ == "__main__":
    import sys

    from locust import main
    sys.argv = ["locust", "-f", __file__]
    main.main()
