from __future__ import annotations
from type_annotations import Entity


async def resolve_entity(client, target: str) -> Entity | None:
    """Resolve a target (id or username) to an entity.

    Minimal, backward-compatible behavior: try numeric id first, then `get_entity`.
    """
    if target is None:
        return None

    entity: Entity | None = None
    # try numeric id
    target_id: int | None = None
    try:
        target_id = int(str(target))
    except Exception:
        target_id = None

    if target_id is not None:
        entity = await client.get_entity(target_id)

    if entity is None:
        try:
            entity = await client.get_entity(target)
        except Exception as e:
            print('Failed to get entity for target:', target, 'Error:', e)
            return None

    return entity
