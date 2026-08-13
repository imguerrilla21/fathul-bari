from sqlalchemy.orm import Session
from app.models.research import ResearchWorkspaceEntity, WorkspaceItemEntity, ResearchNoteEntity, ComparativeLinkEntity

class WorkspaceService:
    def create_workspace(self, db: Session, user_id: str, name: str, description: str = None, research_question: str = None):
        workspace = ResearchWorkspaceEntity(
            user_id=user_id,
            name=name,
            description=description,
            research_question=research_question
        )
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
        return workspace

    def add_item(self, db: Session, workspace_id: str, item_type: str, entity_id: str, title: str = None):
        item = WorkspaceItemEntity(
            workspace_id=workspace_id,
            item_type=item_type,
            entity_id=entity_id,
            title=title
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def create_note(self, db: Session, workspace_id: str, user_id: str, content: str, title: str = None, note_type: str = "OBSERVATION"):
        note = ResearchNoteEntity(
            workspace_id=workspace_id,
            user_id=user_id,
            title=title,
            content=content,
            note_type=note_type
        )
        db.add(note)
        db.commit()
        db.refresh(note)
        return note

    def create_comparative_link(self, db: Session, hadith_id: str, source_a_id: str, source_b_id: str, relationship: str = "POTENTIAL_DIFFERENCE", notes: str = None):
        link = ComparativeLinkEntity(
            hadith_id=hadith_id,
            source_a_id=source_a_id,
            source_b_id=source_b_id,
            relationship=relationship,
            notes=notes
        )
        db.add(link)
        db.commit()
        db.refresh(link)
        return link

    def get_workspace_context(self, db: Session, workspace_id: str):
        # Retrieve all items and notes for a workspace to feed to AI
        items = db.query(WorkspaceItemEntity).filter(WorkspaceItemEntity.workspace_id == workspace_id).all()
        notes = db.query(ResearchNoteEntity).filter(ResearchNoteEntity.workspace_id == workspace_id).all()
        
        context = {
            "items": [{"id": i.id, "type": i.item_type, "entity_id": i.entity_id} for i in items],
            "notes": [{"id": n.id, "content": n.content} for n in notes]
        }
        return context
