# Methods to provide host-port information to containers/processes
import os
import json


class AddressDeclarationError(Exception):
    pass


class AddressAPI(object):
    """
    Class that manages network addresses
    Must be called in a Symphony managed process: Symphony would provide the correct
    Environment variables
    """
    def __init__(self):
        """
        Setup internal data / connection
        """
        self.role = os.environ['SYMPHONY_ROLE']
        pass

    def request(self, service_name):
        """
        Returns host-port to the process requesting the service named <service_name>
        Args:
            @service_name: the name of the service. (Declared to symphony before launch)
        Raises AddressDeclarationError if data is not present
        """
        pass

    def provide(self, service_name):
        """
        Returns host-port to the process providing the service named <service_name>
        Args:
            @service_name: the name of the service. (Declared to symphony before launch)
        Raises AddressDeclarationError if data is not present
        """
        pass


class AddressBookService():
    """
    Datastructure holding address information using address book
    It also keeps track of whether its data is used: (i.e. the decalred port is being claimed)
    """
    def __init__(self, service_name, process_role, verbose=False,
                 provider_host=None, provider_port=None,
                 requester_host=None, requester_port=None):
        """
        Args:
            @service_name: name of the service (for reporting purposes)
            @process_role: role of the current process (for reporting purposes)
            @verbose: Report successful request/provide calls
            @provider_host, @provider_port: address to use for provider 
                                            None if the service is not needed for this process
            @requester_host, @requester_port: address to use for requester
                                            None if the service is not needed for this process
        """
        self.provider_host = provider_host
        self.provider_port = provider_port
        self.requester_host = requester_host
        self.requester_port = requester_port

        self.requested = False
        self.provided = False
        
        self.service_name = service_name
        self.process_role = process_role
        self.verbose = verbose

    def request(self):
        if self.requester_host is None or self.requester_port is None:
            message = '[Error]: Service {} is requested unexpectedly in {}'
            message = message.format(self.service_name,self.process_role)
            raise AddressDeclarationError(message)
        self.requested = True # We don't raise any issues about requesting a service more than once
        if self.verbose:
            message = '[Info]: Service {} is requested by {}. Host: {} | Port: {}'
            message = message.format(self.service_name, self.process_role,
                                    self.requester_host, self.requester_port)
            print(message)
        return self.requester_host, self.requester_port

    def provide(self):
        if self.provider_host is None or self.provider_port is None:
            message = '[Error]: Service {} is provided unexpectedly in {}'
            message = message.format(self.service_name, self.process_role)
            raise AddressDeclarationError(message)
        if self.provided:
            message = '[Warning]: Service {} is provided twice in {}'
            message = message.format(self.service_name, self.process_role)
            print(message)
        self.provided = True # We don't raise any issues about requesting a service more than once
        if self.verbose:
            message = '[Info]: Service {} is requested by {}. Host: {} | Port: {}'
            message = message.format(self.service_name, self.process_role,
                                    self.provider_host, self.provider_port)
            print(message)
        return self.provider_host, self.provider_port


class AddressBook(AddressAPI):
    """
    Collects address information using a json provided as environment variable by
    symphony scheduler
    Json format:
        {
            services: [{}, {}]
        }
    Each service must have 'name'. It can have/not have ('provider_host', 'provider_host')
    ('requester_host, requester_port')
    """
    def __init__(self, verbose=False):
        super().__init__()
        self.verbose = verbose

        self.services = self.parse(os.environ['SYMPHONY_AB_DATA'])

    def parse(self, data):
        services = {}
        data = json.loads(data)
        entries = data['services']
        for entry in entries:
            if 'provider_host' in entry:
                provider_host = entry['provider_host']
                provider_port = int(entry['provider_port'])
            else:
                provider_host = None
                provider_port = None
            if 'requester_host' in entry:
                requester_host = entry['requester_host']
                requester_port = int(entry['requester_port'])
            else:
                requester_host = None
                requester_port = None
            services[entry['name']] = AddressBookService( service_name=entry['name'], 
                process_role=self.role, verbose=self.verbose, 
                provider_host=provider_host, provider_port=provider_port, 
                requester_host=requester_host, requester_port=requester_port)
        return services

    def request(self, service_name):
        if service_name in self.services:
            return self.services[service_name].request()
        else:
            message = '[Error]: Service {} is requested unexpectedly in {}'
            message = message.format(service_name, self.role)
            raise AddressDeclarationError(message)

    def provide(self, service_name):
        if service_name in self.services:
            return self.services[service_name].provide()
        else:
            message = '[Error]: Service {} is provided unexpectedly in {}'
            message = message.format(service_name, self.role)
            raise AddressDeclarationError(message)


