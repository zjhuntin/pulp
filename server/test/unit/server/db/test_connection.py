from ConfigParser import NoOptionError
import unittest

from mock import patch, Mock, call

from pulp.devel import mock_config
from pulp.server import config
from pulp.server.db import connection


class MongoEngineConnectionError(Exception):
    pass


class TestDatabaseSeeds(unittest.TestCase):

    def test_seeds_default(self):
        self.assertEqual(config._default_values['database']['seeds'], 'localhost:27017')

    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    def test_seeds_invalid(self, mock_mongoengine):
        mock_mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}

        connection.initialize(seeds='localhost:27017:1234')

        max_pool_size = connection._DEFAULT_MAX_POOL_SIZE
        database = config.config.get('database', 'name')
        mock_mongoengine.connect.assert_called_once_with(database, max_pool_size=max_pool_size,
                                                         host='localhost')

    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    def test_seeds_is_empty(self, mock_mongoengine):
        mock_mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}

        connection.initialize(seeds='')

        max_pool_size = connection._DEFAULT_MAX_POOL_SIZE
        database = config.config.get('database', 'name')
        mock_mongoengine.connect.assert_called_once_with(database, max_pool_size=max_pool_size)

    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    def test_seeds_is_set_from_argument(self, mock_mongoengine):
        mock_mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}

        connection.initialize(seeds='firsthost:1234,secondhost:5678')

        max_pool_size = connection._DEFAULT_MAX_POOL_SIZE
        database = config.config.get('database', 'name')
        mock_mongoengine.connect.assert_called_once_with(database, max_pool_size=max_pool_size,
                                                         host='firsthost', port=1234)

    @mock_config.patch({'database': {'seeds': 'firsthost:1234,secondhost:5678'}})
    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    def test_seeds_from_config(self, mock_mongoengine):
        mock_mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}

        connection.initialize()

        max_pool_size = connection._DEFAULT_MAX_POOL_SIZE
        database = config.config.get('database', 'name')
        mock_mongoengine.connect.assert_called_once_with(database, max_pool_size=max_pool_size,
                                                         host='firsthost', port=1234)


class TestDatabaseName(unittest.TestCase):

    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    def test__DATABASE_uses_default_name(self, mock_mongoengine):
        """
        Assert that the name from the database config is used if not provided as a parameter to
        initialize().
        """
        mock_mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}

        connection.initialize()

        name = config.config.get('database', 'name')
        host = config.config.get('database', 'seeds').split(':')[0]
        port = int(config.config.get('database', 'seeds').split(':')[1])
        mock_mongoengine.connect.assert_called_once_with(name, host=host, max_pool_size=10,
                                                         port=port)

    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    def test_name_is_set_from_argument(self, mock_mongoengine):
        """
        Assert that passing a name to initialize() overrides the value from the config.
        """
        mock_mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}
        name = 'name_set_from_argument'

        connection.initialize(name=name)

        host = config.config.get('database', 'seeds').split(':')[0]
        port = int(config.config.get('database', 'seeds').split(':')[1])
        mock_mongoengine.connect.assert_called_once_with(name, host=host, max_pool_size=10,
                                                         port=port)


class TestDatabaseReplicaSet(unittest.TestCase):

    def test_replica_set_default_does_not_exist(self):
        self.assertRaises(NoOptionError, config.config.get, 'database', 'replica_set')

    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    def test_database_sets_replica_set(self, mock_mongoengine):
        mock_replica_set = Mock()
        mock_mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}

        connection.initialize(replica_set=mock_replica_set)

        database = config.config.get('database', 'name')
        host = config.config.get('database', 'seeds').split(':')[0]
        port = int(config.config.get('database', 'seeds').split(':')[1])
        max_pool_size = connection._DEFAULT_MAX_POOL_SIZE
        mock_mongoengine.connect.assert_called_once_with(
            database, host=host, max_pool_size=max_pool_size, port=port,
            replicaset=mock_replica_set)

    @mock_config.patch({'database': {'replica_set': 'real_replica_set', 'name': 'nbachamps',
                                     'seeds': 'champs.example.com:27018'}})
    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    def test_database_replica_set_from_config(self, mock_mongoengine):
        """
        Assert that replica set configuration defaults to the configured value if not provided.
        """
        mock_mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}

        connection.initialize()

        max_pool_size = connection._DEFAULT_MAX_POOL_SIZE
        mock_mongoengine.connect.assert_called_once_with(
            'nbachamps', host='champs.example.com', max_pool_size=max_pool_size, port=27018,
            replicaset='real_replica_set')


