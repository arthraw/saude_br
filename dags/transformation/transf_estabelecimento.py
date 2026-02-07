from airflow.sdk import dag, task, task_group
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
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
    dag_id="estabelecimento_transformation",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["transformation", "saude", "sus", "estabelecimento"]
)
def estabelecimento_transformation_dag():
    
    transform_trusted = DatabricksSubmitRunOperator(
        task_id="run_estabelecimento_trusted_data_transformation",
        databricks_conn_id=DATABRICKS_CONN_ID,
        json={
            'run_name': 'Transform Operation Estabelecimento - ' + now().strftime("%Y-%m-%d_%H:%M:%S"),
            'tasks': [{
                'task_key': 'transform_estabelecimento_task',
                'notebook_task': {'notebook_path': f"{DATABRICKS_ROOT_PROJECT_PATH}estabelecimentos/tru_estabelecimento"},
                'serverless': {}
            }]
        }
    )

    @task_group(
        group_id="dim_transformations",
        tooltip="Tasks to transform data from trusted to dimensional model in Databricks",
        ui_color="#f0a14e"
    )
    def dim_transformations():
        dim_list = ['dim_estabelecimento', 'dim_tipo_unidade', 'dim_localizacao', 'dim_turno']
        tasks = []
        for dim in dim_list:
            transform_dim = DatabricksSubmitRunOperator(
                task_id=f"run_{dim}_transformation",
                databricks_conn_id=DATABRICKS_CONN_ID,
                json={
                    'run_name': f'Transform Operation {dim} - ' + now().strftime("%Y-%m-%d_%H:%M:%S"),
                    'tasks': [{
                        'task_key': f'transform_{dim}_task',
                        'notebook_task': {'notebook_path': f"{DATABRICKS_ROOT_PROJECT_PATH}estabelecimentos/{dim}"},
                        'serverless': {}
                    }]
                }
            )
            tasks.append(transform_dim)
        
        return tasks
    

    fact_cadastro =  DatabricksSubmitRunOperator(
            task_id="run_fact_cadastro_transformation",
            databricks_conn_id=DATABRICKS_CONN_ID,
            json={
                'run_name': 'Transform Operation Fact Cadastro - ' + now().strftime("%Y-%m-%d_%H:%M:%S"),
                'tasks': [{
                    'task_key': 'transform_fact_cadastro_task',
                    'notebook_task': {'notebook_path': f"{DATABRICKS_ROOT_PROJECT_PATH}estabelecimentos/fact_cadastro"},
                    'serverless': {}
                }]
            }
        )
    
    transform_trusted >> dim_transformations() >> fact_cadastro

estabelecimento_transformation_dag()