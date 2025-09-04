# Iceberg on K8s
## Overview


## Architecture


## MinIO Deployments
### Deployments without Cert-Manager
1. Start Minikube cluster with sufficient resources and enable addons for local-path StorageClass. Also setup label for our dedicated node worker.
   ```bash
   # Choose 4 nodes because we will have dedicated worker nodes.
   minikube start --cpus=4 --memory=8192 --driver=docker --nodes=4

   # Enable addons for local-path StorageClass
   minikube addons enable storage-provisioner-rancher

   # Setup label and taint for our worker nodes
   kubectl label nodes minikube-m03 minikube-m04 node-role.kubernetes.io/worker-node=true
   kubectl taint nodes minikube-m03 minikube-m04 dedicated=worker-node:NoSchedule
   ```
2. Add MinIO Operator helm repository and install MinIO Operator using Helm Chart.
   ```bash
   helm repo add minio-operator https://operator.min.io
   helm upgrade --install operator minio-operator/operator \
      --namespace minio-operator \
      --create-namespace \
      --values manifests/minio-operator/helm/values.yaml
   ```
3. Verify installation of all components.
   ```bash
   kubectl get all -o wide -n minio-operator
   ```
4. After all pods are running, then install MinIO Tenant.
   ```bash
   helm upgrade --install iceberg-minio minio-operator/tenant \
      --namespace iceberg-minio \
      --create-namespace \
      --values manifests/minio-tenant/helm/values.yaml
   ```
5. Port forward MinIO console service so we can access the Web UI for MinIO.
   ```bash
   kubectl port-forward svc/myminio-console 9443 -n iceberg-minio
   ```