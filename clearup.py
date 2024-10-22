import os
import logging

import boto3
from botocore.client import Config

from pyatlan.client.atlan import AtlanClient
from pyatlan.model.assets import Connection, S3Bucket, S3Object, Process
from pyatlan.model.enums import AtlanConnectorType
from pyatlan.errors import AtlanError, NotFoundError
from pyatlan.model.fluent_search import FluentSearch, CompoundQuery


class AtlanS3Lineage:
    """
    A class to manage S3 lineage in Atlan.
    """
    def __init__(self):
        """
        Initializes the AtlanS3Lineage and the Atlan client.
        """

        # Configure logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        try:
            self.client = AtlanClient(
                base_url=os.environ.get("ATLAN_BASE_URL"),
                api_key=os.environ.get("ATLAN_API_KEY"),
            )
            logging.info("Atlan client initialized")

        except AtlanError as e:
            logging.error(f"Atlan API Error: {e}")

        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")

## Delete Lineages

    def get_connection_qualified_name(self, connection_name: str, connector_type: AtlanConnectorType) -> str | None:
            """
            Retrieves the connection qualified name for a given connection name.

            Args:
                connection_name (str): The name of the connection.
                connector_type (AtlanConnectorType): The type of the connection.

            Returns:
                str | None: The connection qualified name if found, otherwise None.
            """
            try:
                connections = self.client.asset.find_connections_by_name(
                    name=connection_name,
                    connector_type=connector_type,
                    attributes=[]
                )
                if connections:
                    return connections[0].qualified_name
                else:
                    return None
            except AtlanError as e:
                logging.error(f"Atlan API Error retrieving connection qualified name: {e}")
                return None            
        
    def fetch_process_guid_by_connections(self, connection_qualified_names: list[str]) -> list[str]:
            """
            Fetches the GUIDs of processes under the specified list of connection_qualified_names.

            Args:
                connection_qualified_names (list[str]): A list of qualified names of the connections to search within.

            Returns:
                list[str]: A list of GUIDs of the processes found, otherwise an empty list.
            """
            process_list = []  # Initialize an empty list to store process GUIDs

            try:
                for connection_qualified_name in connection_qualified_names:
                    # Build the FluentSearch request to look for Process assets within the connection
                    request = (
                        FluentSearch()
                        .where(CompoundQuery.asset_type(Process))  # Searching for Process asset type
                        .where(CompoundQuery.active_assets())      # Active assets only
                        .where(Process.CONNECTION_QUALIFIED_NAME.eq(connection_qualified_name))
                        .page_size(1000)  # Adjust page size if needed
                    ).to_request()

                    # Execute the search
                    results = self.client.asset.search(request)

                    # Loop through results and append each process's GUID to process_list
                    for result in results:
                        if isinstance(result, Process):
                            process_list.append(result.guid)  # Add process GUID to the list

                return process_list  # Return the list of process GUIDs

            except AtlanError as e:
                logging.error(f"Atlan API Error while searching for processes: {e}")
                return process_list  # Return an empty list in case of error        
            

    # Delete S3Objects

    def fetch_s3_objects_in_connection(self, connection_qualified_name: str) -> list[str]:
            """
            Fetches all S3 objects within the specified connection.

            Args:
                connection_qualified_name (str): The qualified name of the connection to search within.

            Returns:
                list[str]: A list of qualified names of the S3 objects found, otherwise an empty list.
            """
            s3_object_list = []  # Initialize an empty list to store S3 object qualified names

            try:
                # Build the FluentSearch request to look for S3Object assets within the connection
                request = (
                    FluentSearch()
                    .where(CompoundQuery.asset_type(S3Object))  # Searching for S3Object asset type
                    .where(CompoundQuery.active_assets())       # Only active assets
                    .where(S3Object.CONNECTION_QUALIFIED_NAME.eq(connection_qualified_name))  # Filter by connection
                    .page_size(1000)  # Adjust page size if needed
                ).to_request()

                # Execute the search
                results = self.client.asset.search(request)

                # Loop through results and append each S3 object's qualified name to s3_object_list
                for result in results:
                    if isinstance(result, S3Object):
                        s3_object_list.append(result.guid)  # Add the qualified name of the S3 object

                return s3_object_list  # Return the list of S3 object qualified names

            except AtlanError as e:
                logging.error(f"Atlan API Error fetching S3 objects: {e}")
                return s3_object_list  # Return an empty list in case of error

    ## Delete S3 Bucket

    def fetch_buckets_in_connection(self, connection_qualified_name: str) -> list[str]:
            """
            Fetches all buckets within the specified connection.

            Args:
                connection_qualified_name (str): The qualified name of the connection to search within.

            Returns:
                list[str]: A list of qualified names of the buckets found, otherwise an empty list.
            """
            bucket_list = []  # Initialize an empty list to store S3 object qualified names

            try:
                # Build the FluentSearch request to look for S3Object assets within the connection
                request = (
                    FluentSearch()
                    .where(CompoundQuery.asset_type(S3Bucket))  # Searching for S3Object asset type
                    .where(CompoundQuery.active_assets())       # Only active assets
                    .where(S3Object.CONNECTION_QUALIFIED_NAME.eq(connection_qualified_name))  # Filter by connection
                    .page_size(1000)  # Adjust page size if needed
                ).to_request()

                # Execute the search
                results = self.client.asset.search(request)

                # Loop through results and append each S3 object's qualified name to s3_object_list
                for result in results:
                    if isinstance(result, S3Bucket):
                        bucket_list.append(result.guid)  # Add the qualified name of the S3 object

                return bucket_list  # Return the list of S3 object qualified names

            except AtlanError as e:
                logging.error(f"Atlan API Error fetching S3 objects: {e}")
                return bucket_list  # Return an empty list in case of error