class TestDatabaseMaxPoolSize(unittest.TestCase):

    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    def test_database_max_pool_size_default_is_10(self, mock_mongoengine):
        """
        Assert that the max_pool_size parameter defaults to 10.
        """
        mock_mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}

        connection.initialize()

        database = config.config.get('database', 'name')
        host = config.config.get('database', 'seeds').split(':')[0]
        port = int(config.config.get('database', 'seeds').split(':')[1])
        max_pool_size = connection._DEFAULT_MAX_POOL_SIZE
        mock_mongoengine.connect.assert_called_once_with(database, host=host,
                                                         max_pool_size=max_pool_size, port=port)

    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    def test_database_max_pool_size(self, mock_mongoengine):
        """
        Assert that the max_pool_size parameter to initialize() is handled appropriately.
        """
        mock_mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}

        connection.initialize(max_pool_size=5)

        database = config.config.get('database', 'name')
        host = config.config.get('database', 'seeds').split(':')[0]
        port = int(config.config.get('database', 'seeds').split(':')[1])
        mock_mongoengine.connect.assert_called_once_with(database, host=host,
                                                         max_pool_size=5, port=port)


class TestDatabase(unittest.TestCase):

    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    def test_mongoengine_connect_is_called(self, mock_mongoengine):
        """
        Assert that mongoengine.connect() is called.
        """
        mock_mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}

        connection.initialize()

        mock_mongoengine.connect.assert_called_once()

    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    def test__DATABASE_is_returned_from_get_db_call(self, mock_mongoengine):
        """
        This test asserts that pulp.server.db.connection._DATABASE is the result of calling get_db()
        on the connection.
        """
        mock_mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}

        connection.initialize()

        expected_database = mock_mongoengine.connection.get_db.return_value
        self.assertTrue(connection._DATABASE is expected_database)
        mock_mongoengine.connection.get_db.assert_called_once_with()

    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.NamespaceInjector')
    @patch('pulp.server.db.connection.mongoengine')
    def test__DATABASE_receives_namespace_injector(self, mock_mongoengine, mock_namespace_injector):
        """
        This test asserts that the NamespaceInjector was added as a son manipulator to the
        _DATABASE.
        """
        mock_mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}

        connection.initialize()

        mock_son_manipulator = connection._DATABASE.add_son_manipulator
        mock_namespace_injector.assert_called_once_with()
        mock_son_manipulator.assert_called_once_with(mock_namespace_injector.return_value)

    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    def test__DATABASE_collection_names_is_called(self, mock_mongoengine):
        """
        The initialize() method queries for all the collection names just to check that the
        connection is up and authenticated (if necessary). This way it can raise an Exception if
        there is a problem, rather than letting the first real query experience an Exception.
        """
        mock_mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}

        connection.initialize()

        connection._DATABASE.collection_names.assert_called_once_with()

    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    @patch('pulp.server.db.connection._logger')
    def test_unexpected_Exception_is_logged(self, mock__logger, mock_mongoengine):
        """
        Assert that the logger gets called when an Exception is raised by mongoengine.connect().
        """
        mock_mongoengine.connect.side_effect = IOError()

        self.assertRaises(IOError, connection.initialize)

        self.assertTrue(connection._CONNECTION is None)
        self.assertTrue(connection._DATABASE is None)
        mock__logger.critical.assert_called_once()


