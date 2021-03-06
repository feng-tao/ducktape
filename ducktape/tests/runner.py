# Copyright 2015 Confluent Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from ducktape.tests.result import TestResult, TestResults
from ducktape.tests.test import TestContext

import logging
import time
import traceback


class TestRunner(object):
    """Abstract class responsible for running one or more tests."""
    def __init__(self, session_context, tests):
        self.tests = tests
        self.session_context = session_context
        self.results = TestResults(self.session_context)
        self.cluster = session_context.cluster
        self.logger = session_context.logger

        self.logger.debug("Instantiating " + self.who_am_i())

    def who_am_i(self):
        """Human-readable name helpful for logging."""
        return self.__class__.__name__

    def run_all_tests(self):
        raise NotImplementedError()


def create_test_case(test, session_context):
    """Create test context object and instantiate test class.

    :type test_class: ducktape.tests.test.Test.__class__
    :type session_context: ducktape.tests.session.SessionContext
    :rtype test_class
    """

    test_class = test.im_class
    test_context = TestContext(session_context, test_class.__module__, test_class, test, config=None)
    return (test_context, test_class(test_context))


class SerialTestRunner(TestRunner):
    """Runs tests serially."""

    # When set to True, the test runner will finish running/cleaning the current test, but it will not run any more
    stop_testing = False

    def __init__(self, *args, **kwargs):
        super(SerialTestRunner, self).__init__(*args, **kwargs)
        self.current_test = None
        self.current_test_context = None

    def run_all_tests(self):

        self.results.start_time = time.time()
        for test in self.tests:
            # Create single testable unit and corresponding test result object
            self.current_test_context, self.current_test = create_test_case(test, self.session_context)
            result = TestResult(self.current_test_context, self.current_test_context.test_name)

            # Run the test unit
            try:
                self.log(logging.INFO, "setting up")
                self.setup_single_test()

                self.log(logging.INFO, "running")
                result.start_time = time.time()
                result.data = self.run_single_test()
                self.log(logging.INFO, "PASS")

            except BaseException as e:
                self.log(logging.INFO, "FAIL")
                result.success = False
                result.summary += e.message + "\n" + traceback.format_exc(limit=16)

                self.stop_testing = self.session_context.exit_first or isinstance(e, KeyboardInterrupt)

            finally:
                self.log(logging.INFO, "tearing down")
                self.teardown_single_test()
                result.stop_time = time.time()
                self.results.append(result)
                self.current_test_context, self.current_test = None, None

            if self.stop_testing:
                break

        self.results.stop_time = time.time()
        return self.results

    def setup_single_test(self):
        """start services etc"""

        self.log(logging.DEBUG, "Checking if there are enough nodes...")
        if self.current_test.min_cluster_size() > self.cluster.num_available_nodes():
            raise RuntimeError(
                "There are not enough nodes available in the cluster to run this test. Needed: %d, Available: %d" %
                (self.current_test.min_cluster_size(), self.cluster.num_available_nodes()))

        self.current_test.setUp()

    def run_single_test(self):
        """Run the test!"""
        return self.current_test_context.function(self.current_test)

    def teardown_single_test(self):
        """teardown method which stops services, gathers log data, removes persistent state, and releases cluster nodes.

        Catch all exceptions so that every step in the teardown process is tried, but signal that the test runner
        should stop if a keyboard interrupt is caught.
        """
        exceptions = []
        if hasattr(self.current_test_context, 'services'):
            services = self.current_test_context.services
            try:
                services.stop_all()
            except BaseException as e:
                exceptions.append(e)
                self.log(logging.WARN, "Error stopping services: %s" % e.message + "\n" + traceback.format_exc(limit=16))

            try:
                self.current_test.copy_service_logs()
            except BaseException as e:
                exceptions.append(e)
                self.log(logging.WARN, "Error copying service logs: %s" % e.message + "\n" + traceback.format_exc(limit=16))

            try:
                services.clean_all()
            except BaseException as e:
                exceptions.append(e)
                self.log(logging.WARN, "Error cleaning services: %s" % e.message + "\n" + traceback.format_exc(limit=16))

        try:
            self.current_test.free_nodes()
        except BaseException as e:
            exceptions.append(e)
            self.log(logging.WARN, "Error freeing nodes: %s" % e.message + "\n" + traceback.format_exc(limit=16))

        if len([e for e in exceptions if isinstance(e, KeyboardInterrupt)]) > 0:
            # Signal no more tests if we caught a keyboard interrupt
            self.stop_testing = True

    def log(self, log_level, msg):
        """Log to the service log and the test log of the given test."""
        msg = "%s: %s: %s" % (self.who_am_i(), self.current_test_context.test_name, msg)
        self.logger.log(log_level, msg)
        self.current_test.logger.log(log_level, msg)






