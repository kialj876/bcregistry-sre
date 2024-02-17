# Copyright © 2019 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The Notify API service.

This module is the API for the BC Registries Notify application.
"""
import os

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.wsgi import OpenTelemetryMiddleware

from notify_api import errorhandlers, models
from notify_api.config import config
from notify_api.metadata import APP_NAME
from notify_api.models import db
from notify_api.resources import v1_endpoint, v2_endpoint
from notify_api.translations import babel
from notify_api.utils.auth import jwt
from notify_api.utils.logging import env_name_context, setup_logging
from notify_api.utils.tracing import init_trace

setup_logging(os.path.join(os.path.abspath(os.path.dirname(__file__)), "logging.yaml"))  # important to do this first


def create_app(service_environment=os.getenv("DEPLOYMENT_ENV", "production"), **kwargs):
    """Return a configured Flask App using the Factory method."""
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config[service_environment])
    app.url_map.strict_slashes = False

    errorhandlers.init_app(app)
    db.init_app(app)
    Migrate(app, db)

    if app.config.get("TRACING_ENABLE", None):
        init_trace(APP_NAME, service_environment)
        env_name_context.set(service_environment)
        with app.app_context():
            app.wsgi_app = OpenTelemetryMiddleware(app.wsgi_app)
            if app.config.get("TRACING_DB_ENABLE", None):
                SQLAlchemyInstrumentor().instrument(engine=db.engine)
        FlaskInstrumentor().instrument_app(app)

    babel.init_app(app)

    v1_endpoint.init_app(app)
    v2_endpoint.init_app(app)

    setup_jwt_manager(app, jwt)

    register_shellcontext(app)

    return app


def setup_jwt_manager(app, jwt_manager):
    """Use flask app to configure the JWTManager to work for a particular Realm."""

    def get_roles(a_dict):
        return a_dict["realm_access"]["roles"]  # pragma: no cover

    app.config["JWT_ROLE_CALLBACK"] = get_roles

    jwt_manager.init_app(app)


def register_shellcontext(app):
    """Register shell context objects."""

    def shell_context():
        """Shell context objects."""
        return {"app": app, "jwt": jwt, "db": db, "models": models}  # pragma: no cover

    app.shell_context_processor(shell_context)
