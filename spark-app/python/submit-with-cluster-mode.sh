$SPARK_HOME/bin/spark-submit \
  --master k8s://https://$(minikube ip):8443 \
  --deploy-mode cluster \
  --name test-spark-job \
  --conf spark.kubernetes.container.image=py-spark:3.5.5 \
  --conf spark.executor.instances=1 \
  --conf spark.kubernetes.namespace=spark-app \
  --conf spark.kubernetes.file.upload.path=/workspaces/spark-on-k8s/tmp \
  --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark \
  local:///opt/spark/app/main.py