from sqlalchemy.orm import Session

from ..models import Destination, JobDelivery, JobDocument, ScanJob, ScanProfile, Workflow
from .destinations import DestinationError, deliver_file
from .naming import NamingError, resolve_document_metadata


def deliver_job(db: Session, job: ScanJob, workflow: Workflow, destination: Destination, source_path: str | None = None, target_name: str | None = None) -> JobDelivery:
    delivery = JobDelivery(
        scan_job_id=job.id,
        workflow_id=workflow.id,
        destination_id=destination.id,
        status="delivering",
    )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    try:
        target = deliver_file(
            destination.type,
            destination.config_json,
            source_path or job.output_path or job.input_path or "",
            target_name=target_name,
        )
        delivery.status = "delivered"
        delivery.target_path = target
        delivery.error = None
    except DestinationError as exc:
        delivery.status = "error"
        delivery.error = str(exc)

    db.commit()
    db.refresh(delivery)
    return delivery


def deliver_to_matching_inbox_workflows(db: Session, job: ScanJob, profile_id: int) -> list[JobDelivery]:
    workflows = (
        db.query(Workflow)
        .filter(
            Workflow.profile_id == profile_id,
            Workflow.scanner_id.is_(None),
            Workflow.enabled.is_(True),
        )
        .order_by(Workflow.id)
        .all()
    )

    deliveries: list[JobDelivery] = []
    documents = db.query(JobDocument).filter(JobDocument.scan_job_id == job.id).order_by(JobDocument.sequence).all()
    profile = db.get(ScanProfile, profile_id)

    for workflow in workflows:
        destination = db.get(Destination, workflow.destination_id)
        if not destination or not destination.enabled:
            continue
        if job.workflow_id is None:
            job.workflow_id = workflow.id
            db.commit()

        if documents and profile:
            for document in documents:
                try:
                    metadata = resolve_document_metadata(db, job, profile, document)
                    deliveries.append(
                        deliver_job(
                            db,
                            job,
                            workflow,
                            destination,
                            source_path=document.path,
                            target_name=metadata.final_filename,
                        )
                    )
                except NamingError as exc:
                    delivery = JobDelivery(
                        scan_job_id=job.id,
                        workflow_id=workflow.id,
                        destination_id=destination.id,
                        status="error",
                        error=str(exc),
                    )
                    db.add(delivery)
                    db.commit()
                    db.refresh(delivery)
                    deliveries.append(delivery)
        else:
            source_path = job.output_path or job.input_path or ""
            deliveries.append(deliver_job(db, job, workflow, destination, source_path=source_path))

    if deliveries:
        if all(item.status == "delivered" for item in deliveries):
            job.status = "delivered"
            job.error = None
        else:
            job.status = "delivery_error"
            errors = [item.error for item in deliveries if item.error]
            job.error = " | ".join(errors) if errors else "Weiterleitung fehlgeschlagen."
        db.commit()

    return deliveries