class TestDatabaseSSL(unittest.TestCase):

    def test_ssl_off_by_default(self):
        self.assertEqual(config.config.getboolean('database', 'ssl'), False)

    @mock_config.patch({'database': {'ssl': 'false', 'seeds': 'champs.example.com:27018'}})
    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    def test_ssl_is_skipped_if_off(self, mock_mongoengine):
        mock_mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}

        connection.initialize()

        database = config.config.get('database', 'name')
        max_pool_size = connection._DEFAULT_MAX_POOL_SIZE
        mock_mongoengine.connect.assert_called_once_with(database, max_pool_size=max_pool_size,
                                                         host='champs.example.com', port=27018)

    @mock_config.patch({'database': {'verify_ssl': 'true',
                                     'ssl': 'true', 'seeds': 'champs.example.com:27018'}})
    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.ssl')
    @patch('pulp.server.db.connection.mongoengine')
    def test_ssl_is_configured_with_verify_ssl_on(self, mock_mongoengine, mock_ssl):
        mock_mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}

        connection.initialize()

        database = config.config.get('database', 'name')
        max_pool_size = connection._DEFAULT_MAX_POOL_SIZE
        ssl_cert_reqs = mock_ssl.CERT_REQUIRED
        ssl_ca_certs = config.config.get('database', 'ca_path')
        mock_mongoengine.connect.assert_called_once_with(
            database, max_pool_size=max_pool_size, ssl=True, ssl_cert_reqs=ssl_cert_reqs,
            ssl_ca_certs=ssl_ca_certs, host='champs.example.com', port=27018)

    @mock_config.patch({'database': {'verify_ssl': 'false',
                                     'ssl': 'true', 'seeds': 'champs.example.com:27018'}})
    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.ssl')
    @patch('pulp.server.db.connection.mongoengine')
    def test_ssl_is_configured_with_verify_ssl_off(self, mock_mongoengine, mock_ssl):
        mock_mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}

        connection.initialize()

        database = config.config.get('database', 'name')
        max_pool_size = connection._DEFAULT_MAX_POOL_SIZE
        ssl_cert_reqs = mock_ssl.CERT_NONE
        ssl_ca_certs = config.config.get('database', 'ca_path')
        mock_mongoengine.connect.assert_called_once_with(
            database, max_pool_size=max_pool_size, ssl=True, ssl_cert_reqs=ssl_cert_reqs,
            ssl_ca_certs=ssl_ca_certs, host='champs.example.com', port=27018)

    @mock_config.patch({'database': {'ssl_keyfile': 'keyfilepath', 'verify_ssl': 'false',
                                     'ssl': 'true', 'seeds': 'champs.example.com:27018'}})
    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.ssl')
    @patch('pulp.server.db.connection.mongoengine')
    def test_ssl_is_configured_with_ssl_keyfile(self, mock_mongoengine, mock_ssl):
        mock_mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}

        connection.initialize()

        database = config.config.get('database', 'name')
        max_pool_size = connection._DEFAULT_MAX_POOL_SIZE
        ssl_cert_reqs = mock_ssl.CERT_NONE
        ssl_ca_certs = config.config.get('database', 'ca_path')
        mock_mongoengine.connect.assert_called_once_with(
            database, max_pool_size=max_pool_size, ssl=True, ssl_cert_reqs=ssl_cert_reqs,
            ssl_ca_certs=ssl_ca_certs, ssl_keyfile='keyfilepath', host='champs.example.com',
            port=27018)

    @mock_config.patch({'database': {'ssl_certfile': 'certfilepath', 'verify_ssl': 'false',
                                     'ssl': 'true', 'seeds': 'champs.example.com:27018'}})
    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.ssl')
    @patch('pulp.server.db.connection.mongoengine')
    def test_ssl_is_configured_with_ssl_certfile(self, mock_mongoengine, mock_ssl):
        mock_mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}

        connection.initialize()

        database = config.config.get('database', 'name')
        max_pool_size = connection._DEFAULT_MAX_POOL_SIZE
        ssl_cert_reqs = mock_ssl.CERT_NONE
        ssl_ca_certs = config.config.get('database', 'ca_path')
        mock_mongoengine.connect.assert_called_once_with(
            database, max_pool_size=max_pool_size, ssl=True, ssl_cert_reqs=ssl_cert_reqs,
            ssl_ca_certs=ssl_ca_certs, ssl_certfile='certfilepath', host='champs.example.com',
            port=27018)


