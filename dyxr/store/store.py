import uuid


class UserSession:
    def __init__(self, token, open_id, union_id, data, session_key):
        self.token = token
        self.open_id = open_id
        self.union_id = union_id
        self.data = data
        self.session_key = session_key

    def set_token(self, token):
        if token != "":
            self.token = token

    def get_token(self):
        return self.token

    def set_open_id(self, open_id):
        if open_id != "":
            self.open_id = open_id

    def get_open_id(self):
        return self.open_id

    def set_union_id(self, union_id):
        if union_id != "":
            self.union_id = union_id

    def get_union_id(self):
        return self.union_id

    def set_data(self, data):
        if data != "":
            self.data = data

    def get_data(self):
        return self.data

    def set_session_key(self, session_key):
        if session_key != "":
            self.session_key = session_key

    def get_session_key(self):
        return self.session_key


mem_cache = {}


def set_cache(token, open_id, union_id, data, session_key):
    if token in mem_cache.keys():
        user_data = mem_cache.get(token)
        user_data.set_token(token)
        user_data.set_open_id(open_id)
        user_data.set_union_id(union_id)
        user_data.set_data(data)
        user_data.set_session_key(session_key)
        return token
    else:
        new_token = str(uuid.uuid4())
        user_data = UserSession(new_token, open_id, union_id, data, session_key)
        mem_cache[new_token] = user_data
        return new_token


def get_cache(token):
    return mem_cache[token]
