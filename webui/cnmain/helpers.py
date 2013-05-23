""" some helper functions
"""


def get_extension(url):
    """Returns the rightmost extension of a URL resource if any."""
    index = url.rfind('.')
    if index != -1:
        out = url[index:]
        amp_index = out.rfind('&')
        out = out if amp_index == -1 else out[:amp_index]
        percent_index = out.rfind('%')
        out = out if percent_index == -1 else out[percent_index:]
        if not '%' in out:
            return out.lower()
