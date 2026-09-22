
import importlib.util

class MethodLoader:
    """Substitui download_a_single_method / download_many_methods /
    download_combining_and_beamforming_methods por UMA implementação,
    com pareamento explícito em vez de depender da ordem de dict.keys().
    """
 
    @staticmethod
    def load(module_path: str, class_name: str):
        spec = importlib.util.spec_from_file_location("modulo_dinamico", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, class_name)
 
    @classmethod
    def load_named(cls, parameters: dict, names: list[str]) -> dict:
        """Carrega várias técnicas a partir de um dict de parâmetros, usando
        pares explícitos '<name>_module_path' / '<name>_method_class' em vez
        de casar listas filtradas por sufixo (que é frágil e implícito).
        """
        loaded = {}
        for name in names:
            path = parameters[f"{name}_module_path"]
            print(path)
            class_name = parameters[f"{name}_method_class"]
            loaded[name] = cls.load(path, class_name)
        return loaded
