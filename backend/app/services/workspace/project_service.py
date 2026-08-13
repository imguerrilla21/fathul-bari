from sqlalchemy.orm import Session
from app.models.workspace import ResearchProject

def create_project(db: Session, title: str, description: str, created_by: str = "Peneliti Hadis"):
    project = ResearchProject(
        title=title,
        description=description,
        created_by=created_by
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def get_project(db: Session, project_id: str):
    return db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
