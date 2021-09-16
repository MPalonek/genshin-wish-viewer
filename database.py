import sqlite3
from sqlite3 import Error
import logging

# https://www.sqlitetutorial.net/sqlite-python/
# https://stackoverflow.com/questions/10325683/can-i-read-and-write-to-a-sqlite-database-concurrently-from-multiple-connections


# create WishDatabase and PresetDatabase inherited from Database class
class Database:
    database_version = 1
    database_name = ""
    connection = None
    failed_insert_number = 0

    def __init__(self, db_path):
        self.create_connection(db_path)

    def create_connection(self, db_path):
        """Opens connection to the SQLite database located in db_path.
        By using connection object, you can perform various database operations.
        In case, if there is no database this will create one and use it.
        :param db_path: path to database file
        :return:
        """
        try:
            self.connection = sqlite3.connect(db_path)
            logging.info('Connected to database - {}. SQlite version {}, sqlite adapter module version {}'
                         .format(self.database_name, sqlite3.sqlite_version, sqlite3.version))
        except Error as e:
            logging.error('Failed to connect to database. {}'.format(e))

    def execute_command(self, command):
        """ execute command statement
        :param command: sqlite statement
        :return:
        """
        logging.debug('Executing command: {}'.format(command))
        return self.connection.execute(command)

    def create_tables(self):
        # implement this in derived classes
        raise Exception("Tried to create tables for Database base parent class!")

    def initialize_database(self):
        # check version of database
        logging.info("Initializing database")
        try:
            check_version_command = "SELECT version FROM systemInfo;"
            cursor = self.execute_command(check_version_command)
            output = cursor.fetchall()
            logging.info("Database versions: {}, app expects version: {}".format(output, self.database_version))
            if output:
                db_version = int(output[-1][0])
                if db_version > self.database_version:
                    logging.error("Database version ({}) is newer than genshin wish viewer version ({})!"
                                  .format(db_version, self.database_version))
                    raise Exception("Database version is newer than genshin wish counter version!")
                elif db_version < self.database_version:
                    logging.info("Database version is older than genshin wish viewer version. Upgrading...")
                    # upgrade_db(db_version)
                else:
                    logging.info("Database version matches genshin wish viewer version.")
        except sqlite3.OperationalError as e:
            if str(e) == "no such table: systemInfo":
                # database is empty - create tables
                logging.info("Missing systemInfo table. Creating tables...")
                self.create_tables()
            else:
                # unknown error
                raise

    def create_info_table(self):
        logging.info("Creating info table")
        system_info_command = "CREATE TABLE IF NOT EXISTS systemInfo (creationDate date DEFAULT CURRENT_TIMESTAMP," \
                              "version integer NOT NULL PRIMARY KEY);"
        self.execute_command(system_info_command)
        self.insert_info_entry(self.database_version)

    def insert_info_entry(self, version):
        logging.info("Inserting systeminfo entry with version {}".format(version))
        system_info_entry = "INSERT INTO systemInfo (version) VALUES ({});".format(version)
        self.execute_command(system_info_entry)
        self.connection.commit()


class PresetDatabase(Database):
    database_name = "PresetDatabase"

    def create_preset_tables(self):
        logging.info("Creating preset tables")
        wish_commands = ["CREATE TABLE IF NOT EXISTS wishCharacter (id integer PRIMARY KEY AUTOINCREMENT, itemType text"
                         " NOT NULL, itemName text NOT NULL, timeReceived date NOT NULL, itemRarity integer NOT NULL);",
                         "CREATE TABLE IF NOT EXISTS wishNovice (id integer PRIMARY KEY AUTOINCREMENT, itemType text"
                         " NOT NULL, itemName text NOT NULL, timeReceived date NOT NULL, itemRarity integer NOT NULL);",
                         "CREATE TABLE IF NOT EXISTS wishPermanent (id integer PRIMARY KEY AUTOINCREMENT, itemType text"
                         " NOT NULL, itemName text NOT NULL, timeReceived date NOT NULL, itemRarity integer NOT NULL);",
                         "CREATE TABLE IF NOT EXISTS wishWeapon (id integer PRIMARY KEY AUTOINCREMENT, itemType text"
                         " NOT NULL, itemName text NOT NULL, timeReceived date NOT NULL, itemRarity integer NOT NULL);"]
        for command in wish_commands:
            self.execute_command(command)

    def create_tables(self):
        """create tables for database (systemInfo, wishCharacter, wishNovice, wishPermanent, wishWeapon)
        :return:
        """
        self.create_info_table()
        self.create_preset_tables()

    def get_table_names(self):
        tables = []
        cmd = "SELECT name FROM sqlite_master WHERE type='table';"
        cursor = self.execute_command(cmd)
        for item in cursor:
            tables.append(item[0])
        # sqlite_sequence is always in sqlite_master table, if there are any other tables - remove it
        if tables:
            tables.remove('sqlite_sequence')
        return tables

    def get_number_of_elements_in_database(self):
        count_commands = ["SELECT COUNT(1) from wishCharacter;",
                          "SELECT COUNT(1) from wishNovice;",
                          "SELECT COUNT(1) from wishPermanent;",
                          "SELECT COUNT(1) from wishWeapon;"]
        count_table = []
        for cmd in count_commands:
            count_table.append(self.connection.execute(cmd).fetchall()[0][0])
        return count_table

    def insert_wish_entry(self, table, wish):
        try:
            insert = 'INSERT INTO {}(itemType, itemName, timeReceived, itemRarity) VALUES("{}", "{}", {});'\
                .format(table, wish[0], wish[1], wish[2])
            self.connection.execute(insert)
            self.connection.commit()
        except Error as e:
            logging.error('Failed to insert entry. {}'.format(e))
            self.failed_insert_number = self.failed_insert_number + 1

    def insert_multiple_wish_entries(self, table, wishes):
        # TODO looks kinda sussy, review it
        try:
            for wish in wishes:
                insert = 'INSERT INTO {}(itemType, itemName, timeReceived) VALUES("{}", "{}", {});'\
                    .format(table, wish[0], wish[1], wish[2])
                self.connection.execute(insert)
            self.connection.commit()
        except Error as e:
            logging.error('Failed to insert entry. {}'.format(e))
            self.failed_insert_number = self.failed_insert_number + 1