class TestDatabaseVersion(unittest.TestCase):
    """
    test DB version parsing. Info on expected versions is at
    https://github.com/mongodb/mongo/blob/master/src/mongo/util/version.cpp#L39-45
    """

    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    def _test_initialize(self, version_str, mock_mongoengine):
        mock_mongoclient_connect = mock_mongoengine.connect.return_value
        mock_mongoclient_connect.server_info.return_value = {'version': version_str}

        connection.initialize()

    def test_database_version_bad_version(self):
        try:
            self._test_initialize('1.2.3')
            self.fail("RuntimeError not raised")
        except RuntimeError:
            pass  # expected exception

    def test_database_version_good_version(self):
        # the version check succeeded if no exception was raised
        self._test_initialize('2.6.0')

    def test_database_version_good_equal_version(self):
        # the version check succeeded if no exception was raised
        self._test_initialize('2.4.0')

    def test_database_version_good_rc_version(self):
        # the version check succeeded if no exception was raised
        self._test_initialize('2.8.0-rc1')

    def test_database_version_bad_rc_version(self):
        try:
            self._test_initialize('2.3.0-rc1')
            self.fail("RuntimeError not raised")
        except RuntimeError:
            pass  # expected exception


class TestDatabaseAuthentication(unittest.TestCase):

    @mock_config.patch(
        {'database': {'name': 'nbachamps', 'username': 'larrybird',
                      'password': 'celtics1981', 'seeds': 'champs.example.com:27018'}})
    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    def test_initialize_username_and_password(self, mock_mongoengine):
        """
        Assert that the connection is made correctly when a username and password are provided in
        the config.
        """
        mock_mongoengine_instance = mock_mongoengine.connect.return_value
        mock_mongoengine_instance.server_info.return_value = {"version":
                                                              connection.MONGO_MINIMUM_VERSION}

        connection.initialize()

        mock_mongoengine.connect.assert_called_once_with(
            'nbachamps', username='larrybird', host='champs.example.com',
            password='celtics1981', max_pool_size=10, port=27018)

    @mock_config.patch(
        {'database': {'name': 'nbachamps', 'username': 'larrybird',
                      'password': 'celtics1981', 'seeds': 'champs.example.com:27018'}})
    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection._logger.debug')
    @patch('pulp.server.db.connection.mongoengine')
    def test_initialize_username_and_shadows_password(self, mock_mongoengine, mock_log):
        """
        Assert that the password and password length are not logged.
        """
        mock_mongoengine_instance = mock_mongoengine.connect.return_value
        mock_mongoengine_instance.server_info.return_value = {"version":
                                                              connection.MONGO_MINIMUM_VERSION}

        connection.initialize()

        mock_mongoengine.connect.assert_called_once_with(
            'nbachamps', username='larrybird', host='champs.example.com',
            password='celtics1981', max_pool_size=10, port=27018)
        expected_calls = [
            call('Attempting username and password authentication.'),
            call("Connection Arguments: {'username': 'larrybird', 'host': 'champs.example.com', "
                 "'password': '*****', 'max_pool_size': 10, 'port': 27018}"),
            call('Querying the database to validate the connection.')]
        mock_log.assert_has_calls(expected_calls)

    @mock_config.patch({'database': {'username': '', 'password': ''}})
    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    def test_initialize_no_username_or_password(self, mock_mongoengine):
        """
        Assert that no call is made to authenticate() when the username and password are the empty
        string.
        """
        mock_mongoengine_instance = mock_mongoengine.connect.return_value
        mock_mongoengine_instance.server_info.return_value = {"version":
                                                              connection.MONGO_MINIMUM_VERSION}

        connection.initialize()

        self.assertFalse(connection._DATABASE.authenticate.called)

    @mock_config.patch({'database': {'username': 'admin', 'password': ''}})
    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    def test_initialize_username_no_password(self, mock_mongoengine):
        """
        Test that no Exception is raised if a DB username is provided without a password.
        """
        mock_mongoengine_instance = mock_mongoengine.connect.return_value
        mock_mongoengine_instance.server_info.return_value = {"version":
                                                              connection.MONGO_MINIMUM_VERSION}

        # ensure no exception is raised (redmine #708)
        connection.initialize()

    @mock_config.patch({'database': {'username': '', 'password': 'foo'}})
    @patch('pulp.server.db.connection.mongoengine')
    def test_initialize_password_no_username(self, mock_mongoengine):
        mock_mongoengine_instance = mock_mongoengine.connect.return_value
        mock_mongoengine_instance.server_info.return_value = {"version":
                                                              connection.MONGO_MINIMUM_VERSION}

        self.assertRaises(Exception, connection.initialize)

    @patch('pulp.server.db.connection.OperationFailure', new=MongoEngineConnectionError)
    @patch('pulp.server.db.connection.mongoengine')
    def test_authentication_fails_with_RuntimeError(self, mock_mongoengine):
        mock_mongoengine_instance = mock_mongoengine.connect.return_value
        mock_mongoengine_instance.server_info.return_value = {"version":
                                                              connection.MONGO_MINIMUM_VERSION}
        exc = MongoEngineConnectionError()
        exc.code = 18
        mock_mongoengine.connection.get_db.side_effect = exc
        self.assertRaises(RuntimeError, connection.initialize)


