from datetime import datetime, timezone
from uuid import uuid4

from authx.exceptions import MissingTokenError
from authx.schema import TokenPayload
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from pydantic.types import UUID4
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlmodel import Session, select

from src.database.db import get_session
from src.models.note import NoteModel as Note
from src.models.user import UserModel as User
from src.schemas.notes import CreateNoteSchema, UpdateNoteSchema
from src.utils.auth import security

router = APIRouter(prefix="/me", tags=["Notes"])


@router.get("/notes", dependencies=[Depends(security.access_token_required)])
async def get_all_notes(
        payload: TokenPayload = Depends(security.access_token_required),
        session: Session = Depends(get_session),
):
    try:
        user = session.exec(select(User).where(User.id == payload.sub)).first()
        if user:
            return {
                "message": f"All notes from {user.username}",
                "notes": user.notes
            }
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="User not found")
    except MissingTokenError:
        return HTTPException(status_code=401,
                             detail="Could not validate credentials")


@router.get("/notes/{note_id}",
            dependencies=[Depends(security.access_token_required)])
async def get_note(note_id: UUID4, session: Session = Depends(get_session)):
    try:
        note = session.exec(select(Note).where(Note.id == note_id)).one()
        if note:
            return note
    except NoResultFound as ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Note not found") from ex


@router.post("/notes", dependencies=[Depends(security.access_token_required)])
async def create_note(
        new_note: CreateNoteSchema,
        payload: TokenPayload = Depends(security.access_token_required),
        session: Session = Depends(get_session),
):
    try:
        user = session.exec(select(User).where(User.id == payload.sub)).one()
        note = Note(id=uuid4(),
                    title=new_note.title,
                    content=new_note.content,
                    owner_id=user.id,
                    owner=user)
        session.add(note)
        session.commit()
        session.refresh(note)
        return note
    except ValidationError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Invalid data") from ve
    except IntegrityError as ie:
        raise HTTPException(status_code=422,
                            detail="Note already exists") from ie


@router.put("/notes/{note_id}",
            dependencies=[Depends(security.access_token_required)])
async def update_note(
        note_id: UUID4,
        data: UpdateNoteSchema,
        payload: TokenPayload = Depends(security.access_token_required),
        session: Session = Depends(get_session),
):
    try:
        note = session.exec(
            select(Note).where(Note.owner_id == payload.sub).where(
                Note.id == note_id)).one()
        note.title = data.title
        note.content = data.content
        note.updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        session.add(note)
        session.commit()
        session.refresh(note)
        return note
    except ValidationError as ve:
        raise HTTPException(status_code=422, detail="Invalid data") from ve
    except NoResultFound as ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Note not found") from ex


@router.delete("/notes/{note_id}",
               dependencies=[Depends(security.access_token_required)])
async def delete_note(note_id: UUID4,
                      payload: TokenPayload = Depends(
                          security.access_token_required),
                      session: Session = Depends(get_session)):
    try:
        note = session.exec(
            select(Note).where(Note.id == note_id,
                               Note.owner_id == payload.sub)).one()
        session.delete(note)
        session.commit()
        return {"message": f"Note #{note_id} deleted"}
    except NoResultFound as result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Note not found") from result