if __name__ == "__main__":
    lineage_manager = AtlanS3Lineage()
    connection_list = []

    connection_name = "postgres-sv"
    connector_type = AtlanConnectorType.POSTGRES  # Set the connector type to POSTGRES
    Postgresql_connection_qualified_name = (
        lineage_manager.get_connection_qualified_name(
            connection_name, connector_type
        )
    )

    if Postgresql_connection_qualified_name:
        connection_list.append(Postgresql_connection_qualified_name)

    connection_name = "aws-s3-connection-tech-challenge-sv"
    connector_type = AtlanConnectorType.S3  # Set the connector type to S3
    s3_connection_qualified_name = (
        lineage_manager.get_connection_qualified_name(
            connection_name, connector_type
        )
    )

    if s3_connection_qualified_name:
        connection_list.append(s3_connection_qualified_name)

    connection_name = "snowflake-sv"
    connector_type = AtlanConnectorType.SNOWFLAKE  # Set the connector type to SNOWFLAKE
    snowflake_connection_qualified_name = (
        lineage_manager.get_connection_qualified_name(
            connection_name, connector_type
        )
    )

    if snowflake_connection_qualified_name:
        connection_list.append(snowflake_connection_qualified_name)

    lineage_list = lineage_manager.fetch_process_guid_by_connections(
        connection_list
    )

    response = lineage_manager.client.asset.purge_by_guid(lineage_list)
    if deleted := response.assets_deleted(
        asset_type=Process
    ):  # Check for deleted Process assets
        term = deleted[0]
        logging.info(f"Process asset deleted: {term.qualified_name}")


    connection_name = "aws-s3-connection-tech-challenge-sv"
    connector_type = AtlanConnectorType.S3    # Set the connector type to S3
    s3_connection_qualified_name = lineage_manager.get_connection_qualified_name(connection_name, connector_type)

    s3objects_list = lineage_manager.fetch_s3_objects_in_connection(s3_connection_qualified_name)

    response = lineage_manager.client.asset.purge_by_guid(s3objects_list)
    if deleted := response.assets_deleted(asset_type=S3Object):  # 
        term = deleted[0]

    
    s3bucket_list = lineage_manager.fetch_buckets_in_connection(s3_connection_qualified_name)

    response = lineage_manager.client.asset.purge_by_guid(s3bucket_list)
    if deleted := response.assets_deleted(asset_type=S3Bucket):  # 
        term = deleted[0]


    connection_guid = lineage_manager.client.asset.get_by_qualified_name(
        asset_type=Connection,  # 
        qualified_name=s3_connection_qualified_name
    ).guid

    response = lineage_manager.client.asset.purge_by_guid(connection_guid)
    if deleted := response.assets_deleted(asset_type=Connection):  # 
        term = deleted[0]
        logging.info("Deleted successfully");