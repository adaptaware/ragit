"""Exposes a vector index db wrapper."""


import ragit.libs.common as common
import ragit.libs.impl.vdb_chroma as chroma_vector_db
import ragit.libs.impl.vdb_milvus as milvus_vector_db


def get_vector_db(fullpath, collection_name, dimension=1536):
    """Factory function to get a vector db instance.

    :param str fullpath: The full path to the file holding the vector db.
    :param str collection_name: The name of the collection.
    :param int dimension: The length of the embeddings vector.

    :return: An instance of the AbstractVectorDb class.
    :rtype: AbstractVectorDb

    :raises: ValueError
    """
    vector_db_provider = common.get_vector_db_provider()
    if vector_db_provider == common.VectorDbProviderEnum.MILVUS:
        return milvus_vector_db.MilvusVectorDb(
            fullpath, collection_name, dimension
        )
    elif vector_db_provider == common.VectorDbProviderEnum.CHROMA:
        return chroma_vector_db.ChromaVectorDb(
            fullpath, collection_name, dimension
        )

    raise ValueError("Unsupported vector db provider.")





