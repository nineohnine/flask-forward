from oauthlib.oauth2 import MobileApplicationServer
from oauthlib.oauth2 import RequestValidator as ReqVal
from oauthlib.common import Request as OAuthlibRequest
from werkzeug.local import LocalProxy
from flask import Request, Response
from functools import wraps

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

__all__ = (
    'FlaskForward'
    'auth_api',
    'AuthRequest',
    'AuthResponse',
)


class ValidatorService(ReqVal):

    _REQUIRED_METHODS = {
        'user': [
        ],
        'client': [
            'get_redirect_uri',
            'get_scopes',
            'validate_client_id',
            'validate_redirect_uri',
            'validate_response_type',
            'validate_scopes'
        ],
        'token': [
            'save',
            'revoke',
            'validate'
        ]
    }

    user = token = client = None

    def __init__(self, *args, **kwargs):

        for k,v in kwargs.items():
            if k in self.REQUIRED_METHODS:
                for m in self.REQUIRED_METHODS[K]:
                    if not callable(getattr(v, m)):
                        raise NotImplementedError(
                                "%s object must implement %s method." % (k,m)
                            )
                    else:
                        setattr(self, k, v)

    def get_default_redirect_uri(self, client_id, request, *args, **kwargs):
        """Get the default redirect URI for the client.

        :param client_id: Unicode client identifier
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: The default redirect URI for the client

        Method is used by:
            - Authorization Code Grant
            - Implicit Grant
        """
        return self.client.get_redirect_uri(client_id, request, *args, **kwargs)

    def get_default_scopes(self, client_id, request, *args, **kwargs):
        """Get the default scopes for the client.

        :param client_id: Unicode client identifier
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: List of default scopes

        Method is used by all core grant types:
            - Authorization Code Grant
            - Implicit Grant
            - Resource Owner Password Credentials Grant
            - Client Credentials grant
        """
        return self.client.get_scopes(client_id, request, *args, **kwargs)

    def revoke_token(self, token, token_type_hint, request, *args, **kwargs):
        """Revoke an access or refresh token.

        :param token: The token string.
        :param token_type_hint: access_token or refresh_token.
        :param request: The HTTP Request (oauthlib.common.Request)

        Method is used by:
            - Revocation Endpoint
        """
        self.token.revoke(token, token_type_hint, request, *args, **kwargs)

    def save_bearer_token(self, token, request, *args, **kwargs):
        """Persist the Bearer token.

        The Bearer token should at minimum be associated with:
            - a client and it's client_id, if available
            - a resource owner / user (request.user)
            - authorized scopes (request.scopes)
            - an expiration time
            - a refresh token, if issued

        The Bearer token dict may hold a number of items::

            {
                'token_type': 'Bearer',
                'access_token': 'askfjh234as9sd8',
                'expires_in': 3600,
                'scope': 'string of space separated authorized scopes',
                'refresh_token': '23sdf876234',  # if issued
                'state': 'given_by_client',  # if supplied by client
            }

        Note that while "scope" is a string-separated list of authorized scopes,
        the original list is still available in request.scopes

        :param client_id: Unicode client identifier
        :param token: A Bearer token dict
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: The default redirect URI for the client

        Method is used by all core grant types issuing Bearer tokens:
            - Authorization Code Grant
            - Implicit Grant
            - Resource Owner Password Credentials Grant (might not associate a client)
            - Client Credentials grant
        """

        self.token.save(token, request, *args, **kwargs)

    def validate_bearer_token(self, token, scopes, request):
        """Ensure the Bearer token is valid and authorized access to scopes.

        :param token: A string of random characters.
        :param scopes: A list of scopes associated with the protected resource.
        :param request: The HTTP Request (oauthlib.common.Request)

        A key to OAuth 2 security and restricting impact of leaked tokens is
        the short expiration time of tokens, *always ensure the token has not
        expired!*.

        Two different approaches to scope validation:

            1) all(scopes). The token must be authorized access to all scopes
                            associated with the resource. For example, the
                            token has access to ``read-only`` and ``images``,
                            thus the client can view images but not upload new.
                            Allows for fine grained access control through
                            combining various scopes.

            2) any(scopes). The token must be authorized access to one of the
                            scopes associated with the resource. For example,
                            token has access to ``read-only-images``.
                            Allows for fine grained, although arguably less
                            convenient, access control.

        A powerful way to use scopes would mimic UNIX ACLs and see a scope
        as a group with certain privileges. For a restful API these might
        map to HTTP verbs instead of read, write and execute.

        Note, the request.user attribute can be set to the resource owner
        associated with this token. Similarly the request.client and
        request.scopes attribute can be set to associated client object
        and authorized scopes. If you then use a decorator such as the
        one provided for django these attributes will be made available
        in all protected views as keyword arguments.

        :param token: Unicode Bearer token
        :param scopes: List of scopes (defined by you)
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: True or False

        Method is indirectly used by all core Bearer token issuing grant types:
            - Authorization Code Grant
            - Implicit Grant
            - Resource Owner Password Credentials Grant
            - Client Credentials Grant
        """
        return self.token.validate(token, scopes, request)

    def validate_client_id(self, client_id, request, *args, **kwargs):
        """Ensure client_id belong to a valid and active client.

        Note, while not strictly necessary it can often be very convenient
        to set request.client to the client object associated with the
        given client_id.

        :param request: oauthlib.common.Request
        :rtype: True or False

        Method is used by:
            - Authorization Code Grant
            - Implicit Grant
        """
        return self.client.validate_client_id(client_id, request, *args, **kwargs)


    def authenticate_client(self, request, *args, **kwargs):
        """Authenticate client through means outside the OAuth 2 spec.
        Means of authentication is negotiated beforehand and may for example
        be `HTTP Basic Authentication Scheme`_ which utilizes the Authorization
        header.
        Headers may be accesses through request.headers and parameters found in
        both body and query can be obtained by direct attribute access, i.e.
        request.client_id for client_id in the URL query.
        OBS! Certain grant types rely on this authentication, possibly with
        other fallbacks, and for them to recognize this authorization please
        set the client attribute on the request (request.client). Note that
        preferably this client object should have a client_id attribute of
        unicode type (request.client.client_id).
        :param request: oauthlib.common.Request
        :rtype: True or False
        Method is used by:
            - Authorization Code Grant
            - Resource Owner Password Credentials Grant (may be disabled)
            - Client Credentials Grant
            - Refresh Token Grant
        .. _`HTTP Basic Authentication Scheme`: http://tools.ietf.org/html/rfc1945#section-11.1
        """

        return self.client.validate_client_id(request, *args, **kwargs)


    def validate_redirect_uri(self, client_id, redirect_uri, request, *args, **kwargs):
        """Ensure client is authorized to redirect to the redirect_uri requested.

        All clients should register the absolute URIs of all URIs they intend
        to redirect to. The registration is outside of the scope of oauthlib.

        :param client_id: Unicode client identifier
        :param redirect_uri: Unicode absolute URI
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: True or False

        Method is used by:
            - Authorization Code Grant
            - Implicit Grant
        """

        return self.client.validate_redirect_uri(
            client_id,
            redirect_uri,
            request,
            *args,
            **kwargs
        )

    def validate_response_type(self, client_id, response_type, client, request, *args, **kwargs):
        """Ensure client is authorized to use the response_type requested.

        :param client_id: Unicode client identifier
        :param response_type: Unicode response type, i.e. code, token.
        :param client: Client object set by you, see authenticate_client.
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: True or False

        Method is used by:
            - Authorization Code Grant
            - Implicit Grant
        """

        return self.client.validate_response_type(
            client_id,
            response_type,
            client,
            request,
            *args,
            **kwargs
        )

    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        """Ensure the client is authorized access to requested scopes.

        :param client_id: Unicode client identifier
        :param scopes: List of scopes (defined by you)
        :param client: Client object set by you, see authenticate_client.
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: True or False

        Method is used by all core grant types:
            - Authorization Code Grant
            - Implicit Grant
            - Resource Owner Password Credentials Grant
            - Client Credentials Grant
        """

        self.client.validate_scopes(
            client_id,
            scopes,
            client,
            request,
            *args,
            **kwargs
        )


