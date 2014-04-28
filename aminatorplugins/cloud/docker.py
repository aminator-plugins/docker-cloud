# -*- coding: utf-8 -*-

#
#
#  Copyright 2014 Netflix, Inc.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
#

"""
aminatorplugins.cloud.docker
==========================
docker cloud provider
"""
import logging
from aminator.plugins.cloud.base import BaseCloudPlugin
from aminator.config import conf_action
from aminator.util.linux import monitor_command
from aminator.util import retry
from os import environ

__all__ = ('DockerCloudPlugin',)
log = logging.getLogger(__name__)

class DockerCloudPlugin(BaseCloudPlugin):
    _name = 'docker'

    def add_plugin_args(self, *args, **kwargs):
        context = self._config.context
        base_ami = self._parser.add_argument_group(title='Base Docker Image')
        base_ami.add_argument('-b', '--base-image', dest='base_image',
                              action=conf_action(config=context.ami), required=True,
                              help='The name of the base Docker image used in provisioning')
        base_ami.add_argument('-R', '--docker-registry', dest='docker_registry',
                              action=conf_action(config=context.cloud),
                              help='The private registry to push the docker image to')

    def connect(self, **kwargs): pass

    def registry(self):
        registry = self._config.context.cloud.get('docker_registry', None)
        if registry: return registry
        config = self._config.plugins[self.full_name]
        return config.get("docker_registry", None)
        
    @retry(tries=3,delay=2,backoff=2,logger=log)
    def allocate_base_volume(self, tag=True):
        context = self._config.context
        result = monitor_command(["docker", "pull", context.ami.base_image])
        if not result.success:
            log.error('failure:{0.command} :{0.std_err}'.format(result.result))
            return False
        return True

    @retry(tries=3,delay=2,backoff=2,logger=log)
    def attach_volume(self, blockdevice, tag=True):
        context = self._config.context
        result = monitor_command(["docker", "run", "-d", context.ami.base_image, "sleep", "infinity"])
        if not result.success:
            log.error('failure:{0.command} :{0.std_err}'.format(result.result))
            return False
        container = result.result.std_out.rstrip()
        context.cloud["container"] = container

        # # now we need to umount all the mount points that docker imports for us
        # with open("/proc/mounts") as f:
        #     mounts = f.readlines()
        # mountpoints = []
        # for mount in mounts:
        #     if container in mount:
        #         mountpoint = mount.split()[1]
        #         # keep the root mountpoint
        #         if mountpoint.endswith("/root"): continue
        #         if not mountpoint.startswith("/var/lib/docker/containers/"): continue
        #         mountpoints.append( mountpoint )
        # # unmount all the mountpoints in reverse order (in case we have mountpoints
        # # inside of mountpoints
        # for mountpoint in reversed(sorted(mountpoints)):
        #     result = unmount(mountpoint)
        #     if not result.success:
        #         log.error('failure:{0.command} :{0.std_err}'.format(result.result))
        #         return False
        return True

    @retry(tries=3,delay=2,backoff=2,logger=log)
    def detach_volume(self, blockdevice):
        result = monitor_command(["docker", "kill", self._config.context.cloud["container"]])
        if not result.success:
            log.error('failure:{0.command} :{0.std_err}'.format(result.result))
            return False

        return True

    @retry(tries=3,delay=2,backoff=2,logger=log)
    def delete_volume(self):
        context = self._config.context
        # docker rm $container
        result = monitor_command(["docker", "rm", context.cloud["container"]])
        if not result.success:
            log.error('failure:{0.command} :{0.std_err}'.format(result.result))
            return False

        name = "{}/{}".format(self.registry(), context.ami.name)
        result = monitor_command(["docker", "rmi", name])
        if not result.success:
            log.error('failure:{0.command} :{0.std_err}'.format(result.result))
            return False
        return True

    def snapshot_volume(self, description=None):
        context = self._config.context
        name = "{}/{}".format(self.registry(), context.ami.name)
        result = monitor_command(["docker", "commit", self._config.context.cloud["container"], name])
        if not result.success:
            log.error('failure:{0.command} :{0.std_err}'.format(result.result))
            return False
        return True

    def is_volume_attached(self, blockdevice): pass

    def is_stale_attachment(self, dev, prefix): pass

    def attached_block_devices(self, prefix): pass

    def add_tags(self, resource_type): pass

    @retry(tries=3,delay=2,backoff=2,logger=log)
    def register_image(self, *args, **kwargs):
        context = self._config.context
        name = "{}/{}".format(self.registry(), context.ami.name)
        result = monitor_command(["docker", "push", name])
        if not result.success:
            log.error('failure:{0.command} :{0.std_err}'.format(result.result))
            return False
        log.info('Docker Image registered: {0}'.format(name))
        return True

    def __enter__(self):
        self.connect()
        context = self._config.context
        if context.ami.get("base_image",None):
            environ["AMINATOR_DOCKER_BASE_IMAGE"] = context.ami.base_image
        if context.cloud.get("docker_registry",None):
            environ["AMINATOR_DOCKER_REGISTRY"] = context.cloud.docker_registry
        return self
