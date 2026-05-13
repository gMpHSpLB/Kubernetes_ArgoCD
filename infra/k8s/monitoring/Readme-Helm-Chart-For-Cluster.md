 Treat cluster monitoring as its own Helm chart (“umbrella” chart) under infra/k8s/monitoring, separate from your application charts under charts/. That matches what you’re already doing for charts/myapp and works very well with Argo CD + ApplicationSets.

You’d end up with:

    App‑level charts: charts/myapp, charts/mylearning, charts/postgres (already there).

    Infra‑level chart: infra/k8s/monitoring as a Helm chart that depends on kube-prometheus-stack and optionally wires in your alertmanager configs, Grafana dashboards, etc.

Key points:

    infra/k8s/monitoring is a Helm chart root, just like charts/myapp.

    The chart declares kube-prometheus-stack as a dependency in Chart.yaml.

    Your environment‑specific values files are just extra values the Argo CD ApplicationSet passes with helm.valueFiles.

This is the umbrella‑chart pattern lots of folks use for monitoring stacks.

Why not reuse charts/myapp directly?
Your charts/myapp is an application chart focused on your app’s deployment, service, ServiceMonitor, etc. It’s not the right place to own cluster‑wide monitoring infra because:

    Monitoring infra has a different lifecycle than the app itself (e.g., you might upgrade kube‑prometheus‑stack independently).

    You may want to reuse the same monitoring chart across other apps in the future.

    Keeping app charts and infra charts separated keeps concerns clean and makes Argo CD Applications more composable (one for cluster monitoring, one for each app).

So the standard pattern is:

    charts/myapp – app chart, used by myapp-<env> Applications.

    infra/k8s/monitoring – monitoring umbrella chart, used by cluster-monitoring-infra-<env> Applications from your ApplicationSet.

This matches what people typically do with umbrella charts for infra, as in the “Install Kube‑Prometheus‑Stack, Loki, and Vault using App‑of‑Apps and Helm” style setups.