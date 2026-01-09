import sys
import os
import uuid

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
)
from dotenv import load_dotenv

load_dotenv()


from pengent.lib import get_logger

logger = get_logger(level=10)

from pengent.core.artifacts.artifact_service import (
    InMemoryArtifactService,
    StorageArtifactService,
)
from pengent.core.artifacts.artifact import ArtifactText,ArtifactBlob

session_id = os.getenv("SAMPLE_SESSION_ID")
user_id = os.getenv("SAMPLE_USER_ID", "example_user_001")

if not session_id:
    session_id = uuid.uuid4().hex


def example_artifact_save_and_load_inmemory():
    artifact_service = InMemoryArtifactService()
    artifact = ArtifactText(text="This is a sample text artifact.")
    # アーティファクトの保存
    version = artifact_service.save_artifact(
        user_id=user_id,
        session_id=session_id,
        filename="example_artifact.txt",
        artifact=artifact,
    )
    logger.info(f"Artifact saved with version: {version}")

    # アーティファクトの読み込み
    loaded_artifact = artifact_service.load_artifact(
        user_id=user_id,
        session_id=session_id,
        filename="example_artifact.txt",
        version=version,
    )
    logger.info(f"Loaded Artifact: {loaded_artifact}")
    if isinstance(loaded_artifact, ArtifactText):
        logger.info(f"Text: {loaded_artifact.text}")


def example_artifact_save_and_load_storage():
    artifact_service = StorageArtifactService()
    image_file = "example/utility/sample_data/sample.png"
    with open(image_file, "rb") as f:
        blob_data = f.read()
    
    artifact = ArtifactBlob(
        mime_type="image/png",
        blob=blob_data
    )

    # アーティファクトの保存
    version = artifact_service.save_artifact(
        user_id=user_id,
        session_id=session_id,
        filename="sample_png.png",
        artifact=artifact,
    )
    logger.info(f"Artifact saved with version: {version}")

    # アーティファクトの読み込み
    loaded_artifact = artifact_service.load_artifact(
        user_id=user_id,
        session_id=session_id,
        filename="example_artifact.txt",
        version=version,
    )
    logger.info(f"Loaded Artifact: {loaded_artifact}")
    if isinstance(loaded_artifact, ArtifactText):
        logger.info(f"Text: {loaded_artifact.text}")


if __name__ == "__main__":
    # example_artifact_save_and_load_inmemory()
    example_artifact_save_and_load_storage()
