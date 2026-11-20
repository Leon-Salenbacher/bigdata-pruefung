import pendulum
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

# xkcd_pipeline.py located in <repo>/airflow/dags/.
REPO_DIR = "/opt/xkcd-project"
COMPOSE = f"python {REPO_DIR}/airflow/run_compose.py"

with DAG(
    dag_id = "xkcd_pipeline",
    start_date = pendulum.datetime(2026, 1, 1, tz="Europe/Berlin"),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["xkcd", "etl"],
) as dag:
    download = BashOperator(
        task_id = "download",
        cwd=REPO_DIR,
        bash_command=(
            f"{COMPOSE} --profile download run --rm -T "
            "-e XKCD_START_ID=1 -e XKCD_END_ID=10 xkcd-downloader"
        )
    )

    import_hdfs = BashOperator(
        task_id = "import_hdfs",
        cwd=REPO_DIR,
        bash_command =f"{COMPOSE} --profile tools run --rm -T hdfs-import",
    )

    transform = BashOperator(
        task_id = "transform",
        cwd=REPO_DIR,
        bash_command=f"{COMPOSE} --profile tools run --rm -T xkcd-transform",
    )

    export_postgres = BashOperator(
        task_id="export_postgres",
        cwd=REPO_DIR,
        bash_command=(
            f"{COMPOSE} --profile tools run --rm -T xkcd-postgres-export"
        ),
    )

    merge_comics = BashOperator(
        task_id="merge_comics",
        cwd=REPO_DIR,
        bash_command=(
            f"{COMPOSE} exec -T postgres "
            "psql -v ON_ERROR_STOP=1 -U xkcd -d xkcd < sql/merge_comics.sql"
        ),
    )

    download >> import_hdfs >> transform >> export_postgres >> merge_comics