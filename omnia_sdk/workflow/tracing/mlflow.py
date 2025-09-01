import mlflow
from mlflow.tracing.destination import MlflowExperiment


def setup_mlflow_tracing(experiment_name: str) -> None:
    mlflow.autolog()
    experiment = mlflow.get_experiment_by_name(experiment_name)
    experiment_id = experiment.experiment_id if experiment else mlflow.create_experiment(name=experiment_name)
    mlflow.tracing.set_destination(MlflowExperiment(experiment_id=experiment_id), context_local=True)
