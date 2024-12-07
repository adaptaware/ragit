"""Exposes commonly used functions."""

import enum
import json
import os
import pathlib
import shutil
import yaml

_CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
_TESTING_DATA_DIR = os.path.join(_CURRENT_DIR, "testing_data")
_DEFAULT_DB_NAME = "dummy"


class VectorDbProviderEnum(enum.Enum):
    """Enumerates the supported 3rd parties for vector db storage.

    This enum allows us to store the embeddings in any vector database
    assuming that our code base has a wrapper to it.
    """

    MILVUS = 1
    CHROMA = 2


def make_local_connection_string(db_name=None):
    """Makes a connection string to use with the local postgres database.

    :param str db_name: The name of the database to use.

    :return: The connection string for the postgresql.
    :rtype: str
    """
    db_name = db_name or _DEFAULT_DB_NAME

    if running_inside_docker_container():
        user = os.environ.get("POSTGRES_USER")
        password = os.environ.get("POSTGRES_PASSWORD")
        host = os.environ.get("POSTGRES_HOST")
        port = os.environ.get("POSTGRES_PORT")
    else:
        user = "myuser"
        password = "password"
        host = "localhost"
        port = 5432

    conn_str = f"postgres://{user}:{password}@{host}:{port}/{db_name}"
    return conn_str


def get_rag_db_schema():
    """Returns the schema of the RAG database.

    By default the db schema of the RAG database exists under the following
    directory: ./impl/db_schema.sql

    :returns: The schema of the database.
    :rtype: str
    """
    fullpath = os.path.join(_CURRENT_DIR, "impl", "db_schema.sql")
    with open(fullpath) as fin:
        return fin.read()


def get_home_dir():
    """Returns the home directory for the current user.

    :return: The home directory for the current user.
    :rtype: str
    """
    return pathlib.Path.home()


def get_shared_directory():
    """Returns the directory which is used as the root for all collections.

    :return: The directory which is used as the root for all collections.
    :rtype: str
    """
    shared_dir = os.path.join(get_home_dir(), _SHARED_DIR)
    return shared_dir


def get_testing_output_dir(relative_path, wipe_out=False):
    """Returns a directory containing temporary output used for testing.

    As an example of what can go to this directory you can think of a
    vector database that is used for testing purposes or whatever else
    that might not be need to be stored.

    :param str relative_path: The path that is relative to the top level
    testing directory.

    :param bool wipe_out: If True, then whatever already exists under
    the relative path will be deleted and it will start with a clean state.

    :return: A string pointing to a directory containing testing output.
    :rtype: str

    :raises NotADirectoryError: the passed in relative_path is pointing
    to an exising file (not a directory).

    :raises: OSError: OS related error when creating or deleting the directory.
    """
    output_dir = os.path.join(get_home_dir(), "testing_output")

    create_directory_if_not_exists(output_dir)

    fullpath = os.path.join(output_dir, relative_path)

    # If pointing to a file raise an exception.
    if os.path.isfile(fullpath):
        raise NotADirectoryError

    # If the directory already exists delete it if wipe_out is set.
    if os.path.isdir(fullpath) and wipe_out:
        shutil.rmtree(fullpath)
        os.makedirs(fullpath)

    # If the output directory does not exist then create it.
    if not os.path.isdir(fullpath):
        os.makedirs(fullpath)

    return fullpath


def init_settings():
    """Initializes the project's settings.

    Tries to load the settings from the corresponding file under the
    home directory.  If the file is not available then it assumes that
    it is running within a docker container meaning that the settings
    must already be available.

    Before it exits, verifies that the OPENAI_API_KEY is available.

    :raises: ValueError, FileNotFoundError
    """
    if not running_inside_docker_container():
        filepath = os.path.join(get_home_dir(), "settings.json")
        with open(filepath) as fin:
            settings = json.load(fin)
            for k, v in settings.items():
                os.environ[k] = v

    # At this point the OPENAI_API_KEY environment value must exist.
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError(
            "OPENAI_API_KEY is not available. You need to either place it "
            "in the settings.json file under the home directory or to "
            "manually add it to the environment settings."
        )

    # At this point the VECTOR_DB_PROVIDER environment value must exist; just
    # try to get it, if it is missing an exception will be raised.
    _ = get_vector_db_provider()


def get_vector_db_provider():
    """Returns the selected vector db provider.

    The vector db provider is set either in the ~/settings.json (if running
    locally) of in the .env (if running inside docker).

    :return: The selected vector db provider.
    :rtype: VectorDbProviderEnum

    :raises: ValueError
    """
    vector_db_provider = os.environ.get("VECTOR_DB_PROVIDER")
    vector_db_provider = vector_db_provider.strip()
    vector_db_provider = vector_db_provider.upper()
    if vector_db_provider == "MILVUS":
        return VectorDbProviderEnum.MILVUS
    elif vector_db_provider == "CHROMA":
        return VectorDbProviderEnum.CHROMA
    else:
        raise ValueError(
            "VECTOR_DB_PROVIDER is not valid. You need to either place it "
            "in the settings.json file under the home directory or to "
            "manually add it to the environment settings. The Valid values "
            f" are {str(_SUPPORTED_VECTOR_DB_PROVIDERS)}"
        )


def get_testing_data_directory():
    """Returns the directory holding the data files to use for samples.

    :return: The directory containing the data files for sample programs.
    :rtype: str
    """
    return _TESTING_DATA_DIR


class MyGenAIException(Exception):
    """Generic MyGenAI exception."""


def handle_exceptions(foo):
    """Decorator to handle exceptions and customize it."""

    def inner(*args, **kwargs):
        """The inner function of the decorator."""
        try:
            return foo(*args, **kwargs)
        except Exception as ex:
            raise MyGenAIException(str(ex)) from ex

    return inner


class Configuration:
    """Holds the configuration that is loaded from a yaml file.

    :ivar _settings: The configuration instance.
    """

    _settings = None

    def __init__(self, fullpath):
        """Loads the configuration from a yaml file.

        :param str fullpath: The full path to the configuration yaml file.
        """
        with open(fullpath, 'r') as f:
            self._settings = yaml.safe_load(f)

    @property
    def settings(self):
        """Returns the configuration settings object."""
        return self._settings


def create_directory_if_not_exists(fullpath):
    """Creates the passed in directory if it doesn't.

    :param str fullpath: The full path to the directory to create.

    :raises NotADirectoryError: The full path is pointing to an
    existing file instead of a directory.
    """
    # If pointing to a file raise an exception.
    if os.path.isfile(fullpath):
        raise NotADirectoryError
    # If the base output directory does not exist then create it.
    if not os.path.isdir(fullpath):
        os.makedirs(fullpath)


def running_inside_docker_container():
    """Checks if the application is running insider docker.

    :returns: True if the application is running inside a docker container.
    :rtype: bool
    """
    return bool(os.path.exists('/.dockerenv'))


# Whatever follows this line is private to the module and should not be
# used from the outside.

_SHARED_DIR = "ragit-data"

# The VECTOR_DB_PROVIDER string that is set in the settings file
# or the .env (in the case of running inside docker) must match one
# of the supported providers.
_SUPPORTED_VECTOR_DB_PROVIDERS = [
    "MILVUS",
    "CHROME"
]
