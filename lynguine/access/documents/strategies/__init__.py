"""Built-in document segment strategies (CIP-0013)."""

from .pmlr_references_v1 import PmlrReferencesV1, ReferencesRegionNotFoundError
from .pub_dialogue_v1 import PubDialogueV1

__all__ = ["PubDialogueV1", "PmlrReferencesV1", "ReferencesRegionNotFoundError"]
