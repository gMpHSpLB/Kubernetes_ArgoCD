infra/k8s/monitoring/crds:
kube-prometheus-stack-crds-all.yaml
kube-prometheus-stack-crds-big.yaml
kube-prometheus-stack-crds-core.yaml
kube-prometheus-stack-crds.yaml

They are applied by k8s-monitoring-crds-apply via kubectl apply --server-side, which is a good practice to keep CRDs out of Argo’s diffing and size limits.
