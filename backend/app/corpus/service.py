from sqlalchemy.orm import Session
from app.models.corpus import ScholarlyWorkEntity, ScholarlyEditionEntity, ScholarlyVolumeEntity, SourceFileEntity
from app.corpus.fingerprint import generate_edition_fingerprint

class CorpusService:
    def create_work(self, db: Session, title_ar: str, author: str, title_id: str = None, work_type: str = "SHARH", description: str = ""):
        work = ScholarlyWorkEntity(
            title_ar=title_ar,
            title_id=title_id,
            author=author,
            work_type=work_type,
            description=description
        )
        db.add(work)
        db.commit()
        db.refresh(work)
        return work
        
    def create_edition(self, db: Session, work_id: str, publisher: str, editor: str, year: int, total_volumes: int, edition_number: str = "1"):
        fingerprint = generate_edition_fingerprint(
            title="mock", # For a real app, query work title
            publisher=publisher,
            editor=editor,
            year=year,
            volume_count=total_volumes
        )
        
        edition = ScholarlyEditionEntity(
            work_id=work_id,
            publisher=publisher,
            editor=editor,
            publication_year=year,
            total_volumes=total_volumes,
            edition_number=edition_number,
            metadata_json={"fingerprint": fingerprint}
        )
        db.add(edition)
        db.commit()
        db.refresh(edition)
        return edition
        
    def create_volume(self, db: Session, edition_id: str, volume_number: int, label: str = None):
        volume = ScholarlyVolumeEntity(
            edition_id=edition_id,
            volume_number=volume_number,
            label=label or f"Vol {volume_number}"
        )
        db.add(volume)
        db.commit()
        db.refresh(volume)
        return volume

    def register_source_file(self, db: Session, filename: str, mime_type: str, file_size: int, checksum: str, uploader: str):
        source_file = SourceFileEntity(
            filename=filename,
            mime_type=mime_type,
            file_size=file_size,
            checksum_sha256=checksum,
            uploaded_by=uploader
        )
        db.add(source_file)
        db.commit()
        db.refresh(source_file)
        return source_file
