from airflow.sdk import dag, task
from airflow.providers.airbyte.operators.airbyte import AirbyteTriggerSyncOperator
from airflow.providers.databricks.hooks.databricks import DatabricksHook
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

    @task(task_id="run_estabelecimento_staging_data_copy_to_bronze")
    def run_estabelecimento_staging_data_copy_to_bronze():
        run_json = {
            'run_name': f'Copy Estabelecimento Transient Data To Bronze - {now().strftime("%Y-%m-%d_%H:%M:%S")}',
            'tasks': [{
                'task_key': 'estabelecimento_transient_to_bronze_task',
                'notebook_task': {
                    'notebook_path': DATABRICKS_ROOT_PROJECT_PATH + "estabelecimentos/Transient_to_Bronze"
                },
                'serverless': {}
            }]
        }
        try:
            hook = DatabricksHook(databricks_conn_id=DATABRICKS_CONN_ID)
            run_id = hook.submit_run(run_json)        

            result_test = hook.get_run(run_id)
            life_cycle_state = result_test.get("state", {}).get("life_cycle_state", "")

            while life_cycle_state not in ["TERMINATED", "SUCCESS", "INTERNAL_ERROR"]:
                import time 
                time.sleep(30)  # Wait for 30 seconds before checking the status again
                result_test = hook.get_run(run_id)
                life_cycle_state = result_test.get("state", {}).get("life_cycle_state", "")
                print(f"Job {run_id} state: {life_cycle_state}")
            
            print(f"Job {run_id} finished with state: {life_cycle_state}")
        except Exception as e:
            print(f"Error while running copy task in databricks: {str(e)}")

    @task(task_id="run_tipo_unidade_staging_data_copy_to_bronze")
    def run_tipo_unidade_staging_data_copy_to_bronze():
        run_json = {
            'run_name': f'Copy Tipo Unidade Transient Data To Bronze - {now().strftime("%Y-%m-%d_%H:%M:%S")}',
            'tasks': [{
                'task_key': 'tipo_unidade_transient_to_bronze_task',
                'notebook_task': {
                    'notebook_path': DATABRICKS_ROOT_PROJECT_PATH + "tipo_unidade/Transient_to_Bronze"
                },
                'serverless': {}
            }]
        }
        try:
            hook = DatabricksHook(databricks_conn_id=DATABRICKS_CONN_ID)
            run_id = hook.submit_run(run_json)        

            result_test = hook.get_run(run_id)
            life_cycle_state = result_test.get("state", {}).get("life_cycle_state", "")

            while life_cycle_state not in ["TERMINATED", "SUCCESS", "INTERNAL_ERROR"]:
                import time 
                time.sleep(30)  # Wait for 30 seconds before checking the status again
                result_test = hook.get_run(run_id)
                life_cycle_state = result_test.get("state", {}).get("life_cycle_state", "")
                print(f"Job {run_id} state: {life_cycle_state}")
            
            print(f"Job {run_id} finished with state: {life_cycle_state}")
        except Exception as e:
            print(f"Error while running copy task in databricks: {str(e)}")


    copy_estabelecimento_data_staging_to_raw = run_estabelecimento_staging_data_copy_to_bronze()
    copy_tipo_unidade_data_staging_to_raw = run_tipo_unidade_staging_data_copy_to_bronze()
    
    trigger_transformation_dag = TriggerDagRunOperator(
        task_id='trigger_transformation_dag',
        trigger_dag_id='estabelecimento_transformation',
        wait_for_completion=False,
        poke_interval=30
    )

    ingest_from_airbyte >> [copy_estabelecimento_data_staging_to_raw, copy_tipo_unidade_data_staging_to_raw] >> trigger_transformation_dag

saude_sus_ingestion_dag()
