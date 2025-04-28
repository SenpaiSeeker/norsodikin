class YamlHandler(__import__("nsdev").AnsiColors):
    def __init__(self, filePath):
        self.yaml = __import__("yaml")
        self.SimpleNamespace = __import__("types").SimpleNamespace
        super().__init__()

    def loadAndConvert(self, filePath):
        try:
            with open(filePath, "r") as file:
                rawData = self.yaml.safe_load(file)
                return self._convertToNamespace(rawData)
        except FileNotFoundError:
            print(f"{self.YELLOW}File {self.LIGHT_CYAN}'{self.filePath}' {self.RED}tidak ditemukan.{self.RESET}")
        except self.yaml.YAMLError as e:
            print(f"{self.RED}Kesalahan saat memproses file YAML: {e}{self.RESET}")
        return None

    def _convertToNamespace(self, data):
        if isinstance(data, dict):
            return self.SimpleNamespace(**{k: self._convertToNamespace(v) for k, v in data.items()})
        elif isinstance(data, list):
            return [self._convertToNamespace(item) for item in data]
        else:
            return data
