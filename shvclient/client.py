import json
import os
import sys
from ctypes import CDLL, CFUNCTYPE, c_char_p, c_double, c_int
from ctypes.util import find_library
import time

class Client:
    def __init__(self, api_id, api_hash):
        self.api_id = api_id
        self.api_hash = api_hash
        self._load_library()
        self._setup_functions()
        self._setup_logging()
        self.client_id = self._td_create_client_id()

    def _load_library(self):
        tdjson_path = find_library("libs")
        if tdjson_path is None:
            if os.name == "nt":
                tdjson_path = os.path.join("libs/td/tdjson.dll")
        else:
            sys.exit(
                "Error: Can't find 'tdjson' library. Make sure it's installed correctly."
            )

        try:
            self.tdjson = CDLL(tdjson_path)
        except Exception as e:
            sys.exit(f"Error loading TDLib: {e}")

    def _setup_functions(self):
        self._td_create_client_id = self.tdjson.td_create_client_id
        self._td_create_client_id.restype = c_int
        self._td_create_client_id.argtypes = []

        self._td_receive = self.tdjson.td_receive
        self._td_receive.restype = c_char_p
        self._td_receive.argtypes = [c_double]

        self._td_send = self.tdjson.td_send
        self._td_send.restype = None
        self._td_send.argtypes = [c_int, c_char_p]

        self._td_execute = self.tdjson.td_execute
        self._td_execute.restype = c_char_p
        self._td_execute.argtypes = [c_char_p]

        self.log_message_callback_type = CFUNCTYPE(None, c_int, c_char_p)
        self._td_set_log_message_callback = self.tdjson.td_set_log_message_callback
        self._td_set_log_message_callback.restype = None
        self._td_set_log_message_callback.argtypes = [
            c_int,
            self.log_message_callback_type,
        ]

    def _setup_logging(self, verbosity_level = 1):
        @self.log_message_callback_type
        def on_log_message_callback(verbosity_level, message):
            if verbosity_level == 0:
                sys.exit(f"TDLib fatal error: {message.decode('utf-8')}")

        self._td_set_log_message_callback(2, on_log_message_callback)
        self.execute(
            {"@type": "setLogVerbosityLevel", "new_verbosity_level": verbosity_level}
        )

    def execute(self, query):
        query_json = json.dumps(query).encode("utf-8")
        result = self._td_execute(query_json)
        if result:
            return json.loads(result.decode("utf-8"))
        return None
    
    def send(self, query):
        query_json = json.dumps(query).encode("utf-8")
        self._td_send(self.client_id, query_json)

    def receive(self, timeout=1.0):
        result = self._td_receive(timeout)
        if result:
            return json.loads(result.decode("utf-8"))
        return None
    
    def login(self):
        self.send({"@type": "getOption", "name": "version"})
        print("Starting Telegram authentication flow...")
        try:
            self._handle_authentication()
        except KeyboardInterrupt:
            print("\nAuthentication canceled by user.")
            sys.exit(0)

    def _handle_authentication(self) -> None:
        while True:
            event = self.receive()
            if not event:
                continue

            event_type = event["@type"]
            if event_type != "updateAuthorizationState":
                continue
                print(f"Receive: {json.dumps(event, indent=2)}")

            if event_type == "updateAuthorizationState":
                auth_state = event["authorization_state"]
                auth_type = auth_state["@type"]

                if auth_type == "authorizationStateClosed":
                    print("Authorization state closed.")
                    break

                elif auth_type == "authorizationStateWaitTdlibParameters":

                    print("Setting TDLib parameters...")
                    self.send(
                        {
                            "@type": "setTdlibParameters",
                            "database_directory": "tdlib_data",
                            "use_message_database": True,
                            "use_secret_chats": True,
                            "api_id": self.api_id,
                            "api_hash": self.api_hash,
                            "system_language_code": "ru",
                            "device_model": "ЖЕСТКИЙ КАПЕЦ",
                            "application_version": "15",
                        }
                    )

                elif auth_type == "authorizationStateWaitPhoneNumber":
                    phone_number = input(
                        "Please enter your phone number (international format): "
                    )
                    self.send(
                        {
                            "@type": "setAuthenticationPhoneNumber",
                            "phone_number": phone_number,
                        }
                    )

                elif auth_type == "authorizationStateWaitPremiumPurchase":
                    print("Telegram Premium subscription is required.")
                    return

                elif auth_type == "authorizationStateWaitEmailAddress":
                    email_address = input("Please enter your email address: ")
                    self.send(
                        {
                            "@type": "setAuthenticationEmailAddress",
                            "email_address": email_address,
                        }
                    )

                elif auth_type == "authorizationStateWaitEmailCode":
                    code = input(
                        "Please enter the email authentication code you received: "
                    )
                    self.send(
                        {
                            "@type": "checkAuthenticationEmailCode",
                            "code": {
                                "@type": "emailAddressAuthenticationCode",
                                "code": code,
                            },
                        }
                    )

                elif auth_type == "authorizationStateWaitCode":
                    code = input("Please enter the authentication code you received: ")
                    self.send({"@type": "checkAuthenticationCode", "code": code})

                elif auth_type == "authorizationStateWaitRegistration":
                    first_name = input("Please enter your first name: ")
                    last_name = input("Please enter your last name: ")
                    self.send(
                        {
                            "@type": "registerUser",
                            "first_name": first_name,
                            "last_name": last_name,
                        }
                    )

                elif auth_type == "authorizationStateWaitPassword":
                    password = input("Please enter your password: ")
                    self.send(
                        {"@type": "checkAuthenticationPassword", "password": password}
                    )

                elif auth_type == "authorizationStateReady":
                    print("Authorization complete! You are now logged in.")
                    return

    def get_chat(self, chat_id=777000, extra="get_chat_request"):
        query = {
            "@type": "getChat",
            "chat_id": chat_id,
            "@extra": extra
        }
        self.send(query)

    def get_chats(self, limit=50, chat_list=None, extra="get_chats_request"):
        query = {
            "@type": "getChats",
            "limit":limit,
            "chat_list":chat_list,
            "@extra":extra
        }
        self.send(query)

    def send_message(self, chat_id, text):
        request_id = int(time.time() * 1000)
        query = {
            "@type": "sendMessage",
            "chat_id": chat_id,
            "input_message_content": {
                "@type": "inputMessageText",
                "text": {
                    "@type": "formattedText",
                    "text": text
                }
            },
            "@extra": request_id 
        }
        self.send(query)
        return request_id
if __name__ == "__main__":
    pass