import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from pprint import pprint


class Firebase_Boombox:
    
    def __init__(self, logger, colorama, bot_name):

        # Fetch the service account key JSON file contents or OS environ variable
        # try:
        #     self.cred = credentials.Certificate('boombox-327216-firebase-adminsdk-7y7lw-97e32430ca.json')
        #     logger.info(f"{colorama.Fore.GREEN}Successfully loaded credentials from JSON file.{colorama.Style.RESET_ALL}")
        #     logger.info(f"{colorama.Fore.YELLOW}WARN: You shouldn't be using JSON cred file to authenticate.\nIt is recommended to store them as environment variables instead.{colorama.Style.RESET_ALL}")
        # except ValueError:
        self.cred = credentials.Certificate({
            "type": os.environ.get('type'),
            "project_id": os.environ.get('project_id'),
            "private_key_id": os.environ.get('private_key_id'),
            "private_key": os.environ.get('private_key'),
            "client_email": os.environ.get('client_email'),
            'client_id': os.environ.get('client_id'),
            'auth_uri': os.environ.get('auth_uri'),
            "token_uri": os.environ.get('token_uri'),
            'auth_provider_x509_cert_url': os.environ.get('auth_provider_x509_cert_url'),
            "client_x509_cert_url": os.environ.get("client_x509_cert_url")
        })
        logger.info(f"{colorama.Fore.GREEN}Successfully loaded credentials from environment variables.{colorama.Style.RESET_ALL}")

        try:
            self.firebase_database_url = os.environ['firebase_database_url']
        except KeyError:
            logger.warning(f"{colorama.Fore.RED}firebase_database_url not present in environ vars, please add.{colorama.Style.RESET_ALL}")
            quit()

        # Initialize the app with a service account, granting admin privileges
        firebase_admin.initialize_app(self.cred, {
            'databaseURL': self.firebase_database_url
        })
        self.bot_name=bot_name
        self.db = db
        self.logger = logger


    def check_db(self):
        ref = self.db.reference('/')

        databases = ref.get()

        if not databases:
            return False
    
        for database in databases:
            if database == self.bot_name:
                return databases[database]
        return False

    
    def create_db(self):
        ref = self.db.reference('/')

        ref.child(self.bot_name).set({
            "created": True
        })

        if self.check_db():
            return True
        else:
            return False

    
    def sync_database(self, data):
        ref = self.db.reference('/')
        self.logger.info(data)
        ref.child(self.bot_name).set(data)

    
    def update_server_prefix(self, new_command_prefix, guild_id, guild_name):
        ref = self.db.reference('/')

        ref.child(self.bot_name).update({
            guild_id: {
                'guild_name': guild_name,
                'command_prefix': new_command_prefix
            }
        })
