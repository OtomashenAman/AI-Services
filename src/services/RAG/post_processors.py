from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle
import logging
from typing import List
from fastapi.requests import Request
from pydantic import PrivateAttr

from src.services.shared.data_base.qa_sql_writer import create_postgres_session
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
        tenant_id = self._req.state.tenant_id
        if tenant_id is None:
            logger.warning("Tenant ID is not set in the request context. Returning all nodes.")
            return None
        filtered_nodes = [node for node in nodes if node.metadata.get("tenant_id") == tenant_id]
        logger.info("Filtered %d nodes for tenant ID '%s'", len(filtered_nodes), tenant_id)
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
                    tenant_id = int(node.metadata.get('tenant_id'))
                    doc_id = int(node.metadata.get('doc_id'))

                    qa_entry = session.query(QAPair).filter_by(id=int(doc_id), tenant_id=str(tenant_id)).first()

                    if not qa_entry:
                        logger.warning("No QAPair found for doc_id=%s, tenant_id=%s", doc_id, tenant_id)
                        continue

                    node.metadata.update({
                        "answer": qa_entry.answer or "Answer not available/given"
                    })
                    logger.debug(f"Queryed answer for node with doc_id={doc_id}, tenant_id={tenant_id}: {node.metadata['answer']}")

                except Exception as node_err:
                    logger.exception("Error processing node metadata: %s", node_err)
        finally:
            session.close()

        return nodes