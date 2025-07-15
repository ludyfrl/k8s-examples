# Spark-on-K8s
## Overview
Spark Jobs can be run within K8s clusters. But there are many ways to submit your Spark job into K8s clusters. Below is my experiment on trying different way to submit Spark job into K8s cluster.

## Components
- Kubernetes cluster - Minikube
- Docker
- Helm
- Spark client

## Installation
1. Install Minikube as our local kubernetes cluster. Also install `kubectl` to help us interact with Kubernetes cluster.
   ```bash
   # Linux
   curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
   sudo install minikube-linux-amd64 /usr/local/bin/minikube && rm minikube-linux-amd64

   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
   ```
2. Start Minikube cluster with sufficient resources and enable Docker environment within Minikube.
   ```bash
   minikube start --cpus=4 --memory=8192 --driver=docker
   eval $(minikube docker-env)
   ```
3. Create new K8s namespace for your Spark app.
   ```bash
   kubectl create namespace spark-app
   ```
4. Set up RBAC and ServiceAccount to give Spark permissions to create pods.
   ```bash
   kubectl apply -f spark-rbac.yaml
   ```


## Submitting Spark Jobs
There are many ways of submitting Spark jobs into K8s cluster. Below is some of the possible methods.

### Using spark-submit
We can use spark-submit script in Spark’s bin directory to launch applications on a K8s cluster. This is the most common and flexible way to submit a Spark job.
1. Install Spark on our local as Spark client to submit the job into our K8s cluster.
   ```bash
   # Using Spark 3.5.5
   curl -LO https:///dlcdn.apache.org/spark/spark-3.5.5/spark-3.5.5-bin-hadoop3-scala2.13.tgz
   tar -xvzf spark-3.5.5-bin-hadoop3-scala2.13.tgz && rm spark-3.5.5-bin-hadoop3-scala2.13.tgz

   # Build local Spark image
   ${SPARK_HOME}/bin/docker-image-tool.sh -p ${SPARK_HOME}/kubernetes/dockerfiles/spark/bindings/python/Dockerfile build
   ```
2. Submit Spark job, we can either use client or cluster mode. Notice that when using client mode we can directly upload file in our local storage without bundling it into image. That's because in client mode, the Spark driver actually running in our local machine, not in the K8s cluster.
   ```bash
   # Using cluster mode
   docker build -t pyspark-word-count:latest ./spark-app/python/word-count/
   $SPARK_HOME/bin/spark-submit \
      --master k8s://https://$(minikube ip):8443 \
      --deploy-mode cluster \
      --name word-count-spark \
      --conf spark.kubernetes.container.image={IMAGE_NAME:TAG} \
      --conf spark.executor.instances=1 \
      --conf spark.kubernetes.namespace=spark-app \
      --conf spark.kubernetes.file.upload.path=/tmp \
      --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark \
      local:///opt/spark/app/main.py
   
   # Using client mode
   $SPARK_HOME/bin/spark-submit \
      --master k8s://https://$(minikube ip):8443 \
      --deploy-mode client \
      --name simple-df-spark \
      --conf spark.kubernetes.container.image=spark-py:latest \
      --conf spark.executor.instances=1 \
      --conf spark.kubernetes.namespace=spark-app \
      --conf spark.kubernetes.file.upload.path=/workspaces/spark-on-k8s/tmp \
      --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark \
      ./spark-app/python/simple-df/main.py
   ```

### Using Spark Kubernetes Operator
Spark Kubernetes Operator treats your Spark Jobs as native K8s resources. It uses CustomResourceDefinitions (CRDs) to define Spark jobs, which is yaml based. Best used for production, large scale Spark apps.

I am using the relatively new [Spark Kubernetes Operator by Apache](https://github.com/apache/spark-kubernetes-operator) because it should be designed for Apache Spark first, whereas the other with larger user base, [Kubeflow Spark Operator](https://github.com/kubeflow/spark-operator), is designed for Kubeflow first.
1. Install Helm chart for spark-kubernetes-operator.
   ```bash
   # Install Helm - Linux
   curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null
   sudo apt-get install apt-transport-https --yes
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
   sudo apt-get update
   sudo apt-get install helm

   # Install chart for spark-kubernetes-operator
   helm repo add spark-kubernetes-operator https://apache.github.io/spark-kubernetes-operator
   helm repo update
   helm install spark-kubernetes-operator spark-kubernetes-operator/spark-kubernetes-operator \
      --namespace spark-app \
      --set workloadResources.serviceAccount.create=false \ # Set to false because we already have SA for Spark
      --version 1.0.0
   ```
2. Build Spark app image
   ```bash
   docker build -t pyspark-word-count:latest ./spark-app/python/word-count/
   ```
3. Deploy Spark app using Spark K8s Operator
   ```bash
   kubectl apply -f spark-app/kubernetes/word-count-py.yaml
   ```
4. Check Spark Application status
   ```bash
   kubectl get sparkapp pyspark-word-count -n spark-app
   ```