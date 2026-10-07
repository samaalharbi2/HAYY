#!/usr/bin/env bash
# Start a local Airflow for BALAGH.
# Airflow lives in its own environment (~/airflow-venv), outside the project,
# so its dependencies never conflict with dbt or pandas.

export AIRFLOW_HOME="$HOME/airflow"                                  # Airflow's database, logs and config
export AIRFLOW__CORE__DAGS_FOLDER="$HOME/code/BALAGH/airflow/dags"   # read DAGs from this repo
export AIRFLOW__CORE__LOAD_EXAMPLES=False                            # hide the ~50 example DAGs
export AIRFLOW__CORE__MAX_ACTIVE_TASKS_PER_DAG=1

source "$HOME/airflow-venv/bin/activate"
airflow standalone
