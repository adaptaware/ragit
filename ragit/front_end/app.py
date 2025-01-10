#!/usr/bin/env python3
"""Exposes the Ragit Front End.

This module initializes an aiohttp based web server that serves different
front-end interfaces based on command line parameters.

Usage:
    python server.py <collection_name> [--admin]

Parameters:
collection_name (str):
    Mandatory. The name of the RAG (Retrieval-Augmented Generation) collection
    that must point to the corresponding vectorized database.

--admin (optional):
    If passed, regardless of case (e.g., 'ADMIN', 'admin'), the application
    will enable full administrative features on the front-end, including
    history and admin screens. If not passed, the application will default to
    only providing the chatbox interface.
"""

import dataclasses
import datetime
import functools
import logging
import os
import sys
import uuid

import aiohttp
import aiohttp.web as web
import jinja2
import jwt
import markdown

import ragit.libs.common as common
import ragit.libs.dbutil as dbutil
import ragit.libs.rag_mgr as rag_mgr
import ragit.libs.user_registry as user_registry

_JINJA_ENV = jinja2.Environment(
    loader=jinja2.PackageLoader(
        'templates',
        'templates'),
    autoescape=jinja2.select_autoescape(['html', 'xml'])
)

_CURR_DIR = os.path.dirname(os.path.realpath(__file__))
_PATH_TO_STATIC = os.path.join(_CURR_DIR, 'static')
_CONFIGURATION = common.Configuration(os.path.join(_CURR_DIR, 'config.yaml'))
_DEFAULT_PORT = 13131

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(_CONFIGURATION.settings["web_service"]["name"])

# Aliases.
UserRegistry = user_registry.UserRegistry


class AuthenticationError(Exception):
    """Authentication Error."""


class Globals:
    """Global variables holder.

    :cvar: RagManager rag_manager: The Rag Manager instance for the rag
    collection which is defined in the configuration file. It is instantiated
    once when the service is starting and remains in memory for the rest of
    the lifespan of the program.

    :cvar: str _secret_key:  The secret key that is used for authentication.

    :cvar: bool is_admin: True if the user is an admin; in this case he will
    have access to the full environment including the postgres database and
    the document file storage.
    """
    rag_manager = None
    _secret_key = str(uuid.uuid4())
    is_admin = False

    @classmethod
    def generate_token(cls, user_name, expiration_minutes=3600):
        """Creates a JSON Web Token (JWT) for the given user.

        :param str user_name: The user's username.
        :param int expiration_minutes: The token expiration in minutes.

        :return: The generated JWT token.
        :rtype: str
        """
        payload = {
            'username': user_name,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(
                minutes=expiration_minutes
            )
        }
        token = jwt.encode(payload, cls._secret_key, algorithm='HS256')
        return token

    @classmethod
    def validate_token(cls, token, user_name):
        """Validates the passed in token.

        :param str token: The token to validate.
        :param str user_name: The user name.
        """
        try:
            payload = jwt.decode(token, cls._secret_key, algorithms=['HS256'])
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as ex:
            raise AuthenticationError(str(ex)) from ex


def get_metrics():
    """Reports metrics for the active RAG collection.

    This function gathers two types of metrics:

    1. Document Processing Metrics:
       These metrics pertain to document that have been processed and inserted
       into the vectorization database. They are sourced from a PostgreSQL
       database corresponding to the specified collection name, ensuring
       synchronization between the documents, the database, and the vector
       database.

    2. Front-End Usage Metrics:
       These metrics reflect the usage of the front end. They are stored in an
       SQLite database, managed by the `UserRegistry` class. The metrics
       include user queries, responses received, and details about the RAG
       model. They also track the chunks utilized in each request and other
       relevant information.

    :return: A dictionary containing metrics as key-value pairs.
    :rtype: dict
    """
    collection_name = Globals.rag_manager.get_rag_collection_name()
    conn_str = common.make_local_connection_string(collection_name)
    dbutil.SimpleSQL.register_connection_string(conn_str)
    ragger = rag_mgr.RagManager(collection_name)
    metrics = {}
    with dbutil.SimpleSQL() as db:
        stats = ragger.get_metrics(db)
        for field in dataclasses.fields(stats):
            field_name = field.name
            if field_name.strip().lower() == 'full_path':
                continue
            field_value = getattr(stats, field_name)
            name = f"{field_name.replace('_', ' ').ljust(25, '.')}"
            metrics[name] = field_value
    return metrics


