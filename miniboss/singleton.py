"""The singleton metaclass for ensuring only one instance of a class."""
import abc


class Singleton(abc.ABCMeta, type):
    """
    Singleton metaclass for ensuring only one instance of a class.

    This metaclass allows only one instance of a class to be created. It maintains a dictionary
    of instances, and whenever the class is instantiated, it checks if an instance of that class
    already exists. If it does, it returns the existing instance; otherwise, it creates a new instance
    and stores it in the dictionary for future use.

    Note:
        This metaclass should be used as the metaclass for the class that needs to be a singleton.

    Example:
        class MySingletonClass(metaclass=Singleton):
            pass
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Call method for the singleton metaclass."""
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class AbstractSingleton(abc.ABC, metaclass=Singleton):
    """
    Abstract singleton class for ensuring only one instance of a class.

    This abstract class provides the base implementation for a singleton class. It is meant to be
    inherited by classes that need to enforce the singleton pattern. The AbstractSingleton class itself
    cannot be instantiated directly.

    Example:
        class MySingletonClass(AbstractSingleton):
            pass
    """

    pass
