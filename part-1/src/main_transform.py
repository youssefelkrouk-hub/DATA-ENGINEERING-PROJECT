from util.config_handler import ConfigHandler
from util.data_transformer import DataTransformer

def transform():
    config_handler = ConfigHandler()
    transformer = DataTransformer(config_handler)
    transformer.transform_and_save()


if __name__ == "__main__":
    transform()