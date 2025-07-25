from typing import Any

import httpx
import pendulum

from airflow.models.baseoperator import BaseOperator
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import dag, task, Context


class GetRequestOperator(BaseOperator):
    """Custom operator to send GET request to provided url"""

    template_fields = ("url",)

    def __init__(self, *, url: str, **kwargs):
        super().__init__(**kwargs)
        self.url = url

    def execute(self, context: Context):
        return httpx.get(self.url).json()


@dag(
    schedule=None,
    start_date=pendulum.datetime(2025, 7, 20, tz="UTC"),
    catchup=False,
    tags=["example"],
)
def example_dag_decorator(url: str = "http://httpbin.org/get"):
    """
    DAG to get IP address and echo it via BashOperator.

    :param url: URL to get IP address from. Defaults to "http://httpbin.org/get".
    """
    get_ip = GetRequestOperator(task_id="get_ip", url=url)

    @task(multiple_outputs=True)
    def prepare_command(raw_json: dict[str, Any]) -> dict[str, str]:
        external_ip = raw_json["origin"]
        return {
            "command": f"echo 'Seems like today your server executing Airflow is connected from IP {external_ip}'",
        }

    command_info = prepare_command(get_ip.output)

    BashOperator(task_id="echo_ip_info", bash_command=command_info["command"])


example_dag = example_dag_decorator()