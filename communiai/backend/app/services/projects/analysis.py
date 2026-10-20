"""Project expertise job handler."""
from sqlalchemy.orm import Session

from app.models import AIJob, AnalysisStatus, Project, ProjectAnalysis
from app.services import jobs
from app.services.ai import services as ai
from app.services.ai.provider import get_provider


def handle_analysis(db: Session, job: AIJob) -> None:
    analysis = db.get(ProjectAnalysis, job.resource_id)
    project = db.get(Project, analysis.project_id)
    analysis.result_json = ai.analyze_project(project, job.user_id)
    analysis.ai_model = get_provider().model
    analysis.status = AnalysisStatus.COMPLETED
    analysis.error_message = None


def on_analysis_failure(db: Session, job: AIJob, code: str, message: str) -> None:
    analysis = db.get(ProjectAnalysis, job.resource_id)
    if analysis and analysis.status == AnalysisStatus.PENDING:
        analysis.status = AnalysisStatus.FAILED
        analysis.error_message = message


def register_handlers() -> None:
    jobs.register("project_analysis", handle_analysis, on_analysis_failure)