class AuthInterface(object):

    def __init__(self, *args, **kwargs):
        pass

    def authorize_client(self, *args, **kwargs):
        pass

    def authorize_token(self, *args, **kwargs):
        pass

    def validate_auth_request(self, *args, **kwargs):
        pass

    def validate_revoke_request(self, *args, **kwargs):
        pass


class OAuthService(AuthInterface):

    auth_request_cls = OAuthlibRequest
    validator = server = None

    def __init__(self, user_cls, client_cls, token_cls, **kwargs):

            self.validator = ValidatorService(
                user=user_cls(),
                client=client_cls(),
                token=token_cls()
            )

            self.server = MobileApplicationServer(self.validator)

    def authorize_client(self, request, *args, **kwargs):
        request = request.to_auth_request()
        return self.validator.authenticate_client(
                request,
                *args,
                **kwargs
        )

    def authorize_token(self, request, *args, **kwargs):
        token = request.token
        request = request.to_auth_request()
        return self.validator.validate_bearer_token(
                token,
                request.scopes,
                request,
                *args,
                **kwargs
        )

    def validate_auth_request(self, request, *args, **kwargs):
        user = request.user
        request = request.to_auth_request()
        return self.server.create_authorization_response(
                url,
                http_methed=request.http_method,
                body=request.body,
                headers=request.headers,
                scopes=request.scope,
                credentials={'user', user}
        )

    def validate_revoke_request(self, request,*args, **kwargs):
        request = request.to_auth_req()
        return self.server.create_revocation_response(
                url,
                http_methed=request.http_method,
                body=request.body,
        )


