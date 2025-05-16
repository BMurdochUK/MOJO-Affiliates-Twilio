"""
Custom Flask CLI commands for MOJO WhatsApp Manager
"""
import click
from flask.cli import with_appcontext
from mojo_web import db
from mojo_web.models import User

@click.command('create-admin')
@click.option('--username', default='mojo-admin', help='Admin username')
@click.option('--password', default='Letmein99#123', help='Admin password')
@with_appcontext
def create_admin_command(username, password):
    """Create an admin user"""
    # Check if user already exists
    user = User.query.filter_by(username=username).first()
    if user:
        click.echo(f'User {username} already exists')
        return
    
    # Create new user
    user = User(username=username)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    click.echo(f'Admin user {username} created successfully') 