class TestDatabaseRetryOnInitialConnectionSupport(unittest.TestCase):

    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    @patch('pulp.server.db.connection.time.sleep', Mock())
    def test_retry_waits_when_mongoengine_connection_error_is_raised(self, mock_mongoengine):
        def break_out_on_second(*args, **kwargs):
            mock_mongoengine.connect.side_effect = StopIteration()
            raise MongoEngineConnectionError()

        mock_mongoengine.connect.side_effect = break_out_on_second
        mock_mongoengine.connection.ConnectionError = MongoEngineConnectionError

        self.assertRaises(StopIteration, connection.initialize)

    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.time.sleep')
    @patch('pulp.server.db.connection.mongoengine')
    def test_retry_sleeps_with_backoff(self, mock_mongoengine, mock_sleep):
        def break_out_on_second(*args, **kwargs):
            mock_sleep.side_effect = StopIteration()

        mock_sleep.side_effect = break_out_on_second
        mock_mongoengine.connect.side_effect = MongoEngineConnectionError()
        mock_mongoengine.connection.ConnectionError = MongoEngineConnectionError

        self.assertRaises(StopIteration, connection.initialize)

        mock_sleep.assert_has_calls([call(1), call(2)])

    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.time.sleep')
    @patch('pulp.server.db.connection.mongoengine')
    def test_retry_with_max_timeout(self, mock_mongoengine, mock_sleep):
        def break_out_on_second(*args, **kwargs):
            mock_sleep.side_effect = StopIteration()

        mock_sleep.side_effect = break_out_on_second
        mock_mongoengine.connect.side_effect = MongoEngineConnectionError()
        mock_mongoengine.connection.ConnectionError = MongoEngineConnectionError

        self.assertRaises(StopIteration, connection.initialize, max_timeout=1)

        mock_sleep.assert_has_calls([call(1), call(1)])

    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    @patch('pulp.server.db.connection.itertools')
    def test_retry_uses_itertools_chain_and_repeat(self, mock_itertools, mock_mongoengine):
        mock_mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}

        connection.initialize()

        mock_itertools.repeat.assert_called_once_with(32)
        mock_itertools.chain.assert_called_once_with([1, 2, 4, 8, 16],
                                                     mock_itertools.repeat.return_value)


class TestGetDatabaseFunction(unittest.TestCase):

    @patch('pulp.server.db.connection._DATABASE')
    def test_get_database(self, mock__DATABASE):
        self.assertEqual(mock__DATABASE, connection.get_database())


class TestGetConnectionFunction(unittest.TestCase):

    @patch('pulp.server.db.connection._CONNECTION')
    def test_get_connection(self, mock__CONNECTION):
        self.assertEqual(mock__CONNECTION, connection.get_connection())


class TestInitialize(unittest.TestCase):
    """
    This class contains tests for the initialize() function.
    """
    @patch('pulp.server.db.connection._CONNECTION', None)
    @patch('pulp.server.db.connection._DATABASE', None)
    @patch('pulp.server.db.connection.mongoengine')
    def test_multiple_calls_errors(self, mongoengine):
        """
        This test asserts that more than one call to initialize() raises a RuntimeError.
        """
        mongoengine.connect.return_value.server_info.return_value = {'version': '2.6.0'}
        # The first call to initialize should be fine
        connection.initialize()

        # A second call to initialize() should raise a RuntimeError
        self.assertRaises(RuntimeError, connection.initialize)

        # The connection should still be initialized
        self.assertEqual(connection._CONNECTION, mongoengine.connect.return_value)
        self.assertEqual(connection._DATABASE, mongoengine.connection.get_db.return_value)
        # Connect should still have been called correctly
        name = config.config.get('database', 'name')
        host = config.config.get('database', 'seeds').split(':')[0]
        port = int(config.config.get('database', 'seeds').split(':')[1])
        mongoengine.connect.assert_called_once_with(name, host=host, max_pool_size=10, port=port)
