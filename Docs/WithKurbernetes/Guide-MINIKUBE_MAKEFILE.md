# Minikube Makefile Guide (WSL2 + Docker Desktop)

This guide explains how to use the provided `Makefile` to manage a local Kubernetes cluster with **Minikube** on **WSL2 + Docker Desktop**, and how to use the helper targets for day-to-day development, training, and troubleshooting. Minikube’s Docker driver lets you run Kubernetes directly inside the Docker engine, which is a good fit for WSL2 setups.

## Prerequisites

Before using the Makefile, ensure:

- Windows 11 with WSL2 (Ubuntu) is set up.
- Docker Desktop is installed, running, and configured to use Linux containers.
- Docker Desktop is connected to your WSL2 Ubuntu distro (Docker CLI works inside WSL2).
- Minikube is installed in the WSL2 Ubuntu environment with `minikube` available in the PATH.
- `kubectl` is installed; Minikube will configure it to talk to the cluster on start.

You can verify Docker and Minikube quickly:

```bash
docker version
minikube version
kubectl version --client
```

## Makefile overview

The Makefile provides:

- Cluster lifecycle targets: start, stop, recreate, delete.
- Safety target: `ensure-minikube` (start only if needed).
- `kubectl` convenience targets for nodes, pods, logs, and metrics.
- A `help` target so the Makefile is self-documenting.

You can run any target with:

```bash
make <target>
```

## Configuration variables

These variables live at the top of the Makefile and can be overridden when running `make`:

- `MINIKUBE_PROFILE`  
  Minikube profile (cluster) name. Default: `minikube`.  
  Profiles let you run and manage multiple local clusters.

- `MINIKUBE_DRIVER`  
  Minikube driver. This guide uses `docker`, which runs Kubernetes inside Docker containers rather than a separate VM.

- `MINIKUBE_MEMORY`  
  RAM assigned to the cluster in MB. Default: `6144` (≈ 6 GB).

- `MINIKUBE_CPUS`  
  CPU cores assigned to the cluster. Default: `4`.

- `NAMESPACE`  
  Default Kubernetes namespace used by `kubectl` helper targets. Default: `default`.

Override example:

```bash
make kubectl-get-pods NAMESPACE=staging
```

## Quick Start

Use these commands to start Minikube and verify that your local Kubernetes cluster is ready:

```bash
make ensure-minikube
make kubectl-get-nodes
make kubectl-get-pods
```

### What these commands do

- `make ensure-minikube` starts Minikube only if the cluster is not already healthy.
- `make kubectl-get-nodes` confirms the cluster node is in `Ready` state.
- `make kubectl-get-pods` lists pods in the `default` namespace.

### Reset the cluster

If the cluster is broken and normal start does not fix it:

```bash
make recreate-minikube
make kubectl-get-nodes
```

### Work in another namespace

If your app is deployed in a non-default namespace:

```bash
make kubectl-get-pods NAMESPACE=staging
make kubectl-get-all NAMESPACE=staging
```

### View logs

To inspect pod logs:

```bash
make kubectl-logs POD=<pod-name>
```

## Targets: detailed reference

### help

```bash
make help
```

- Shows all available targets with short descriptions, parsed from `##` comments.
- Use this as a built-in reference for you and your team.

---

### status-minikube

```bash
make status-minikube
```

- Runs `minikube status` for the configured profile.
- Use it to see component-level status:
  - `host`
  - `kubelet`
  - `apiserver`
  - `kubeconfig`
- Helpful for quick manual checks of cluster health.

---

### ensure-minikube

```bash
make ensure-minikube
```

- Checks Minikube status for `apiserver: Running`.
- If not running, starts Minikube with the configured driver, memory, and CPUs.
- Refreshes kubeconfig via `minikube update-context` to avoid stale endpoint issues.
- Use it at the top of any workflow that assumes a running cluster.

---

### start-minikube

```bash
make start-minikube
```

- Explicitly runs `minikube start` with:
  - `--driver=$(MINIKUBE_DRIVER)`
  - `--memory=$(MINIKUBE_MEMORY)`
  - `--cpus=$(MINIKUBE_CPUS)`
- Updates kubeconfig after start.
- Use it when you want to start the cluster without condition checks.

---

### stop-minikube

