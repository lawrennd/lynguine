"""Built-in document segment strategies (CIP-0013)."""

from .docx_chatbot_v1 import DocxChatbotV1
from .docx_workshop_v1 import DocxWorkshopV1
from .pmlr_references_v1 import PmlrReferencesV1, ReferencesRegionNotFoundError
from .pub_dialogue_v1 import PubDialogueV1

__all__ = [
    "DocxChatbotV1",
    "DocxWorkshopV1",
    "PubDialogueV1",
    "PmlrReferencesV1",
    "ReferencesRegionNotFoundError",
]
