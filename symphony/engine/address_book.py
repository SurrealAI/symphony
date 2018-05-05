

class AddressBook(object):
    def __init__(self, di=None):
        self.entries = {}
        if di is not None:
            self.entries = di

    def add_entry(self, name, host, port):
        entry = self.entries.get(name, {})
        entry['host'] = host
        entry['port'] = port
        self.entries[name] = entry

    def dump(self):
        output = {}
        for name in self.entries:
            entry = self.entries[name]
            formatted_name = self.format_name(name)
            output['SYMPH_{}_HOST'.format(formatted_name)] = entry['host']
            output['SYMPH_{}_PORT'.format(formatted_name)] = entry['port']
        return output

    def format_name(self, name):
        formatted_name = name.upper()
        formatted_name = formatted_name.replace('-', '_')
        return formatted_name

    # Add serialize3