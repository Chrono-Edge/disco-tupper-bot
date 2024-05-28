from exceptions.exceptions import ConfigurationError


def check_config_for_null(**kwargs):
    for var_name, var_value in kwargs.items():
        if var_value is None:
            raise ConfigurationError(
                f"You did not specify {var_name} in the configuration file.")