def _raw_headers_to_dict(raw_headers):
    """Converts raw headers to a dictionary."""
    d = {}
    for k, v in raw_headers:
        try:
            d[k.decode('utf-8')] = v.decode('utf-8')
        except Exception as ex:
            logger.exception(ex)
    return d


def web_handler(handler_func):
    """Wraps a handler function adding standard processing."""

    @functools.wraps(handler_func)
    async def _inner(self, request):
        """The decorator function."""
        try:
            raw_headers = _raw_headers_to_dict(request.raw_headers)
            real_ip = raw_headers.get("X-Real-IP")
            logger.info(f"Connected User IP: {real_ip}")
            return await handler_func(self, request)
        except web.HTTPFound:
            # must be a redirect..
            raise
        except Exception as ex:
            logger.exception(ex)
            raise aiohttp.web.HTTPInternalServerError()

    return _inner


class RagitLightHandler:
    """Implements the light handlers."""

    @web_handler
    async def main_page_handler(self, request):
        """Displays the main page.

        :param request: The web request.
        """
        try:
            auth_token = request.cookies.get('ragit_auth_token')
            user_name = request.cookies.get('user_name')
            Globals.validate_token(auth_token, user_name)
        except AuthenticationError:
            return web.HTTPFound('/login')
        else:
            template = _JINJA_ENV.get_template('ragit_light.html')
            collection_name = Globals.rag_manager.get_rag_collection_name()
            txt = template.render(
                host=request.host,
                collection_name=collection_name,
                page_name="CHAT",
                is_admin=Globals.is_admin

            )
            response = web.Response(
                body=txt.encode(),
                content_type='text/html'
            )
            response.set_cookie('ragit_auth_token', auth_token)
            response.set_cookie('user_name', user_name)
            logger.info("Serving main page.")
            return response


