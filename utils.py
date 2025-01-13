import json
from urllib import parse


def get_user_data():
    with open("user.txt", encoding="utf-8") as f:
        user = f.read().strip()

    user_data = parse.unquote(user)

    user_data = dict(parse.parse_qsl(user_data))

    keys_to_remove = list(user_data.keys())[list(user_data.keys()).index("hash") + 1 :]
    for key in keys_to_remove:
        del user_data[key]

    return user_data


def get_user_token(token: str) -> str:
    start_index = token.find("{")
    end_index = token.rfind("}")

    json_string = token[start_index : end_index + 1]
    json_string = json.loads(json_string)

    return json_string["token"]
