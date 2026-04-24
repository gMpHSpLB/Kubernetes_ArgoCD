repeatable observability stack before pointing CI at real clusters. At an enterprise level, you want the same pattern in local, CI-kind/minikube, dev, staging, and prod, with only values changing.

Below is a concrete design and what to add.

1. Overall architecture and repo layout
Use Helm for everything, with a dedicated infra/k8s area that can be applied to any cluster (local, CI, dev, staging, prod) via different values files.

Proposed layout:

text
infra/
  k8s/
    monitoring/
      # upstream chart dependency via requirements or helmfile,
      # or you vendor charts as subcharts
      kube-prometheus-stack-values-dev.yaml
      kube-prometheus-stack-values-staging.yaml
      kube-prometheus-stack-values-prod.yaml

    logging/
      loki-stack-values-dev.yaml
      loki-stack-values-staging.yaml
      loki-stack-values-prod.yaml

    rules/
      prometheus-rules-base.yaml      # custom alerting rules

    # optional GitOps wrapper later (Flux/Argo)
    # flux/
    #   kustomization-monitoring.yaml
Charts you’ll use:

kube-prometheus-stack for Prometheus + Alertmanager + Grafana + exporters + CRDs.

loki-stack (or separate Loki + Promtail/Fluent Bit chart) for logs.

Your existing charts/myapp and charts/mylearning for apps.

Key idea: one stack, different values per environment.

2. Metrics: kube-prometheus-stack + ServiceMonitor
2.1 Install kube-prometheus-stack
For local/kind/minikube:

bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install kps prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f infra/k8s/monitoring/kube-prometheus-stack-values-dev.yaml
kube-prometheus-stack includes:

Prometheus Operator (manages Prometheus via CRDs).

Prometheus, Alertmanager, Grafana, node-exporter, kube-state-metrics.

Default dashboards and rules for cluster metrics.

In staging/prod, same command but with *-values-staging.yaml / *-values-prod.yaml.

Minimal kube-prometheus-stack-values-dev.yaml:

text
# infra/k8s/monitoring/kube-prometheus-stack-values-dev.yaml
grafana:
  adminPassword: "admin"         # dev only; staging/prod from secrets
  service:
    type: ClusterIP

prometheus:
  prometheusSpec:
    serviceMonitorSelectorNilUsesHelmValues: false
    podMonitorSelectorNilUsesHelmValues: false

alertmanager:
  enabled: true
You’ll later override Grafana admin/ingress in staging/prod and wire Alertmanager to Slack/PagerDuty.

2.2 Expose /metrics in apps
In myapp and mylearning:

Use Prometheus client library and expose /metrics. E.g., FastAPI + Prometheus middleware.

Confirm locally that curl http://localhost:8000/metrics works.

Your charts/myapp/templates/deployment.yaml already exposes port 8000. No change needed there besides ensuring app actually serves metrics.

2.3 Service + ServiceMonitor for myapp
Your service.yaml should have proper labels (you already do), e.g.:

text
apiVersion: v1
kind: Service
metadata:
  name: {{ include "myapp.fullname" . }}
  labels:
    app.kubernetes.io/name: {{ include "myapp.name" . }}
    app.kubernetes.io/instance: {{ .Release.Name }}
spec:
  selector:
    app.kubernetes.io/name: {{ include "myapp.name" . }}
    app.kubernetes.io/instance: {{ .Release.Name }}
  ports:
    - name: http
      port: 8000
      targetPort: 8000
Enterprise‑grade pattern: use ServiceMonitor CRDs, not only annotations, because you’re using Prometheus Operator.

Create charts/myapp/templates/servicemonitor.yaml:

text
{{- if .Values.metrics.enabled }}
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {{ include "myapp.fullname" . }}
  labels:
    release: kps          # must match kube-prometheus-stack's release label selector
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ include "myapp.name" . }}
      app.kubernetes.io/instance: {{ .Release.Name }}
  namespaceSelector:
    matchNames:
      - {{ .Release.Namespace }}
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
      scrapeTimeout: 10s
{{- end }}
In charts/myapp/values.yaml:

text
metrics:
  enabled: true
Do the same for mylearning (use path/port appropriate for that service).

This is the canonical Operator way: Prometheus discovers your ServiceMonitor and scrapes /metrics.

3. Logging: Loki + Promtail/Fluent Bit
3.1 Deploy Loki stack
For dev/kind/minikube:

bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm upgrade --install loki grafana/loki-stack \
  -n logging --create-namespace \
  -f infra/k8s/logging/loki-stack-values-dev.yaml
