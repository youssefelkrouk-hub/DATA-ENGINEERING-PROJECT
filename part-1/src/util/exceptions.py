class ProjectBaseException(Exception):
    """Classe de base pour toutes les exceptions custom du projet.

    Hériter d'une exception commune permet, si besoin, d'attraper
    n'importe quelle erreur "métier" du projet avec un seul except,
    tout en gardant la possibilité de cibler une exception précise.
    """
    pass


# ------------------------------------------------------------------
# Exceptions liées à la configuration
# ------------------------------------------------------------------

class InvalidValueException(ProjectBaseException):
    """Levée quand une valeur de configuration est manquante, vide,
    ou mal formée (ex: section absente dans config.ini, chemin vide...).
    """
    pass


# ------------------------------------------------------------------
# Exceptions liées à l'API
# ------------------------------------------------------------------

class ApiRequestException(ProjectBaseException):
    """Levée quand l'appel à l'API externe (Mockaroo) échoue :
    timeout, erreur réseau, ou code de statut HTTP non 2xx.
    """
    pass


# ------------------------------------------------------------------
# Exceptions liées aux fichiers
# ------------------------------------------------------------------

class FileHandlingException(ProjectBaseException):
    """Levée en cas de problème lors de la lecture/écriture des fichiers
    CSV ou du registry (ex: fichier corrompu, registry illisible).
    """
    pass


class RegistryException(ProjectBaseException):
    """Levée quand le fichier registry.txt est introuvable, corrompu,
    ou ne peut pas être mis à jour correctement.
    """
    pass


# ------------------------------------------------------------------
# Exceptions liées à la base de données
# ------------------------------------------------------------------

class DBConnectionException(ProjectBaseException):
    """Levée quand la connexion à PostgreSQL échoue (mauvais identifiants,
    base inexistante, serveur injoignable, erreur d'encodage...).
    """
    pass


class DBQueryException(ProjectBaseException):
    """Levée quand une requête SQL échoue (création de table, upsert...),
    après que la connexion a déjà été établie avec succès.
    """
    pass