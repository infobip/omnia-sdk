from io import StringIO

from dotenv import dotenv_values


def read_environment_file(source: str | StringIO) -> dict:
        """
        Read environment variables from a file path or StringIO object.
        
        :param source: Path to the environment file or StringIO object containing environment data.
        :return: Dictionary of environment variables.
        """
        if isinstance(source, StringIO):
            # Reset position to beginning for StringIO objects
            source.seek(0)
            content = source.read()
            environment = dotenv_values(stream=StringIO(content))
        else:
            environment = dotenv_values(source)
        return environment
