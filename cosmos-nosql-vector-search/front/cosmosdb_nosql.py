from azure.cosmos import cosmos_client, diagnostics, exceptions, PartitionKey
import traceback, time

class CosmosDBNoSQLService:
    """
    This class is used to access a Cosmos DB NoSQL API account.
    """
    def __init__(self, opts):
        self._dbname = None
        self._dbproxy = None
        self._ctrproxy = None
        self._cname = None
        self.reset_record_diagnostics()
        url = opts['url']
        key = opts['key']
        if 'enable_query_metrics' in opts.keys():
            self._query_metrics = True
        else:
            self._query_metrics = False
        self._client = cosmos_client.CosmosClient(url, {'masterKey': key})

    def list_databases(self):
        """ Return the list of database names in the account. """
        self.reset_record_diagnostics()
        return list(self._client.list_databases())
    
    def set_db(self, dbname):
        """ Set the current database to the given dbname. """
        try:
            self.reset_record_diagnostics()
            self._dbname = dbname
            self._dbproxy = self._client.get_database_client(database=dbname)
        except Exception as excp:
            print(str(excp))
            print(traceback.format_exc())

        return self._dbproxy
        
    def create_db(self, dbname):
        """ Create database to the given dbname. """
        try:
            self.reset_record_diagnostics()
            self._dbname = dbname
            self._dbproxy = self._client.create_database(id=dbname)
        except exceptions.CosmosResourceExistsError:
            self.database = self.set_db(dbname)
        return self._dbproxy
    
    def list_containers(self):
        """ Return the list of container names in the current database. """
        self.reset_record_diagnostics()
        return list(self._dbproxy.list_containers())

    def create_container(self, dbname, cname, partition_key, throughput):
        """ Create a container in the current database. """
        try:
            self.reset_record_diagnostics()
            self._dbproxy = self.set_db(dbname)
            self._ctrproxy = self._dbproxy.create_container(
                id=cname,
                partition_key=PartitionKey(path=partition_key),
                offer_throughput=throughput,
                populate_query_metrics=self._query_metrics,
                response_hook=self._record_diagnostics)
            return self._ctrproxy
            # <class 'azure.cosmos.container.ContainerProxy'>
        except exceptions.CosmosResourceExistsError as excp:
            print(str(excp))
            print(traceback.format_exc())
            return self.set_container(cname)
        except Exception as excp2:
            print(str(excp2))
            print(traceback.format_exc())
            return None
    
    def create_or_replace_container(self, cname, partition_key, throughput):
        """ Create or replace a container in the current database. """
        try:
            existing_containers = self.list_containers()
            
            if cname in (x['id'] for x in existing_containers):
                # Container already exists, replace it
                return self.replace_container(cname, partition_key, throughput)
            else:
                # Container does not exist, create it
                return self.create_container(cname, partition_key, throughput)
        except Exception as excp:
            print(str(excp))
            print(traceback.format_exc())
            return None
        
    def create_container_no_throughput(self, cname, partition_key):
        """ Create a container in the current database. """
        try:
            self.reset_record_diagnostics()
            self._ctrproxy = self._dbproxy.create_container(
                id=cname,
                partition_key=PartitionKey(path=partition_key),
                populate_query_metrics=self._query_metrics,
                response_hook=self._record_diagnostics)
            return self._ctrproxy
            # <class 'azure.cosmos.container.ContainerProxy'>
        except exceptions.CosmosResourceExistsError as excp:
            print(str(excp))
            print(traceback.format_exc())
            return self.set_container(cname)
        except Exception as excp2:
            print(str(excp2))
            print(traceback.format_exc())
            return None

    def create_or_replace_container_no_throughput(self, cname, partition_key):
        """ Create or replace a container in the current database. """
        try:
            existing_containers = self.list_containers()
            
            if cname in (x['id'] for x in existing_containers):
                # Container already exists, replace it
                return self.replace_container(cname, partition_key)
            else:
                # Container does not exist, create it
                return self.create_container_no_throughput(cname, partition_key)
        except Exception as excp:
            print(str(excp))
            print(traceback.format_exc())
            return None

    def replace_container(self, cname, partition_key):
        """ Replace the existing container with new settings. """
        try:
            existing_container = self.set_container(cname)
            
            if existing_container:
                self.reset_record_diagnostics()
                self._ctrproxy = existing_container.replace_container(
                    partition_key=PartitionKey(path=partition_key),
                    populate_query_metrics=self._query_metrics,
                    response_hook=self._record_diagnostics)
                return self._ctrproxy
            else:
                # Handle the case where the container does not exist
                return None
        except Exception as excp:
            print(str(excp))
            print(traceback.format_exc())
            return None
        
    def set_container(self, cname):
        """ Set the current container in the current database to the given cname. """
        self.reset_record_diagnostics()
        self._ctrproxy = self._dbproxy.get_container_client(cname)
        # <class 'azure.cosmos.container.ContainerProxy'>
        return self._ctrproxy

    def update_container_throughput(self, cname, throughput):
        """ Update the throughput of the given container. """
        self.reset_record_diagnostics()
        self.set_container(cname)
        offer = self._ctrproxy.replace_throughput(
            throughput=int(throughput),
            response_hook=self._record_diagnostics)
        return offer

    def get_container_offer(self, cname):
        """ Get the current offer (throughput) for the given container. """
        self.reset_record_diagnostics()
        self.set_container(cname)
        offer = self._ctrproxy.read_offer(
            response_hook=self._record_diagnostics)
        # <class 'azure.cosmos.offer.Offer'>
        return offer

    def delete_container(self, cname):
        """ Delete the given container name in the current database. """
        try:
            self.reset_record_diagnostics()
            return self._dbproxy.delete_container(
                cname,
                populate_query_metrics=self._query_metrics,
                response_hook=self._record_diagnostics)
        except Exception as excp:
            print(str(excp))
            print(traceback.format_exc())
            return None

    def upsert_doc(self, doc):
        """ Upsert the given document in the current container. """
        try:
            self.reset_record_diagnostics()
            return self._ctrproxy.upsert_item(
                doc,
                populate_query_metrics=self._query_metrics,
                response_hook=self._record_diagnostics)
        except Exception as excp:
            print(str(excp))
            print(traceback.format_exc())
            return None

    def delete_doc(self, doc, doc_pk):
        """ Delete the given document in the current container. """
        try:
            self.reset_record_diagnostics()
            return self._ctrproxy.delete_item(
                doc,
                partition_key=doc_pk,
                populate_query_metrics=self._query_metrics,
                response_hook=self._record_diagnostics)
        except Exception as excp:
            print(str(excp))
            print(traceback.format_exc())
            return None

    def read_doc(self, cname, doc_id, doc_pk):
        """ Execute a point-read for container, document id, and partition key. """
        try:
            self.set_container(cname)
            self.reset_record_diagnostics()
            return self._ctrproxy.read_item(
                doc_id,
                partition_key=doc_pk,
                populate_query_metrics=self._query_metrics,
                response_hook=self._record_diagnostics)
        except Exception as excp:
            print(str(excp))
            print(traceback.format_exc())
            return None

    def query_container(self, cname, sql, xpartition, max_count):
        """ Execute a given SQL query of the given container name. """
        try:
            self.set_container(cname)
            self.reset_record_diagnostics()
            return self._ctrproxy.query_items(
                query=sql,
                enable_cross_partition_query=xpartition,
                max_item_count=max_count,
                populate_query_metrics=self._query_metrics,
                response_hook=self._record_diagnostics)
        except Exception as excp:
            print(str(excp))
            print(traceback.format_exc())
            return excp

    # Metrics and Diagnostics

    def enable_query_metrics(self):
        """ Return a boolean indicating whether query metrics are enabled. """
        self._query_metrics = True

    def disable_query_metrics(self):
        """ Set query metrics to False. """
        self._query_metrics = False

    def reset_record_diagnostics(self):
        """ Reset the record diagnostics in this object. """
        self._record_diagnostics = diagnostics.RecordDiagnostics()

    def print_record_diagnostics(self):
        """ Print the record diagnostics. """
        print(f'record_diagnostics: {self._record_diagnostics.headers}')
        print(str(type(self._record_diagnostics.headers)))
        keys = self._record_diagnostics.headers.keys()
        print(str(type(keys)))
        print(keys)
        for header in self._record_diagnostics.headers.items():
            print(header)
            print(str(type(header)))

    def record_diagnostics_headers_dict(self):
        """ Read and return the record diagnostics headers as a dictionary. """
        data = {}
        for header in self._record_diagnostics.headers.items():
            key, val = header  # unpack the header 2-tuple
            data[key] = val
        return data

    def print_last_request_charge(self):
        """ Print the last request charge and activity id. """
        charge = self.last_request_charge()
        activity = self.last_activity_id()
        print(f'last_request_charge: {charge} activity: {activity}')

    def last_request_charge(self):
        """ Return the last request charge in RUs, default to -1. """
        header = 'x-ms-request-charge'
        if header in self._record_diagnostics.headers:
            return self._record_diagnostics.headers[header]
        return -1

    def last_activity_id(self):
        """ Return the last diagnostics activity id, default to None. """
        header = 'x-ms-activity-id'
        if header in self._record_diagnostics.headers:
            return self._record_diagnostics.headers[header]
        return None

    def vector_search(self, query_vector, limit=5):
        """ Return the vector search results for the given query. """
        query = f"SELECT TOP {limit} c.title, c.ingredients, c.directions, c.link, c.NER, VectorDistance(c.embedding, {query_vector}) AS SimilarityScore FROM c ORDER BY VectorDistance(c.embedding, {query_vector})"
        parameters = None

        start_time = time.time()          

        docs = self._ctrproxy.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        )   

        recipes = []
        for doc in docs:
            recipes.append(doc)

        end_time = time.time()
        elapsed_time = end_time - start_time

        return recipes, elapsed_time