# Deployments
1. Start Minikube cluster with sufficient resources and enable Docker environment within Minikube.
   ```bash
   minikube start --cpus=4 --memory=8192 --driver=docker
   ```
2. Deploy minio-operator
   ```bash
   kubectl apply -k "github.com/minio/operator?ref=v7.0.1"
   ```
3. Deploy minio-tenant
   ```bash
   kubectl create namespace minio-tenant

   kubectl apply -f ./manifests/minio-tenant/deployment.yaml
   kubectl apply -f ./manifests/minio-tenant/load-balancer.yaml
   ```