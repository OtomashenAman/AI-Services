from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle
import logging
from typing import List
from fastapi.requests import Request
from pydantic import PrivateAttr

from src.services.shared.data_base.storage_context import create_postgres_session
from src.services.ingestion.models import QAPair

logger = logging.getLogger(__name__)
class TenantFilterPostprocessor(BaseNodePostprocessor):
    """
    A postprocessor that filters nodes based on the tenant ID.

    This postprocessor ensures that only nodes belonging to the current tenant
    are returned after retrieval. It uses the tenant ID set in the settings.
    """

    model_config = {"arbitrary_types_allowed": True}  # <- this line is crucial
    def __init__(self, request: Request, **kwargs):
        super().__init__(**kwargs)  # required if llama_index expects pydantic init
        self._req = request  # safe to assign now


    def _postprocess_nodes(self, nodes: List[NodeWithScore], query_bundle: QueryBundle) -> List[NodeWithScore]:
        """
        Filters nodes to include only those that match the current tenant ID.

        Args:
            nodes (List[NodeWithScore]): The list of nodes retrieved.
            query_bundle (QueryBundle): The query bundle containing metadata.

        Returns:
            List[NodeWithScore]: Filtered list of nodes for the current tenant.
        """
        user_type = self._req.state.user_type
        if user_type is None:
            logger.warning("Tenant ID is not set in the request context. Returning all nodes.")
            return None
        filtered_nodes = [node for node in nodes if node.metadata.get("user_type") == user_type]
        logger.info("Filtered %d nodes for tenant ID '%s'", len(filtered_nodes), user_type)
        return filtered_nodes

class QA_dataadditionPostprocessor(BaseNodePostprocessor):
    """
    A postprocessor that adds metadata to nodes for Q&A data enrichment.
    """

    def _postprocess_nodes(self, nodes: List[NodeWithScore], query_bundle: QueryBundle) -> List[NodeWithScore]:
        logger.info("Adding metadata to nodes for Q&A data addition...")
        session = create_postgres_session()
        try:
            for node in nodes:
                try:
                    user_type = str(node.metadata.get('user_type'))
                    doc_id = int(node.metadata.get('doc_id'))

                    qa_entry = session.query(QAPair).filter_by(id=int(doc_id), user_type=str(user_type)).first()

                    if not qa_entry:
                        logger.warning("No QAPair found for doc_id=%s, user_type=%s", doc_id, user_type)
                        continue

                    node.metadata.update({
                        "answer": qa_entry.answer or "Answer not available/given"
                    })
                    logger.debug(f"Queryed answer for node with doc_id={doc_id}, user_type={user_type}: {node.metadata['answer']}")

                except Exception as node_err:
                    logger.exception("Error processing node metadata: %s", node_err)
        finally:
            session.close()

        return nodes