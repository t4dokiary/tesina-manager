import pymysql

pymysql.install_as_MySQLdb()

from django.db.backends.mysql.base import DatabaseWrapper
from django.db.backends.mysql.features import DatabaseFeatures

# 1. Ignorar la comprobación de versión mínima de MariaDB
DatabaseWrapper.check_database_version_supported = lambda self: None

# 2. Desactivar RETURNING para evitar el error de sintaxis en MariaDB 10.4
DatabaseFeatures.can_return_columns_from_insert = False
DatabaseFeatures.can_return_rows_from_bulk_insert = False