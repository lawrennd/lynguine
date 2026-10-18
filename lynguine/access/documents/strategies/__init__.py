"""Built-in document segment strategies (CIP-0013).

Code strategies live as modules here; YAML strategies are ``*.yml`` files
loaded via :mod:`lynguine.access.documents.strategies.loader`.
"""

from .docx_chatbot_v1 import DocxChatbotV1
from .docx_workshop_v1 import DocxWorkshopV1
from .loader import YamlStrategy, load_strategy_yaml
from .pmlr_references_v1 import PmlrReferencesV1, ReferencesRegionNotFoundError
from .pub_dialogue_v1 import PubDialogueV1

__all__ = [
    "DocxChatbotV1",
    "DocxWorkshopV1",
    "PubDialogueV1",
    "PmlrReferencesV1",
    "ReferencesRegionNotFoundError",
    "YamlStrategy",
    "load_strategy_yaml",
]
