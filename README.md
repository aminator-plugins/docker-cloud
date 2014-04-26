Docker Plugin for NetflixOSS Amainator
============

aminator plugins to allow creation of docker images

Warning: This is experimental, use at your own risk.

Examples
--------

```
$ sudo aminate -e docker_aptitude --base-image ubuntu:14.04 --suffix $(date +%Y%m%d%H%M) --docker-registry myregister.company.com:8080 /tmp/mypackage_1.0-409e639_all.deb 
```

Installation
------------

First, install Aminator, then install the Docker plugin for Aminator:

```
$ sudo aminator-plugin install docker
```

Then you will need to make add an environment that uses the Docker plugins to your `/etc/aminator/environments.yml` file. For example:

```
docker_yum:
    cloud: docker
    distro: redhat
    provisioner: yum
    volume: docker
    blockdevice: "null"
    finalizer: docker
docker_apt:
    cloud: docker
    distro: debian
    provisioner: apt
    volume: docker
    blockdevice: "null"
    finalizer: docker
docker_aptitude:
    cloud: docker
    distro: debian
    provisioner: aptitude
    volume: docker
    blockdevice: "null"
    finalizer: docker
```

You might want to set the default docker register to use.  You can do that with this:
```
cat <<EOM > /etc/aminator/plugins/aminatorplugins.cloud.docker.yml 
enabled: true
docker_registry: myregister.company.com:8080
EOM
```

License
-------

Copyright 2014 Netflix, Inc.

Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain
a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable
law or agreed to in writing, software distributed under the License is
distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. See the License for the specific
language governing permissions and limitations under the License.