Minimal infra/k8s/logging/loki-stack-values-dev.yaml:

text
loki:
  auth_enabled: false

grafana:
  enabled: false  # you already have Grafana from kube-prometheus-stack

promtail:
  enabled: true
  config:
    clients:
      - url: http://loki:3100/loki/api/v1/push
Promtail tails container logs and pushes to Loki. In staging/prod, tune retention, storage, and auth.

3.2 Integrate logs in Grafana
Add Loki as a data source pointing at http://loki.logging.svc:3100 in Grafana’s values or via UI.

Build dashboards that correlate logs + metrics + traces (via Uptrace or OTEL collector).

4. Alerting: custom Prometheus rules
You want base alerts for:

High 5xx rate.

High latency.

Pod restarts.

Failed rollouts / unavailable replicas.

Create infra/k8s/rules/prometheus-rules-base.yaml:

text
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: myapp-base-rules
  namespace: monitoring
  labels:
    release: kps
spec:
  groups:
    - name: myapp.rules
      rules:
        # High 5xx rate
        - alert: High5xxRate
          expr: |
            rate(http_server_requests_seconds_count{job="myapp",status=~"5.."}[5m]) /
            rate(http_server_requests_seconds_count{job="myapp"}[5m]) > 0.05
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High 5xx rate for myapp"
            description: "More than 5% of requests are 5xx for 5 minutes."

        # High latency (p95 > 500ms)
        - alert: HighRequestLatency
          expr: |
            histogram_quantile(0.95,
              sum(rate(http_server_requests_seconds_bucket{job="myapp"}[5m])) by (le)
            ) > 0.5
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High request latency for myapp"
            description: "p95 latency > 500ms for 5 minutes."

        # Pod restarts
        - alert: PodRestartingFrequently
          expr: increase(kube_pod_container_status_restarts_total{namespace=~"default|myapp-namespace"}[10m]) > 3
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "Pods are restarting frequently"
            description: "Container restarts > 3 in 10m."

        # Deployment not fully available
        - alert: DeploymentNotAvailable
          expr: kube_deployment_status_replicas_available{deployment=~"myapp.*"} < kube_deployment_spec_replicas{deployment=~"myapp.*"}
          for: 10m
          labels:
            severity: critical
          annotations:
            summary: "Deployment not fully available"
            description: "myapp deployment has fewer available replicas than desired."
Apply it:

bash
kubectl apply -f infra/k8s/rules/prometheus-rules-base.yaml
kube-prometheus-stack’s Prometheus instance will pick up this PrometheusRule via the release: kps label.

In staging/prod, you can:

Tighten thresholds.

Route critical to PagerDuty, warning to Slack by configuring Alertmanager values for kube-prometheus-stack.

5. Traces: OTEL + Uptrace
You already use Uptrace/OTEL env vars; in K8s:

Ensure OTLP endpoint is reachable from cluster (OTEL_EXPORTER_OTLP_ENDPOINT pointing to Uptrace or an in-cluster OTEL Collector).

Optional enterprise pattern: deploy an OTEL Collector in-cluster to receive OTLP from apps and forward to Uptrace/Tempo/etc.

You can add a simple collector deployment later under infra/k8s/otel/.

6. Enterprise-grade polish and CI story
To make this production-ready across local/CI/dev/staging/prod:

Values layering:

Base chart defaults in charts/myapp/values.yaml.

Env-specific overrides: environments/dev|staging|prod/values-*.yaml for apps and for monitoring/logging stacks.

CI-kind job:

Start kind cluster.

Install kube-prometheus-stack + loki-stack with dev values.

Apply PrometheusRule.

Deploy myapp + mylearning (dev values).

Run smoke tests that hit /metrics and validate that Prometheus can see series.

Optionally port-forward Grafana and export dashboards as artifacts.

Dev/staging/prod clusters:

Use the same Helm commands with environment-appropriate values.

Secrets for Uptrace, DB, etc., created externally as you designed.

Alertmanager wired to real on-call channels in staging/prod.

7. What’s missing / next steps
Additional things worth adding for an enterprise setup:

SLOs & burn-rate alerts: build on top of your metrics to define SLO-based alerts (e.g. 99.9% success).

Multi-tenant Grafana: configure folders, teams, and RBAC per environment.

Central log retention: for Loki in prod, use object storage (S3/GCS/Azure Blob) with retention policies.

Security & cost: resource requests/limits for monitoring/logging components, PodSecurity (PSA) settings, and network policies restricting who can scrape metrics.