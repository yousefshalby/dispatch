import logging
from sqlalchemy.orm import Session
from dispatch.case.messaging import send_entity_update_notification
from dispatch.entity_type.models import EntityScopeEnum
from dispatch.signal.models import SignalInstance
from dispatch.entity_type import service as entity_type_service

from dispatch.entity_type.models import EntityType
from dispatch.entity import service as entity_service

log = logging.getLogger(__file__)


def recalculate_entity_flow(
    db_session: Session,
    entity_type: EntityType,
    signal_instance: SignalInstance,
):
    """
    Recalculate entity findings for historical signals based on a newly associated EntityType.

    Args:
        db_session (Session): The database session to use for entity creation.
        new_entity_type (EntityType): The newly created EntityType to associate with signals.
    """
    # fetch `all` entities that should be associated with all signal definitions
    entity_types = entity_type_service.get_all(
        db_session=db_session, scope=EntityScopeEnum.all
    ).all()
    entity_types = signal_instance.signal.entity_types.append(entity_type)

    if entity_types:
        entities = entity_service.find_entities(
            db_session=db_session,
            signal_instance=signal_instance,
            entity_types=entity_types,
        )
        signal_instance.entities = entities
        db_session.commit()

    try:
        send_entity_update_notification(
            db_session=db_session,
            entity_type=entity_type,
            case=signal_instance.case,
        )
    except Exception as e:
        log.warning(f"Failed to send entity update notification: {e}")

    return signal_instance
