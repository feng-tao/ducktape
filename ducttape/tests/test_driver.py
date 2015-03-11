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

from camus_test import CamusHadoopV1Test, CamusHadoopV2Test, CamusHDPTest
from everything_runs_test import EverythingRunsTest
from hadoop_test import HadoopV1SetupTest, HadoopV2SetupTest, HDPSetupTest
from kafka_benchmark import KafkaBenchmark
from native_vs_rest_performance import NativeVsRestConsumerPerformance, NativeVsRestProducerPerformance
from schema_registry_benchmark import SchemaRegistryBenchmark
from sr_kafka_broker_failover import KafkaLeaderCleanFailover, KafkaLeaderHardFailover, KafkaBrokerCleanBounce, KafkaBrokerHardBounce
from sr_master_failover import MasterCleanFailover, MasterHardFailover, CleanBounce, HardBounce
from ducttape.logger import Logger
from ducttape.cluster import VagrantCluster
import time, logging


class TestDriver(Logger):

    def discover_tests(self):
        # test_classes = [
        #     CamusHadoopV1Test,
        #     CamusHadoopV2Test,
        #     CamusHDPTest,
        #     EverythingRunsTest,
        #     HadoopV1SetupTest,
        #     HadoopV2SetupTest,
        #     HDPSetupTest,
        #     KafkaBenchmark,
        #     NativeVsRestConsumerPerformance,
        #     NativeVsRestProducerPerformance,
        #     SchemaRegistryBenchmark,
        #     KafkaLeaderCleanFailover,
        #     KafkaLeaderHardFailover,
        #     KafkaBrokerCleanBounce,
        #     KafkaBrokerHardBounce,
        #     MasterCleanFailover,
        #     MasterHardFailover,
        #     CleanBounce,
        #     HardBounce
        # ]

        test_classes = [
            MasterCleanFailover
        ]

        return test_classes

    def setup(self, log_level=logging.INFO):
        logging.basicConfig(level=log_level)
        self.tests = self.discover_tests()
        self.cluster = VagrantCluster()

    def teardown(self):
        pass

    def run_test(self, test_class):
        """Run one test."""
        test = test_class(self.cluster)

        if test.min_cluster_size() > self.cluster.num_available_nodes():
            raise RuntimeError(
                "There are not enough nodes available in the cluster to run this test. Needed: %d, Available: %d" %
                (test_class.min_cluster_size(), self.cluster.num_available_nodes()))

        test.log_start()
        test.run()

    def run_all(self):
        for test in self.tests:
            try:
                for node in self.cluster.all_nodes:
                    node.kill_process("java", clean_shutdown=True, allow_fail=True)
                    time.sleep(1)
                for node in self.cluster.all_nodes:
                    time.sleep(1)
                    node.kill_process("java", clean_shutdown=False, allow_fail=True)
            except Exception as e:
                print "Error while trying to clean up processes: %s" % e.message

            try:
                self.run_test(test)
                time.sleep(.5)
            except Exception as e:
                print "Error while running %s: %s" % (test, e.message)
            finally:
                # try to consolidate logs
                # try to clean up
                pass


def main():
    test_driver = TestDriver()
    test_driver.setup()
    test_driver.run_all()
    test_driver.teardown()


if __name__ == "__main__":
    main()