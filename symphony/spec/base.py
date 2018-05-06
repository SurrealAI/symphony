"""
All experiments, processes, and process_groups extend from this base class
"""
import benedict.data_format as df


class BaseSpec:
    def __init__(self, name):
        self.name = name

    def dump_dict(self):
        raise NotImplementedError

    @classmethod
    def load_dict(cls, data):
        raise NotImplementedError

    # ---------------- derived JSON/YAML methods -----------------
    @classmethod
    def load_json_file(cls, file_path, **loader_kwargs):
        return cls(df.load_json_file(file_path, **loader_kwargs))

    @classmethod
    def load_json_str(cls, string, **loader_kwargs):
        return cls(df.load_json_str(string, **loader_kwargs))

    @classmethod
    def load_yaml_file(cls, file_path, **loader_kwargs):
        return cls(df.load_yaml_file(file_path, **loader_kwargs))

    @classmethod
    def load_yaml_str(cls, string, **loader_kwargs):
        return cls(df.load_yaml_str(string, **loader_kwargs))

    @classmethod
    def load_file(cls, file_path, **loader_kwargs):
        """
        Args:
            file_path: JSON or YAML loader depends on the file extension

        Raises:
            IOError: if extension is not ".json", ".yml", or ".yaml"
        """
        return cls(df.load_file(file_path, **loader_kwargs))

    def dump_json_file(self, file_path, **dumper_kwargs):
        df.dump_json_file(self.dump_dict(), file_path, **dumper_kwargs)

    def dump_json_str(self, **dumper_kwargs):
        """Returns: string"""
        return df.dump_json_str(self.dump_dict(), **dumper_kwargs)

    def dump_yaml_file(self, file_path, **dumper_kwargs):
        df.dump_yaml_file(self.dump_dict(), file_path, **dumper_kwargs)

    def dump_yaml_str(self, **dumper_kwargs):
        """Returns: string"""
        return df.dump_yaml_str(self.dump_dict(), **dumper_kwargs)

    def dump_file(self, file_path, **dumper_kwargs):
        """
        Args:
            file_path: JSON or YAML loader depends on the file extension

        Raises:
            IOError: if extension is not ".json", ".yml", or ".yaml"
        """
        df.dump_file(self.dump_dict(), file_path, **dumper_kwargs)
