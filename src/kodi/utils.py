from typing import Dict, Optional, List, Any


def find_sub_dict(j: Dict, key: str) -> Optional[Dict]:
    """
    Finds the sub dictionary recursively associated with the specified key.


    :param j: the dictionary to search
    :type j: dict
    :param key: the key of the dictionary
    :type key: str
    :return: the dictionary or None if not found
    :rtype: dict or None
    """
    result = None
    for k in j:
        if isinstance(j[k], dict):
            if k == key:
                return j[k]
            else:
                result = find_sub_dict(j[k], key)
                if result is not None:
                    return result

    return result


def get_nested_value(j: Dict, path: List[str]) -> Optional[Any]:
    """
    Obtains the value from a path through the nested dictionaries.

    :param j: the dictionary to get the value from
    :type j: dict
    :param path: the list of dictionary keys for the nested dictionaries
    :type path: list
    :return: the located value or None if path not found
    """
    if len(path) == 0:
        return None
    if path[0] in j:
        if len(path) == 1:
            return j[path[0]]
        else:
            return get_nested_value(j[path[0]], path[1:])
    else:
        return None