class RagitHandler:
    """Implements all the web handlers used from the service."""

    @classmethod
    def _is_multipart_request(cls, request):
        """Checks if the passed in request is a multipart upload.

        :param request : aiohttp.web.Request instance

        :returns: True if the request is a multipart upload, False otherwise.
        """
        headers = dict(request.headers)
        for key, value in headers.items():
            if key.lower() == "content-type":
                return "multipart" in value.lower()
        return False

    @web_handler
    async def upload_file(cls, request):
        """Uploads the file.

        Saves the file that is uploaded under the collection's documents
        directory and then it runs its embeddings and inserts it to the
        vectorized database.

        :param request : aiohttp.web.Request instance

        :returns: The fullpath to the temporary file holding the upload.
        :rtype: str
        """
        if not cls._is_multipart_request(request):
            return web.Response(
                text="Invalid upload: not a multipart/form-data request.",
                status=400
            )
        reader = await request.multipart()
        temp_file_path = None
        uploaded_filename = None
        while True:
            part = await reader.next()
            if part is None:
                break
            if part.filename:
                shared_dir = common.get_shared_directory()
                fullpath = os.path.join(
                    shared_dir,
                    Globals.rag_manager.get_rag_collection_name(),
                    "documents",
                    part.filename
                )
                with open(fullpath, 'wb') as fout:
                    while True:
                        chunk = await part.read_chunk()
                        if not chunk:
                            break
                        fout.write(chunk)

        raise web.HTTPFound(location="/admin")

    @web_handler
    async def admin_handler(self, request):
        """Displays the admin page.

        :param request: The web request.
        """
        try:
            auth_token = request.cookies.get('ragit_auth_token')
            user_name = request.cookies.get('user_name')
            Globals.validate_token(auth_token, user_name)
        except AuthenticationError:
            return web.HTTPFound('/login')
        else:
            template = _JINJA_ENV.get_template('admin.html')
            collection_name = Globals.rag_manager.get_rag_collection_name()
            txt = template.render(
                host=request.host,
                collection_name=collection_name,
                page_name="ADMIN",
                data=get_metrics(),
                is_admin=Globals.is_admin
            )
            response = web.Response(
                body=txt.encode(),
                content_type='text/html'
            )
            response.set_cookie('ragit_auth_token', auth_token)
            response.set_cookie('user_name', user_name)
            logger.info("Serving admin page.")
            return response

    @web_handler
    async def main_page_handler(self, request):
        """Displays the main page.

        :param request: The web request.
        """
        try:
            auth_token = request.cookies.get('ragit_auth_token')
            user_name = request.cookies.get('user_name')
            Globals.validate_token(auth_token, user_name)
        except AuthenticationError:
            return web.HTTPFound('/login')
        else:
            template = _JINJA_ENV.get_template('index.html')
            collection_name = Globals.rag_manager.get_rag_collection_name()
            txt = template.render(
                host=request.host,
                collection_name=collection_name,
                page_name="CHAT",
                is_admin=Globals.is_admin

            )
            response = web.Response(
                body=txt.encode(),
                content_type='text/html'
            )
            response.set_cookie('ragit_auth_token', auth_token)
            response.set_cookie('user_name', user_name)
            logger.info("Serving main page.")
            return response

    @web_handler
    async def history(self, request):
        """Redirects to history."""
        try:
            auth_token = request.cookies.get('ragit_auth_token')
            user_name = request.cookies.get('user_name')
            Globals.validate_token(auth_token, user_name)
        except AuthenticationError:
            return web.HTTPFound('/login')
        collection_name = Globals.rag_manager.get_rag_collection_name()
        template = _JINJA_ENV.get_template('history.html')
        txt = template.render(
            host=request.host,
            collection_name=collection_name,
            page_name="HISTORY",
            is_admin=Globals.is_admin
        )
        response = web.Response(
            body=txt.encode(),
            content_type='text/html'
        )
        return response

    @web_handler
    async def get_all_queries(self, request):
        """Returns all the available queries as a json document."""
        try:
            auth_token = request.cookies.get('ragit_auth_token')
            user_name = request.cookies.get('user_name')
            Globals.validate_token(auth_token, user_name)
        except AuthenticationError:
            return web.HTTPFound('/login')
        all_queries = UserRegistry.get_all_queries()
        return web.json_response(all_queries)

    @web_handler
    async def recent_chats_handler(self, request):
        """Returns the last chats for the user.

        Used to load the chatbox with the last conversations that were
        asked; meant to be called every time the use re-visits the chatbox.
        """
        try:
            auth_token = request.cookies.get('ragit_auth_token')
            user_name = request.cookies.get('user_name')
            Globals.validate_token(auth_token, user_name)
        except AuthenticationError:
            return web.HTTPFound('/login')

        count = int(request.match_info['count'])
        recent_chats = UserRegistry.get_recent_chats(user_name, count)
        return web.json_response(recent_chats)

    @web_handler
    async def speechify_handler(self, request):
        """Returns the recording for a message's response."""
        query_requests = str(request.rel_url)
        if query_requests.startswith('/'):
            query_requests = query_requests[1:]
        tokens = query_requests.split("/")[1:]
        msg_id = tokens[-1]
        file_path = UserRegistry.get_path_to_audio_recoding(msg_id)
        return web.FileResponse(path=file_path, headers={
            'Content-Type': 'audio/mpeg',
        })

    @web_handler
    async def delete_query(self, request):
        """Deletes a query using the passed in msg_id."""
        try:
            auth_token = request.cookies.get('ragit_auth_token')
            user_name = request.cookies.get('user_name')
            Globals.validate_token(auth_token, user_name)
        except AuthenticationError:
            return web.HTTPFound('/login')

        try:
            msg_id = int(request.match_info['msg_id'])
            UserRegistry.delete_query(msg_id)
        except:
            return web.json_response(
                {'message': 'Operation Failed'}, status=404
            )
        else:
            return web.Response(status=204)

    @web_handler
    async def query_handler(self, request):
        """Handles a query that is submitted by the chatbot user.

        :param request: The web request.
        """
        try:
            auth_token = request.cookies.get('ragit_auth_token')
            user_name = request.cookies.get('user_name')
            Globals.validate_token(auth_token, user_name)
        except AuthenticationError:
            return web.HTTPFound('/login')
        try:
            data = await request.json()
            query = data.get('query')

            temperature = data.get("temperature")
            max_tokens = data.get("max_tokens")
            matches_count = data.get("matches_count")

            if temperature:
                temperature = float(temperature)

            if max_tokens:
                max_tokens = int(max_tokens)

            if matches_count:
                matches_count = int(matches_count)

            t1 = datetime.datetime.now()
            response = Globals.rag_manager.query(
                query,
                k=matches_count,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            t2 = datetime.datetime.now()

            msg_id = UserRegistry.insert_message(
                user_name, t1, query, response, t2
            )
            return web.json_response(
                {
                    "response": response.response,
                    "message_id": msg_id
                }
            )
        except Exception as ex:
            return web.json_response({"response": str(ex)})

    @web_handler
    async def default_handler(self, request):
        """Redirects to login."""
        return web.HTTPFound('/login')

    @web_handler
    async def document_handler(self, request):
        """Returns a document from the local file system.

        :param request: The web request.
        """
        # Construct the full path to the file that is requested.
        query_requests = str(request.rel_url)
        if query_requests.startswith('/'):
            query_requests = query_requests[1:]
        tokens = query_requests.split("/")[1:]
        collection_name = Globals.rag_manager.get_rag_collection_name()

        file_path = os.path.join(
            common.get_shared_directory(),
            collection_name,
            "documents",
            *tokens
        )

        if not os.path.exists(file_path):
            error_desc = f"Requested file {file_path} not found."
            logger.error(error_desc)
            return web.HTTPNotFound(reason=error_desc)

        logger.info(f"Serving file: {file_path}")

        if file_path.endswith(".pdf"):
            return web.FileResponse(path=file_path, headers={
                'Content-Type': 'application/pdf',
            })
        elif file_path.endswith(".md"):
            with open(file_path) as fin:
                txt = fin.read()
            md_text = markdown.markdown(txt)
            return web.Response(
                body=md_text,
                content_type='text/html'
            )
        else:
            with open(file_path) as fin:
                txt = fin.read()
            return web.Response(text=txt)

    @web_handler
    async def signup_screen(self, request):
        """Displays the signupscreen.

        :param request: The web request.
        """
        template = _JINJA_ENV.get_template('signup.html')
        txt = template.render(
            host=request.host,
            page_name="CHAT"
        )
        return web.Response(
            body=txt.encode(),
            content_type='text/html'
        )

    @web_handler
    async def update_user_reaction(self, request):
        """Updates user reaction data (like thumps up / down, desired messsage).

        :param request: The web request.
        """
        try:
            auth_token = request.cookies.get('ragit_auth_token')
            user_name = request.cookies.get('user_name')
            Globals.validate_token(auth_token, user_name)
        except AuthenticationError:
            return web.HTTPFound('/login')
        try:
            data = await request.json()
            message_id = data.get('msg_id')
            thumps_up = data.get('thumps_up')
            desired_response = data.get('desired_response')

            UserRegistry.update_user_reaction(
                message_id, thumps_up, desired_response
            )

            return web.json_response(
                {
                    "response": "ok"
                }
            )
        except Exception as ex:
            return web.json_response({"response": str(ex)})

    @web_handler
    async def vote(self, request):
        """Casts the user's vote (thumps up - down).

        :param request: The web request.
        """
        try:
            auth_token = request.cookies.get('ragit_auth_token')
            user_name = request.cookies.get('user_name')
            Globals.validate_token(auth_token, user_name)
        except AuthenticationError:
            return web.HTTPFound('/login')
        try:
            data = await request.json()
            message_id = data.get('message_id')
            vote = data.get('vote')

            if vote == 1:
                UserRegistry.set_thumps_up(message_id)
            elif vote == 0:
                UserRegistry.set_thumps_down(message_id)

            return web.json_response(
                {
                    "response": "ok"
                }
            )
        except Exception as ex:
            return web.json_response({"response": str(ex)})

    @web_handler
    async def signup_new_acount(self, request):
        """Creates a new account

        :param request: The web request.
        """
        data = await request.post()  # Get the POST data as a dictionary
        user_name = data.get("user_name")
        password = data.get("password")
        email = data.get("email")
        try:
            UserRegistry.add_new_user(user_name, email, password)

        except common.MyGenAIException:
            return web.HTTPFound('/login')

    @web_handler
    async def login_screen(self, request):
        """Displays the login page.

        :param request: The web request.
        """
        try:
            auth_token = request.cookies.get('ragit_auth_token')
            user_name = request.cookies.get('user_name')
            Globals.validate_token(auth_token, user_name)
        except AuthenticationError:
            template = _JINJA_ENV.get_template('login.html')
            txt = template.render(
                host=request.host,
                page_name="LOGIN"
            )
            logger.info("Serving login page.")
            return web.Response(
                body=txt.encode(),
                content_type='text/html'
            )
        else:
            return web.HTTPFound('/ragit')

    @web_handler
    async def login_validate(self, request):
        """Validates login credentials.

        :param request: The web request.
        """
        data = await request.post()  # Get the POST data as a dictionary
        user_name = data.get("user_name")
        password = data.get("password")

        try:
            UserRegistry.validate_password(user_name, password)
            response = aiohttp.web.HTTPFound('/ragit')
            auth_token = Globals.generate_token(user_name)
            response.set_cookie('ragit_auth_token', auth_token)
            response.set_cookie('user_name', user_name)
            return response
        except common.MyGenAIException:
            return web.HTTPFound('/login')


def initialize():
    """Initializes the environment."""
    common.init_settings()
    if common.running_inside_docker_container():
        collection_name = os.environ.get("RAG_COLLECTION")
        is_admin = os.environ.get("IS_ADMIN")
        if isinstance(is_admin, str):
            is_admin = is_admin.upper() == "ADMIN"
        else:
            is_admin = False
    else:
        try:
            collection_name = sys.argv[1]
        except IndexError:
            raise ValueError("You must provide a valid collection name.")

        try:
            is_admin = sys.argv[2]
        except IndexError:
            is_admin = False
        else:
            if isinstance(is_admin, str):
                is_admin = is_admin.upper() == "ADMIN"
            else:
                is_admin = False
    Globals.is_admin = is_admin
    if Globals.is_admin:
        print("Running the RAGIT UI as ADMIN")
    else:
        print("Running the RAGIT UI as not ADMIN")
    print(f"Loading vector db, using collection {collection_name}")
    logger.info(f"Loading vector db, using collection {collection_name}")

    Globals.rag_manager = rag_mgr.RagManager(collection_name)
    response = Globals.rag_manager.query("what is this about?")
    logger.info("Loading vector db done.. %s", response)

    UserRegistry.set_rag_collection_name(collection_name)
    UserRegistry.create_db_if_needed()


def run():
    """Runs the backend service."""
    initialize()
    app = web.Application()
    ragit_handler = RagitHandler()
    ragit_light_handler = RagitLightHandler()

    app.add_routes(
        [
            web.get('/', ragit_handler.default_handler),
            web.get('/login', ragit_handler.login_screen, name="login"),
            web.post('/login', ragit_handler.login_validate),
            web.get('/ragit', ragit_handler.main_page_handler),
            web.post('/ragit', ragit_handler.query_handler),
            web.get('/signup', ragit_handler.signup_screen),
            web.post('/signup', ragit_handler.signup_new_acount),
            web.post('/vote', ragit_handler.vote),
            web.get('/history', ragit_handler.history),
            web.get('/queries', ragit_handler.get_all_queries),
            web.delete('/queries/{msg_id}', ragit_handler.delete_query),
            web.get('/admin', ragit_handler.admin_handler),
            web.post('/admin', ragit_handler.upload_file),
            web.get('/document/{file_path:.*}', ragit_handler.document_handler),
            web.get('/speechify/{file_path:.*}',
                    ragit_handler.speechify_handler),
            web.get('/recentchats/{count}', ragit_handler.recent_chats_handler),
            web.put('/updateuserinteraction',
                    ragit_handler.update_user_reaction),
            web.get('/light', ragit_light_handler.main_page_handler),
        ]
    )

    app_name = _CONFIGURATION.settings["web_service"]["name"]
    port = os.environ.get("SERVICE_PORT") or _DEFAULT_PORT
    port = int(port)
    app.router.add_static('/static', _PATH_TO_STATIC)
    logger.info(f"Starting {app_name} on port {port}")
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == '__main__':
    x = os.environ.get("RAG_COLLECTION")
    run()
