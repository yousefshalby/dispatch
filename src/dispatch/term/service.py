
from dispatch.definition import service as definition_service
from dispatch.project import service as project_service

from .models import Term, TermCreate, TermUpdate


def get(*, db_session, term_id: int) -> Term | None:
    return db_session.query(Term).filter(Term.id == term_id).first()


def get_by_text(*, db_session, text: str) -> Term | None:
    return db_session.query(Term).filter(Term.text == text).first()


def get_all(*, db_session, project_id: int):
    return db_session.query(Term).filter(Term.project_id == project_id)


def create(*, db_session, term_in: TermCreate) -> Term:
    project = project_service.get_by_name_or_raise(
        db_session=db_session, project_in=term_in.project
    )

    definitions = [
        definition_service.upsert(db_session=db_session, definition_in=d)
        for d in term_in.definitions
    ]

    term = Term(
        **term_in.dict(exclude={"definitions", "project"}), project=project, definitions=definitions
    )

    db_session.add(term)
    db_session.commit()
    return term


def update(*, db_session, term: Term, term_in: TermUpdate) -> Term:
    term_data = term.dict()

    # we only allow updates to definition associations
    definitions = [
        definition_service.upsert(db_session=db_session, definition_in=d)
        for d in term_in.definitions
    ]

    update_data = term_in.dict(exclude_unset=True, exclude={"definitions"})

    for field in term_data:
        if field in update_data:
            setattr(term, field, update_data[field])

    term.definitions = definitions

    db_session.commit()
    return term


def update_or_create(*, db_session, term_in: TermCreate) -> Term:
    q = db_session.query(Term).filter(Term.text == term_in.text)

    instance = q.first()

    if instance:
        return update(db_session=db_session, term=instance, term_in=term_in)

    return create(db_session=db_session, term_in=term_in)


def get_or_create(*, db_session, term_in) -> Term:
    if term_in.id:
        q = db_session.query(Term).filter(Term.id == term_in.id)
    else:
        q = db_session.query(Term).filter_by(**term_in.dict(exclude={"definitions", "id"}))

    instance = q.first()
    if instance:
        return instance

    return create(db_session=db_session, term_in=term_in)


def delete(*, db_session, term_id: int):
    term = db_session.query(Term).filter(Term.id == term_id).first()
    term.definitions = []
    db_session.delete(term)
    db_session.commit()
