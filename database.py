import sqlite3
from sqlite3 import Error
import logging

# https://www.sqlitetutorial.net/sqlite-python/
# https://stackoverflow.com/questions/10325683/can-i-read-and-write-to-a-sqlite-database-concurrently-from-multiple-connections

# character and banner lists data:
# https://genshin-impact.fandom.com/wiki/Wishes/List#Current


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
    # WEAPON 5-STAR:    MORA    WPN_ASC_MAT ELT_ASC_MAT CMN_ASC_MAT
    # ---1---          10000        5            5           3
    # ---2---          20000        5           18          12
    # ---3---          30000        9            9           9
    # ---4---          45000        5           18          14
    # ---5---          55000        9           14           9
    # ---6---          65000        6           27          18
    # WEAPON 4-STAR:    MORA    WPN_ASC_MAT ELT_ASC_MAT CMN_ASC_MAT
    # ---1---           5000        3            3           2
    # ---2---          15000        3           12           8
    # ---3---          20000        6            6           6
    # ---4---          30000        3           12           9
    # ---5---          35000        6            9           6
    # ---6---          45000        4           18          12
    ###############################################################
    # CHAR:             MORA    ASC_GEM BOS_MAT LCL_SPC CMN_ASC_MAT
    # ---1---          20000        1        0       3       3
    # ---2---          40000        3        2      10      15
    # ---3---          60000        6        4      20      12
    # ---4---          80000        3        8      30      18
    # ---5---         100000        6       12      45      12
    # ---6---         120000        6       20      60      24
    # CHAR TALENT:      MORA    REQ_ASC CMN_ASC_MAT TLN_MAT WKL_BOS_MAT
    # ---1---          12500        2        6       3          0
    # ---2---          17500        3        3       2          0
    # ---3---          25000        3        4       4          0
    # ---4---          30000        4        6       6          0
    # ---5---          37500        4        9       9          0
    # ---6---         120000        5        4       4          1
    # ---7---         260000        5        6       6          1
    # ---8---         450000        6        9      12          2
    # ---9---         700000        6       12      16          2

    def create_preset_tables(self):
        logging.info("Creating preset tables")
        preset_commands = ["CREATE TABLE IF NOT EXISTS Characters ();",
                           "CREATE TABLE IF NOT EXISTS Weapons ();",
                           "CREATE TABLE IF NOT EXISTS Materials ();",
                           "CREATE TABLE IF NOT EXISTS Artifacts ();"]
        for command in preset_commands:
            self.execute_command(command)

    def create_tables(self):
        """create tables for database (systemInfo, Characters, Weapons, Materials, Artifacts)
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
        count_commands = ["SELECT COUNT(1) from Characters;",
                          "SELECT COUNT(1) from Weapons;",
                          "SELECT COUNT(1) from Materials;",
                          "SELECT COUNT(1) from Artifacts;"]
        count_table = []
        for cmd in count_commands:
            count_table.append(self.connection.execute(cmd).fetchall()[0][0])
        return count_table

    def insert_entry(self, table, wish):
        pass

    def insert_multiple_entries(self, table, wishes):
        pass


class WishDatabase(Database):
    database_name = "WishDatabase"

    def create_wish_tables(self):
        logging.info("Creating wish tables")
        wish_commands = ["CREATE TABLE IF NOT EXISTS wishCharacter (id integer PRIMARY KEY AUTOINCREMENT, itemType text"
                         " NOT NULL, itemName text NOT NULL, timeReceived date NOT NULL, itemRarity integer NOT NULL);",
                         "CREATE TABLE IF NOT EXISTS wishWeapon (id integer PRIMARY KEY AUTOINCREMENT, itemType text"
                         " NOT NULL, itemName text NOT NULL, timeReceived date NOT NULL, itemRarity integer NOT NULL);",
                         "CREATE TABLE IF NOT EXISTS wishStandard (id integer PRIMARY KEY AUTOINCREMENT, itemType text"
                         " NOT NULL, itemName text NOT NULL, timeReceived date NOT NULL, itemRarity integer NOT NULL);",
                         "CREATE TABLE IF NOT EXISTS wishBeginner (id integer PRIMARY KEY AUTOINCREMENT, itemType text"
                         " NOT NULL, itemName text NOT NULL, timeReceived date NOT NULL, itemRarity integer NOT NULL);"]
        for command in wish_commands:
            self.execute_command(command)

    def create_tables(self):
        """create tables for database (systemInfo, wishCharacter, wishWeapon, wishStandard, wishBeginner)
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
                          "SELECT COUNT(1) from wishWeapon;",
                          "SELECT COUNT(1) from wishStandard;",
                          "SELECT COUNT(1) from wishBeginner;"]
        count_table = []
        for cmd in count_commands:
            count_table.append(self.connection.execute(cmd).fetchall()[0][0])
        return count_table

    def get_wishes_from_table(self, table_name):
        try:
            select = 'SELECT itemType, itemName, timeReceived, itemRarity FROM {} ORDER BY timeReceived ASC, id ASC;'.format(table_name)
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
