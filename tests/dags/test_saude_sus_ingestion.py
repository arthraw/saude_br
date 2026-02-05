import pytest
from airflow.providers.databricks.hooks.databricks import DatabricksHook
from dotenv import load_dotenv
import os

load_dotenv()

DATABRICKS_USER = os.getenv('DATABRICKS_USER')
DATABRICKS_ROOT_PROJECT_PATH = f"/Workspace/Users/{DATABRICKS_USER}/saude_br/notebooks/"

def test_databricks_serverless_submission():
    conn_id = "databricks_default"
    hook = DatabricksHook(databricks_conn_id=conn_id)
    run_json = {
        'run_name': 'Teste Airflow Astro',
        'tasks': [{
            'task_key': 'test_task',
            'notebook_task': {
                'notebook_path': DATABRICKS_ROOT_PROJECT_PATH + "estabelecimentos/Transient_to_Bronze"
            },
            'serverless': {}
        }]
    }
    
    try:
        run_id = hook.submit_run(run_json)        

        # First assertion to check if run_id is returned
        assert run_id is not None
        result_test = hook.get_run(run_id)
        life_cycle_state = result_test.get("state", {}).get("life_cycle_state", "")
        print(f"Estado do Job {run_id}: {life_cycle_state}")

        # Second assertion to check if the job is in a valid state
        assert life_cycle_state in ["PENDING", "RUNNING", "TERMINATING", "TERMINATED", "SUCCESS"]
        
        # Third assertion to ensure the job did not end in an internal error
        assert life_cycle_state != "INTERNAL_ERROR"

    except Exception as e:
        pytest.fail(f"Erro ao disparar notebook no Serverless: {str(e)}")