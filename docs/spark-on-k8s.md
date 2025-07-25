# Spark-on-K8s
## Overview
Spark Jobs can be run within K8s clusters. But there are many ways to submit your Spark job into K8s clusters. Below is my experiment on trying different way to submit Spark job into K8s cluster.

## Components
- Minikube — Local Kubernetes cluster
- Docker — CRI for Minikube
- Helm
- Spark client
- Python (3.10) — Version must match across Docker images and Python in your local. You can use virtualenv to solve this

## Installation
1. Install Minikube as our local K8s cluster. Also install `kubectl` to help us interact with K8s cluster.
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
4. Set up RBAC and ServiceAccount to give Spark permissions to managing pods.
   ```bash
   kubectl apply -f manifests/spark/spark-rbac.yaml
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
   export SPARK_HOME="spark-3.5.5-bin-hadoop3-scala2.13"

   # Build local Spark image -- `spark` and `spark-py`
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
      --conf spark.kubernetes.container.image=pyspark-word-count:latest \
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
      --conf spark.kubernetes.file.upload.path=spark-on-k8s/tmp \
      --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark \
      ./spark-app/python/simple-df/main.py
   ```
3. Use this command in different terminal to watch the Pods status changes over the time.
   ```bash
   kubectl get pods -n spark-app -w
   ```

### Using Spark Kubernetes Operator
Spark Kubernetes Operator treats your Spark Jobs as native K8s resources. It uses CustomResourceDefinitions (CRDs) to define Spark jobs, which is yaml based. Best used for production, large scale Spark apps.

I am using [Kubeflow Spark Operator](https://github.com/kubeflow/spark-operator) because this version is used by Airflow example and also the most used Spark Operator by community.
1. Install Helm chart for spark-kubernetes-operator.
   ```bash
   # Install Helm - Linux
   curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null
   sudo apt-get install apt-transport-https --yes
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
   sudo apt-get update
   sudo apt-get install helm

   # Install chart for spark-kubernetes-operator
   helm repo add --force-update spark-operator https://kubeflow.github.io/spark-operator
   helm install spark-operator spark-operator/spark-operator \
      --namespace spark-operator \
      --create-namespace \
      --set "spark.jobNamespaces={spark-app}" \
      --wait
   ```
2. Build Spark app image
   ```bash
   docker build -t pyspark-word-count:latest ./spark-app/python/word-count/
   ```
3. Deploy Spark app using Spark K8s Operator
   ```bash
   kubectl apply -f manifests/spark/word-count-py.yaml
   ```
4. Check Spark Application status
   ```bash
   kubectl get sparkapp pyspark-word-count -n spark-app
   ```

### Using Apache Airflow
1. Add Airflow Helm repo
   ```bash
   helm repo add apache-airflow https://airflow.apache.org
   helm repo update
   ```
2. Create namespace for Airflow in k8s
   ```bash
   kubectl create namespace airflow
   ```
3. Create PV and PVC for our Airflow dags
   ```bash
   # Copy DAGs file to Minikube
   scp -r -i $(minikube ssh-key) $(pwd)/airflow/ docker@$(minikube ip):/tmp/

   # Create PV and PVC
   kubectl apply -f manifests/airflow/airflow-pv-dags.yaml
   ```
4. Install Airflow
   ```bash
   # Install Airflow version 3.0.2
   helm install airflow apache-airflow/airflow \
      --set dags.persistence.enabled=true \
      --set dags.persistence.existingClaim=airflow-dags-pvc \
      --set dags.gitSync.enabled=false \
      --version 1.18.0 \
      --namespace airflow \
      --debug
   ```
5. Grant permission for Airflow worker to access spark-app namespace.
   ```bash
   kubectl apply -f manifests/airflow/airflow-spark-operator.yaml
   ```
6. Port forward Airflow UI to port 8080
   ```bash
   kubectl port-forward svc/airflow-api-server 8080:8080 --namespace airflow
   ```