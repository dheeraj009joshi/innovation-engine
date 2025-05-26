import uuid
from azure.storage.blob import BlobServiceClient

AZURE_STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=printxd;AccountKey=CaL/3SmhK8iKVM02i/cIN1VgE3058lyxRnCxeRd2J1k/9Ay6I67GC2CMnW//lJhNl+71WwxYXHnC+AStkbW1Jg==;EndpointSuffix=core.windows.net"
CONTAINER_NAME = "mf2"

blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

def upload_to_azure(file):
    try:
        blob_name = str(uuid.uuid4()) + "_" + file.name
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=blob_name)

        # THIS IS THE CRITICAL LINE:
        blob_client.upload_blob(file.getvalue(), overwrite=True)

        return blob_client.url
    except Exception as e:
        print("❌ Azure upload failed:", str(e))
        raise
