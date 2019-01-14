# miscellaneous classes that are used by the code

import colorama
import re

colorama.init()

class objectify(dict):
    def __init__(self, dictionary):
        d = dictionary.copy()
        self.__dict__ = self
        for key, value in dictionary.items():
            if (type(value) == dict):
                value = objectify(value)
            self.__setitem__(key, value)

class validate:
	@staticmethod
	def file_name(name):
		return re.sub(r'[\\\/\:\*\?\"\<\>\|]', '', name)


class console:
    """
    when calling the console class to display messages, use == to
    highlight important words
    """

    @staticmethod
    def info(message, end = None):
        console.__display__('lightblue_ex', 'info', message, end)

    @staticmethod
    def warning(message, end = None):
        console.__display__('lightyellow_ex', 'warning', message, end)

    @staticmethod
    def success(message, end = None):
        console.__display__('lightgreen_ex', 'success', message, end)

    @staticmethod
    def error(message, end = None):
        console.__display__('lightred_ex', 'error', message, end)

    @staticmethod
    def debug(message, end = None):
        console.__display__('magenta', 'debug', message, end)

    @staticmethod
    def config(message, end = None):
        console.__display__('cyan', 'config', message, end)

    @staticmethod
    def __display__(color, prefix, message, end = '\n'):
        background = getattr(colorama.Back, color.upper())
        foreground = getattr(colorama.Fore, color.upper())
        text_color = getattr(colorama.Fore, 'WHITE')

        message = re.sub(r'==(.*?)==', lambda highlight: '{0}{1}{2}'.format(foreground, highlight.group(1), text_color), message)
        message = message[0].upper()+message[1:]

        print('{background} {black_background} {foreground}{prefix} {text_color}{black_background}{message}'.format(
        	background = background,
            background_color = background,
            black_background = getattr(colorama.Back, 'BLACK'),
            foreground = foreground,
            message = message,
            prefix = prefix.upper(),
            text_color = text_color
        ), end = end)
