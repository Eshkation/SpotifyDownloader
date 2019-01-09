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

class console:
    """
    when calling the console class to display messages, use == to
    highlight important words
    """

    @staticmethod
    def info(message):
        console.__display__('lightblue_ex', 'info', message)

    @staticmethod
    def warning(message):
        console.__display__('yellow', 'warning', message)

    @staticmethod
    def success(message):
        console.__display__('lightgreen_ex', 'success', message)

    @staticmethod
    def error(message):
        console.__display__('lightred_ex', 'error', message)

    @staticmethod
    def debug(message):
        console.__display__('magenta', 'debug', message)

    @staticmethod
    def __display__(color, prefix, message):
        background = getattr(colorama.Back, color.upper())
        foreground = getattr(colorama.Fore, color.upper())
        textColor = getattr(colorama.Fore, 'WHITE')

        message = re.sub(r'==(.*?)==', lambda highlight: '{0}{1}{2}'.format(foreground, highlight.group(1), textColor), message)
        message = message[0].upper()+message[1:]

        print('{foreground}> {prefix} {textColor}{blackBackground}{message}'.format(
            background_color = background,
            blackBackground = getattr(colorama.Back, 'BLACK'),
            foreground = foreground,
            message = message,
            prefix = prefix.upper(),
            textColor = textColor
        ))
