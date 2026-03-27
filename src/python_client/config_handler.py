import os
import json

class Config(dict):
    def __init__(self, filepath: str = None):
        super().__init__()

        self.filepath = filepath
        if filepath:
            self.load(filepath)

    def save(self, filepath: str = None):
        # TODO save a backup of the old config file

        print(f"Saving config to '{self.filepath}'")

        # use existing path if none provided
        if not filepath:
            filepath = self.filepath

        with open(filepath, "w") as cfg_file:
            json.dump(self, cfg_file, indent=4)
            self.filepath = filepath

    def load(self, filepath: str):
        fullpath = os.path.abspath(filepath)
        print(f"Loading config from '{fullpath}'")
        with open(fullpath, "r") as cfg_file:
            self.clear()
            self.update(json.load(cfg_file))
            self.filepath = fullpath
