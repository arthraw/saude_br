from airflow.sdk import dag, task, task_group
from airflow.providers.airbyte.operators.airbyte import AirbyteTriggerSyncOperator
from airflow.providers.databricks.hooks.databricks import DatabricksHook
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.models import Variable
from pendulum import datetime, now

# Global variables definition - Configuration
DATABRICKS_USER = Variable.get("DATABRICKS_USER")
DATABRICKS_CLUSTER_ID = Variable.get("DATABRICKS_CLUSTER_ID")
AIRBYTE_CONN_NAME = "airbyte_conn"
AIRBYTE_CONNECTION_ID = Variable.get("AIRBYTE_CONNECTION_ID")
DATABRICKS_ROOT_PROJECT_PATH = f"/Workspace/Users/{DATABRICKS_USER}/saude_br/notebooks/"
DATABRICKS_CONN_ID = "databricks_default"
default_args = {
    'owner': 'Arthur Andrade',
    'retries':30,
}

@dag(
    dag_id="saude_sus_ingestion",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["ingestion", "saude", "sus"],
)
def saude_sus_ingestion_dag():
    
    ingest_from_airbyte = AirbyteTriggerSyncOperator(
        task_id="ingest_from_airbyte",
        airbyte_conn_id=AIRBYTE_CONN_NAME,
        connection_id=AIRBYTE_CONNECTION_ID,
        deferrable=True
    )
    
    @task_group(
        group_id="ingestion_to_raw",
        tooltip="Tasks to copy data from staging to bronze layer in Databricks",
        ui_color="#4eb7f0"
    )
    def ingestion_to_raw():
        copy_estabelecimento = DatabricksSubmitRunOperator(
            task_id="run_estabelecimento_staging_data_copy_to_bronze",
            databricks_conn_id=DATABRICKS_CONN_ID,
            json={
                'run_name': 'Copy Operation Estabelecimento - ' + now().strftime("%Y-%m-%d_%H:%M:%S"),
                'tasks': [{
                    'task_key': 'copy_estabelecimento_task',
                    'notebook_task': {'notebook_path': f"{DATABRICKS_ROOT_PROJECT_PATH}estabelecimentos/Transient_to_Bronze"},
                    'serverless': {}
                }]
            }
        )

        copy_tipo_unidade = DatabricksSubmitRunOperator(
            task_id="run_tipo_unidade_staging_data_copy_to_bronze",
            databricks_conn_id=DATABRICKS_CONN_ID,
            json={
                'run_name': 'Copy Operation Tipo Unidade - ' + now().strftime("%Y-%m-%d_%H:%M:%S"),
                'tasks': [{
                    'task_key': 'copy_tipo_unidade_task',
                    'notebook_task': {'notebook_path': f"{DATABRICKS_ROOT_PROJECT_PATH}tipo_unidade/Transient_to_Bronze"},
                    'serverless': {}
                }]
            }
        )
        [copy_estabelecimento, copy_tipo_unidade]


    trigger_transformation_dag = TriggerDagRunOperator(
        task_id='trigger_transformation_dag',
        trigger_dag_id='estabelecimento_transformation',
        wait_for_completion=False,
        poke_interval=30
    )

    ingest_from_airbyte >> ingestion_to_raw() >> trigger_transformation_dag

saude_sus_ingestion_dag()
