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

from .test import Test
from ducttape.services.core import ZookeeperService
import time


class SimpleZkTest(Test):
    """ Tiny test to help set up nightly run process.
    """
    def __init__(self, cluster):
        self.cluster = cluster
        self.num_zk = 1

    def min_cluster_size(self):
        return self.num_zk

    def run(self):
        self.zk = ZookeeperService(self.cluster, self.num_zk)
        self.zk.start()

        time.sleep(10)
        self.zk.stop()

        self.logger.info("All proceeded smoothly.")

if __name__ == "__main__":
    EverythingRunsTest.run_standalone()