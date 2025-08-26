from types import SimpleNamespace

import yaml

from .colorize import AnsiColors

class YamlHandler(AnsiColors):
    def __init__(self):
        super().__init__()

    def loadAndConvert(self, filePath):
        try:
            with open(filePath, "r", encoding="utf-8") as file:
                rawData = yaml.safe_load(file)
                return self._convertToNamespace(rawData)
        except FileNotFoundError:
            print(f"{self.YELLOW}File {self.LIGHT_CYAN}'{filePath}' {self.RED}tidak ditemukan.{self.RESET}")
        except yaml.YAMLError as e:
            print(f"{self.YELLOW}Kesalahan saat memproses file YAML: {self.RED}{e}{self.RESET}")
        return None

    def _convertToNamespace(self, data):
        if isinstance(data, dict):
            string_keyed_dict = {str(k): self._convertToNamespace(v) for k, v in data.items()}
            return SimpleNamespace(**string_keyed_dict)
        elif isinstance(data, list):
            return [self._convertToNamespace(item) for item in data]
        else:
            return data
