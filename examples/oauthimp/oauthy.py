from flask import Flask, jsonify
from flask_forward import FlaskForward

print(dir(FlaskForward))


class MockDbObj(object):

    _data = {
        'asdfkehlkjasdf': {
            'token': 'lkasjasdfasdfalskdjf',
            'user': {
                'username': 'userone',
                'email': 'email@emailscool.com'
            },
            'scopes': ['users', 'posts'],
            'redirect_uri': 'domain.com'
        },
        'laksdjlasdkjf': {
            'token': 'laksjdflaksdjfksjdlasdj',
            'user': {
                'username': 'usertwo',
                'email': 'email@someschool.edu'
            },
            'scopes': ['posts'],
            'redirect_uri': 'domain.com'
        },
        'haskdjfldlkja': {
            'token': 'asdfjlaskdfjkdkdkddk',
            'user': {
                'username': 'userthree',
                'email': 'email@somecompany.net'
            },
            'scopes':['followers'],
            'redirect_uri': 'domain.com'

        },
    }

    _tokens = [
        'lkasjasdfasdfalskdjf',
        'laksjdflaksdjfksjdlasdj',
        'asdfjlaskdfjkdkdkddk'
    ]


    def get_token(self, token):
        return token if token in _tokens else False

    def val_token(self, cid, token):
        return token == _data[cid]['token']

    def get_client(self, cid):
        return _data.get(cid)

    def val_client(self, cid):
        return _data.get(cid, False)

    def val_scopes(self, cid, scopes):
        return self.get_scopes(cid) == scopes

    def is_client(self, cid):
        return cid in _data

    def get_scopes(self, cid):
        return _data[cid]['scopes']

    def get_user(self, cid):
        return _data[cid]['user']

    def get_red(self, cid):
        return _data[cid]['redirect_uri']

    def val_red(self, cid, red_uri):
        return self.get_red(cid) in red_uri

    def val_resp_type(self):
        return True

    def save_token(self, cid, token):
        _tokens.append(token)
        _data[cid]['token'] = token
        return True


class ResService(object):

    def __init__(self):
        self.db = MockDbObj()


class UserService(ResService):
    pass


class TokenService(ResService):

    def save(self, token, request, *args, **kwargs):
        return self.db.save_token(request.client_id, token['access_token'])

    def revoke(self):
        pass

    def validate(self, token, scopes, request):
        valid = False
        valid = self.db.val_token(request.client_id, token)
        valid = self.db.val_scopes(request.client_id, scopes)
        return valid


class ClientService(ResService):

    def get_redirect_uri(self, client_id, request, *args, **kwargs):
        return self.db.get_red(client_id)

    def get_scopes(self, client_id, request, *args, **kwargs):
        return self.db.get_scopes(client_id)

    def validate_client_id(self, client_id, request, *args, **kwargs):
        request.client = self.db.get_client(client_id)
        request.client['client_id'] = client_id
        return self.db.val_client(client_id)

    def validate_redirect_uri(self, client_id, redirect_uri, request, *args, **kwargs):
        return self.db.val_red(client_id, redirect_uri)

    def validate_response_type(self, client_id, response_type, client, request, *args, **kwargs):
        return self.db.val_resp_type()

    def validate_scopes(self, client_id, scopes, request, *args, **kwargs):
        return self.db.val_scopes(client_id, scopes)


app = Flask(__name__)


@app.route("/clients", methods=['POST'])
def register_client():
    return 'hello world'


@app.route("/tokens", methods=['POST'])
@auth_api.auth_required(client_auth=True, token_auth=False)
def issue_token():
    return 'hello world'


@app.route("/")
def hello():
    return 'hello world'


@app.route("/users")
@auth_api.auth_required(client_auth=True, token_auth=True, scope=['users'])
def get_users():
    return jsonify([
        {
            'username': 'userone'
        },
        {
            'username': 'usertwo'
        },
        {
            'username': 'userthree'
        }
    ])


if __name__ == "__main__":
    app.run()