```bash
make stop-minikube
```

- Runs `minikube stop` for the profile.
- Frees CPU and memory while keeping cluster data and configuration.
- Use it when you’re done for the day but may work on the cluster again later.

---

### delete-minikube

```bash
make delete-minikube
```

- Runs `minikube delete --purge=true` for the profile.
- Fully removes the Minikube profile and associated resources.
- Use it when you want to remove the cluster completely.

---

### update-minikube-context

```bash
make update-minikube-context
```

- Runs `minikube update-context` to refresh the kubeconfig entry for Minikube.
- Fixes issues where `kubectl` is pointing at a stale Minikube endpoint or port.
- Use it after restarts or when `kubectl` fails to talk to the cluster.

---

### recreate-minikube

```bash
make recreate-minikube
```

- Stops the cluster.
- Deletes the profile (`--all=true --purge=true`).
- Starts a brand new cluster with the configured driver, memory, and CPUs.
- Updates kubeconfig after creation.
- Use it as a “hard reset” when the control plane fails to start or the profile is corrupted.

---

### dry-run

```bash
make dry-run
```

- Prints the exact `minikube start` command that would be run with current variables.
- Does **not** execute anything.
- Use it for training, documentation, or debugging configuration.

---

### kubectl-get-nodes

```bash
make kubectl-get-nodes
```

- Ensures Minikube is running via `ensure-minikube`.
- Runs `kubectl get nodes`.
- Use it to confirm that the cluster node is in `Ready` state after starting the cluster.

---

### kubectl-get-pods

```bash
make kubectl-get-pods
make kubectl-get-pods NAMESPACE=staging
```

- Ensures Minikube is running.
- Runs `kubectl get pods -n $(NAMESPACE)`.
- Use it to view pod status in any namespace, especially when validating deployments or debugging.

---

### kubectl-get-all

```bash
make kubectl-get-all
make kubectl-get-all NAMESPACE=staging
```

- Ensures Minikube is running.
- Runs `kubectl get all -n $(NAMESPACE)`.
- Use it for a broad overview of workloads and services in a namespace.

---

### kubectl-describe-node

```bash
make kubectl-describe-node
```

- Ensures Minikube is running.
- Runs `kubectl describe node minikube`.
- Use it to inspect node conditions, capacities, labels, and recent events when debugging resource or scheduling issues.

---

### kubectl-logs

```bash
make kubectl-logs POD=<pod-name>
make kubectl-logs POD=<pod-name> CONTAINER=<container>
```

- Ensures Minikube is running.
- Checks that `POD` is provided; optionally accepts `CONTAINER`.
- Runs `kubectl logs` for the pod/container.
- Use it for application-level debugging via logs.

---

### kubectl-top-pods

```bash
make kubectl-top-pods
make kubectl-top-pods NAMESPACE=staging
```

- Ensures Minikube is running.
- Runs `kubectl top pods -n $(NAMESPACE)` if metrics-server is available.
- Use it to see CPU and memory usage per pod during performance analysis or incident response.

## Typical workflows

### Day-to-day development

```bash
make ensure-minikube
make kubectl-get-nodes
make kubectl-get-pods
make kubectl-get-all
```

### Working in a non-default namespace

```bash
make ensure-minikube
make kubectl-get-pods NAMESPACE=staging
make kubectl-get-all NAMESPACE=staging
```

### Debugging an application

```bash
make ensure-minikube
make kubectl-logs POD=my-app-pod
make kubectl-top-pods
```

### Hard reset of the cluster

```bash
make recreate-minikube
make kubectl-get-nodes
```

## Troubleshooting (WSL2 + Docker Desktop)

For WSL2 + Docker Desktop, common issues include Docker not being ready or Minikube failing to connect to the Docker engine.

- Ensure Docker Desktop is running and configured for **Linux containers**.
- Confirm Docker works inside WSL2:
  ```bash
  docker ps
  ```
- If Minikube fails with driver-related errors:
  - Check the Minikube Docker driver docs.
  - Confirm WSL2 is properly linked to Docker Desktop.

If issues persist after `recreate-minikube`, it can help to:

- Restart Docker Desktop.
- Restart the WSL2 instance.
- Then run:
  ```bash
  make ensure-minikube
  make kubectl-get-nodes
  ```