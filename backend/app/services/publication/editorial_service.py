from sqlalchemy.orm import Session
from app.models.publication import EditorialIssueEntity, PublicationEntity

def report_issue(db: Session, pub_id: str, block_id: str, issue_type: str, severity: str, description: str):
    issue = EditorialIssueEntity(
        publication_id=pub_id,
        block_id=block_id,
        issue_type=issue_type,
        severity=severity,
        description=description,
        status="OPEN"
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    
    # Optionally update publication status to EDITORIAL_REVIEW
    pub = db.query(PublicationEntity).filter(PublicationEntity.id == pub_id).first()
    if pub and pub.status == "DRAFT":
        pub.status = "EDITORIAL_REVIEW"
        db.commit()
        
    return issue

def get_issues_for_publication(db: Session, pub_id: str):
    return db.query(EditorialIssueEntity).filter(EditorialIssueEntity.publication_id == pub_id).order_by(EditorialIssueEntity.created_at.desc()).all()
