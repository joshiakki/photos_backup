from flask.cli import FlaskGroup

from app import create_app
from extensions import db
import models

app = create_app()

cli = FlaskGroup(create_app=create_app)


@app.shell_context_processor
def shell_context():

    return {

        "db": db,

        "User": models.User,
        "Media": models.Media,
        "RefreshToken": models.RefreshToken,
        "LoginHistory": models.LoginHistory

    }


if __name__ == "__main__":

    cli()