class OAuthRequest(Request):

    authorized = access_token = redirect_uri = scope = None
    response_type = state = token = client_id = user = _json_data = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._json_data = self.get_json();
        self.scope = self.form.get('scope') or self._json_data.get('scope')
        self.state = self.form.get('state') or self._json_data.get('state')
        self.redirect_uri = self.form.get('redirect-uri') or self._json_data.get('redirect-uri')
        self.response_type = self.form.get('response-type') or self._json_data.get('response-type')
        self.client_id = self.form.get('client-id') or self._json_data.get('client-id') or self.headers.get('client-id')
        self.token = self.headers.get('Authorization')[7:] if self.headers.get('Authorization') else None;

    def to_auth_req(self):

        req_body = {
            'client_id': self.client_id,
            'state': self.state,
            'response_type': self.response_type,
            'scopes': self.scope
        }

        return OAuthService.auth_request_cls(
            self.url,
            http_method=self.method,
            body=req_body,
            headers=self.headers
        )


class OAuthResponse(Response):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def from_auth_response():
        # return instance of Authentication Token Engine's request class
        pass


class OAuthApi(object):

    def __init__(self, user, token, client, **kwargs):

        self.auth_service = OAuthService(
            user,
            client,
            token
        )


    def auth_required(self, f, client_auth=None, token_auth=None, scope=None, *args, **kwargs):

        @wraps(f)
        def df(*args, **kwargs):
            request.authorized = False

            if client_auth:
                authorized = self.auth_server.authorize_client(
                    request,
                    *args,
                    **kwargs
                )

            if token_auth:
                request.authorized = self.auth_server.authorize_token(
                    request,
                    *args,
                    **kwargs
                )

            return f(*args, **kwargs)

        return df

    def build_authorization_response(self, request):
        return self.auth_service.validate_auth_request(request)

    def build_revocation_response(self, request):
        return self.auth_service.validate_revoke_request(request)


class FlaskForward(object):

    auth_api_cls = OAuthApi
    auth_api = _user_cls = _token_cls = client_cls = None
    ff_request_cls = OAuthRequest
    ff_response_cls = OAuthResponse

    def __init__(self, app=None, usr_cls=None, tk_cls=None, cl_cls=None):
        self.app = app
        self._user_srv = usr_cls if usr_cls is not None else self._user_cls
        self._client_srv = cl_cls if cl_cls is not None else self._client_cls
        self._token_cls = tk_cls if tk_cls is not None else self._token_cls

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.request_class = self.ff_request_cls
        app.response_class = self.ff_response_cls

        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

    def teardown(self, exception):
        ctx = stack.top
        if hasattr(ctx, 'flask_forward'):
            delattr(ctx, 'flask_forward')

    def start(self):
        return self.auth_api_cls(
            self._user_cls,
            self._token_cls,
            self._client_cls
        )

    @property
    def auth_api(self):
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'flask_forward'):
                ctx.flask_forward = self.start()
            return ctx.flask_forward

auth_api = LocalProxy(lambda: stack.top.auth_api)

