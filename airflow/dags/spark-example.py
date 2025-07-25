import pendulum

from airflow.providers.cncf.kubernetes.operators.spark_kubernetes import SparkKubernetesOperator
from airflow.decorators import dag, task

@dag(
    schedule=None,
    start_date=pendulum.datetime(2025, 7, 20, tz="UTC"),
    catchup=False,
    tags=["example"],
)
def spark_kubernetes_operator_example():
    """
    DAG to run Spark application via SparkKubernetesOperator.
    """
    @task.bash
    def run_echo() -> str:
        return 'echo "Starting Spark Application..."'

    # Create the task instance
    echo_task = run_echo()

    # Create Spark task - remove dag parameter and fix indentation
    spark_task = SparkKubernetesOperator(
        task_id="spark_task",
        image="pyspark-word-count:latest",
        code_path="local:///opt/spark/app/main.py",
        application_file="spark_job_template.yaml",
        namespace="spark-app",
    )
    
    # Set up task dependencies
    echo_task >> spark_task

# Instantiate the DAG
spark_dag = spark_kubernetes_operator_example()