class WishDatabase(Database):
    database_name = "WishDatabase"

    def create_wish_tables(self):
        logging.info("Creating preset tables")
        wish_commands = ["CREATE TABLE IF NOT EXISTS wishCharacter (id integer PRIMARY KEY AUTOINCREMENT, itemType text"
                         " NOT NULL, itemName text NOT NULL, timeReceived date NOT NULL, itemRarity integer NOT NULL);",
                         "CREATE TABLE IF NOT EXISTS wishNovice (id integer PRIMARY KEY AUTOINCREMENT, itemType text"
                         " NOT NULL, itemName text NOT NULL, timeReceived date NOT NULL, itemRarity integer NOT NULL);",
                         "CREATE TABLE IF NOT EXISTS wishPermanent (id integer PRIMARY KEY AUTOINCREMENT, itemType text"
                         " NOT NULL, itemName text NOT NULL, timeReceived date NOT NULL, itemRarity integer NOT NULL);",
                         "CREATE TABLE IF NOT EXISTS wishWeapon (id integer PRIMARY KEY AUTOINCREMENT, itemType text"
                         " NOT NULL, itemName text NOT NULL, timeReceived date NOT NULL, itemRarity integer NOT NULL);"]
        for command in wish_commands:
            self.execute_command(command)

    def create_tables(self):
        """create tables for database (systemInfo, wishCharacter, wishNovice, wishPermanent, wishWeapon)
        :return:
        """
        self.create_info_table()
        self.create_wish_tables()

    def get_table_names(self):
        tables = []
        cmd = "SELECT name FROM sqlite_master WHERE type='table';"
        cursor = self.execute_command(cmd)
        for item in cursor:
            tables.append(item[0])
        # sqlite_sequence is always in sqlite_master table, if there are any other tables - remove it
        if tables:
            tables.remove('sqlite_sequence')
        return tables

    def get_number_of_elements_in_database(self):
        count_commands = ["SELECT COUNT(1) from wishCharacter;",
                          "SELECT COUNT(1) from wishNovice;",
                          "SELECT COUNT(1) from wishPermanent;",
                          "SELECT COUNT(1) from wishWeapon;"]
        count_table = []
        for cmd in count_commands:
            count_table.append(self.connection.execute(cmd).fetchall()[0][0])
        return count_table

    def get_wishes_from_table(self, table_name):
        try:
            select = 'SELECT itemType, itemName, timeReceived, itemRarity FROM {};'.format(table_name)
            return self.connection.execute(select).fetchall()
        except Error as e:
            logging.error('Failed to select entries. {}'.format(e))

    def insert_wish_entry(self, table, wish):
        try:
            insert = 'INSERT INTO {}(itemType, itemName, timeReceived, itemRarity) VALUES("{}", "{}", "{}", {});'\
                .format(table, wish[0], wish[1], wish[2], wish[3])
            self.connection.execute(insert)
            self.connection.commit()
        except Error as e:
            logging.error('Failed to insert entry. {}'.format(e))
            self.failed_insert_number = self.failed_insert_number + 1

    def insert_multiple_wish_entries(self, table, wishes):
        # TODO looks kinda sussy, review it - if one entry fails whole page of wishes get rekt
        try:
            for wish in wishes:
                insert = 'INSERT INTO {}(itemType, itemName, timeReceived, itemRarity) VALUES("{}", "{}", "{}", {});'\
                    .format(table, wish[0], wish[1], wish[2], wish[3])
                self.connection.execute(insert)
            self.connection.commit()
        except Error as e:
            logging.error('Failed to insert entry. {}'.format(e))
            self.failed_insert_number = self.failed_insert_number + 1
