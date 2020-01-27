# -*- coding: utf-8 -*-

""" Sahana Eden Setup Model:
        * Installation of a Deployment
        * Configuration of a Deployment
        * Managing a Deployment (Start/Stop/Clean instances)
        * Monitoring of a Deployment
        * Upgrading a Deployment (tbc)

    @copyright: 2015-2020 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ("S3DNSModel",
           "S3GandiDNSModel",
           "S3CloudModel",
           "S3AWSCloudModel",
           "S3SetupModel",
           "S3SetupMonitorModel",
           #"Storage2",
           #"setup_DeploymentRepresent",
           "setup_monitor_run_task",
           "setup_monitor_check_email_reply",
           "setup_instance_settings_read",
           #"setup_write_playbook",
           "setup_run_playbook",
           "setup_rheader",
           )

import json
import os
import random
import string
import sys
import time

from gluon import *

from ..s3 import *
from s3compat import basestring

TIME_FORMAT = "%b %d %Y %H:%M:%S"
MSG_FORMAT = "%(now)s - %(category)s - %(data)s\n\n"

WEB_SERVERS = {#1: "apache",
               2: "cherokee",
               3: "nginx",
               }

DB_SERVERS = {#1: "mysql",
              2: "postgresql",
              ##3: "sqlite",
              }

INSTANCE_TYPES = {1: "prod",
                  2: "setup",
                  3: "test",
                  4: "demo",
                  }

# =============================================================================
class S3DNSModel(S3Model):
    """
        Domain Name System (DNS) Providers
        - super-entity
    """

    names = ("setup_dns",
             "setup_dns_id",
             )

    def model(self):

        T = current.T
        db = current.db

        #----------------------------------------------------------------------
        # Super entity
        #
        dns_types = Storage(setup_gandi_dns = T("Gandi LiveDNS"),
                            )

        tablename = "setup_dns"
        self.super_entity(tablename, "dns_id",
                          dns_types,
                          Field("name",
                                #label = T("Name"),
                                ),
                          Field("description",
                                #label = T("Description"),
                                ),
                          #Field("enabled", "boolean",
                          #      default = True,
                          #      #label = T("Enabled?")
                          #      #represent = s3_yes_no_represent,
                          #      ),
                          #on_define = lambda table: \
                          #  [table.instance_type.set_attributes(readable = True),
                          #   ],
                          )

        # Reusable Field
        represent = S3Represent(lookup = tablename)
        dns_id = S3ReusableField("dns_id", "reference %s" % tablename,
                                 label = T("DNS Provider"),
                                 ondelete = "SET NULL",
                                 represent = represent,
                                 requires = IS_EMPTY_OR(
                                    IS_ONE_OF(db, "setup_dns.dns_id",
                                              represent,
                                              sort = True
                                              ),
                                    ),
                                 )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return {"setup_dns_id": dns_id,
                }

# =============================================================================
class S3GandiDNSModel(S3DNSModel):
    """
        Gandi LiveDNS
        - DNS Provider Instance

        https://doc.livedns.gandi.net/
    """

    names = ("setup_gandi_dns",)

    def model(self):

        #T = current.T

        # ---------------------------------------------------------------------
        tablename = "setup_gandi_dns"
        self.define_table(tablename,
                          self.super_link("dns_id", "setup_dns"),
                          Field("name"),
                          Field("description"),
                          #Field("enabled", "boolean",
                          #      default = True,
                          #      #label = T("Enabled?"),
                          #      represent = s3_yes_no_represent,
                          #      ),
                          Field("api_key", "password",
                                readable = False,
                                requires = IS_NOT_EMPTY(),
                                widget = S3PasswordWidget(),
                                ),
                          # Currently only supports a single Domain per DNS configuration
                          Field("domain", # Name
                                requires = IS_NOT_EMPTY(),
                                ),
                          # Currently only supports a single Zone per DNS configuration
                          Field("zone", # UUID
                                requires = IS_NOT_EMPTY(),
                                ),
                          *s3_meta_fields())

        self.configure(tablename,
                       super_entity = "setup_dns",
                       )

        # ---------------------------------------------------------------------
        return {}

# =============================================================================
class S3CloudModel(S3Model):
    """
        Clouds
        - super-entity
    """

    names = ("setup_cloud",
             "setup_cloud_id",
             )

    def model(self):

        T = current.T
        db = current.db

        #----------------------------------------------------------------------
        # Super entity
        #
        cloud_types = Storage(setup_aws_cloud = T("Amazon Web Services"),
                              )

        tablename = "setup_cloud"
        self.super_entity(tablename, "cloud_id",
                          cloud_types,
                          Field("name",
                                #label = T("Name"),
                                ),
                          Field("description",
                                #label = T("Description"),
                                ),
                          #Field("enabled", "boolean",
                          #      default = True,
                          #      #label = T("Enabled?")
                          #      #represent = s3_yes_no_represent,
                          #      ),
                          #on_define = lambda table: \
                          #  [table.instance_type.set_attributes(readable = True),
                          #   ],
                          )

        # Reusable Field
        represent = S3Represent(lookup = tablename)
        cloud_id = S3ReusableField("cloud_id", "reference %s" % tablename,
                                   label = T("Cloud"),
                                   ondelete = "SET NULL",
                                   represent = represent,
                                   requires = IS_EMPTY_OR(
                                    IS_ONE_OF(db, "setup_cloud.cloud_id",
                                              represent,
                                              sort = True
                                              ),
                                    ),
                                   )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return {"setup_cloud_id": cloud_id,
                }

# =============================================================================
class S3AWSCloudModel(S3CloudModel):
    """
        Amazon Web Services
        - Cloud Instance

        https://docs.ansible.com/ansible/latest/scenario_guides/guide_aws.html
        https://docs.ansible.com/ansible/latest/modules/ec2_module.html
    """

    names = ("setup_aws_cloud",
             "setup_aws_server",
             )

    def model(self):

        #T = current.T

        configure = self.configure
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # AWS Cloud Configuration
        #
        tablename = "setup_aws_cloud"
        define_table(tablename,
                     # Instance of Super-Entity
                     self.super_link("cloud_id", "setup_cloud"),
                     Field("name"),
                     Field("description"),
                     #Field("enabled", "boolean",
                     #      default = True,
                     #      #label = T("Enabled?"),
                     #      represent = s3_yes_no_represent,
                     #      ),
                     Field("secret_key", "password",
                           readable = False,
                           requires = IS_NOT_EMPTY(),
                           widget = S3PasswordWidget(),
                           ),
                     Field("access_key", "password",
                           readable = False,
                           requires = IS_NOT_EMPTY(),
                           widget = S3PasswordWidget(),
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  super_entity = "setup_cloud",
                  )

        # ---------------------------------------------------------------------
        # AWS Server Details
        #
        #aws_instance_types = ["t3.micro",
        #                      ]
        #aws_regions = {"eu-west-2": "Europe (London)",
        #               }
        tablename = "setup_aws_server"
        define_table(tablename,
                     self.setup_server_id(),
                     Field("region",
                           default = "eu-west-2", # Europe (London)
                           #label = T("Region"),
                           #requires = IS_IN_SET(aws_regions),
                           #represent = S3Represent(options = aws_regions)
                           ),
                     Field("instance_type",
                           default = "t3.micro",
                           #label = T("Instance Type"),
                           #requires = IS_IN_SET(aws_instance_types),
                           ),
                     Field("image",
                           default = "ami-0ad916493173c5680", # Debian 9 in London
                           #label = T("Image"), # AMI ID
                           ),
                     Field("security_group",
                           default = "default",
                           #label = T("Security Group"),
                           ),
                     # Normally populated automatically:
                     Field("instance_id",
                           #label = T("Instance ID"),
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  ondelete = self.setup_aws_server_ondelete,
                  )

        # ---------------------------------------------------------------------
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_aws_server_ondelete(row):
        """
            Cleanup Tasks when a Server is Deleted
            - AWS Instance
            - AWS Keypair
        """

        s3db = current.s3db
        stable = s3db.setup_server
        astable = s3db.setup_aws_server
        dtable = s3db.setup_deployment
        atable = s3db.setup_aws_cloud

        query = (stable.id == row.server_id) & \
                (astable.server_id == stable.id) & \
                (dtable.id == stable.deployment_id) & \
                (dtable.cloud_id == atable.id)
        deployment = current.db(query).select(atable.access_key,
                                              atable.secret_key,
                                              astable.region, # Only deleted_fks are in the row object
                                              stable.name,
                                              limitby = (0, 1)
                                              ).first()

        server_name = deployment["setup_server.name"]
        region = deployment["setup_aws_server.region"]
        aws = deployment["setup_aws_cloud"]
        access_key = aws.access_key
        secret_key = aws.secret_key

        playbook = [{"hosts": "localhost",
                     "connection": "local",
                     "gather_facts": "no",
                     "tasks": [# Terminate AWS Instance
                               {"ec2": {"aws_access_key": access_key,
                                        "aws_secret_key": secret_key,
                                        "region": region,
                                        "instance_ids": row.instance_id,
                                        "state": "absent",
                                        },
                                    },
                               # Delete Keypair
                               {"ec2_key": {"aws_access_key": access_key,
                                            "aws_secret_key": secret_key,
                                            "region": region,
                                            "name": server_name,
                                            "state": "absent",
                                            },
                                },
                               ],
                     },
                    ]

        # Write Playbook
        name = "aws_server_ondelete_%d" % int(time.time())
        task_vars = setup_write_playbook("%s.yml" % name,
                                         playbook,
                                         )

        # Run Playbook
        current.s3task.schedule_task(name,
                                     vars = task_vars,
                                     function_name = "setup_run_playbook",
                                     repeats = None,
                                     timeout = 6000,
                                     #sync_output = 300
                                     )

# =============================================================================
class S3SetupModel(S3Model):

    names = ("setup_deployment",
             "setup_deployment_id",
             "setup_server",
             "setup_server_id",
             "setup_instance",
             "setup_setting",
             )

    def model(self):

        T = current.T
        db = current.db

        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        set_method = self.set_method

        folder = current.request.folder
        path_join = os.path.join
        template_path = path_join(folder, "modules", "templates")

        # ---------------------------------------------------------------------
        # Deployments
        #
        tablename = "setup_deployment"
        define_table(tablename,
                     # @ToDo: Allow use of a Custom repo
                     # @ToDo: Add ability to get a specific hash/tag
                     Field("repo_url",
                           # @ToDo: Switch to Stable once it has a templates.txt
                           #default = "https://github.com/sahana/eden-stable",
                           default = "https://github.com/sahana/eden",
                           label = T("Eden Repository"),
                           requires = IS_URL(),
                           readable = False,
                           writable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Eden Repository"),
                                                           T("If you wish to use your own Fork, then you can set this here")
                                                           )
                                         ),
                           ),
                     Field("country",
                           label = T("Country"),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET_LAZY(lambda: self.setup_get_countries(template_path),
                                                       zero = current.messages.SELECT_LOCATION,
                                                       )),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Country"),
                                                           T("Selecting your country means that the appropriate locale settings can be applied. If you need to support multiple countries then you may need to create a custom template.")
                                                           )
                                         ),
                           ),
                     Field("template", "list:string",
                           default = ["default"],
                           label = T("Template"),
                           requires = IS_IN_SET_LAZY(lambda: self.setup_get_templates(template_path),
                                                     multiple = True,
                                                     zero = None,
                                                     ),
                           ),
                     Field("webserver_type", "integer",
                           default = 3,
                           label = T("Web Server"),
                           represent = S3Represent(options = WEB_SERVERS),
                           requires = IS_IN_SET(WEB_SERVERS),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Web Server"),
                                                           T("Currently only Nginx and Cherokee is supported by this tool, although Apache should be possible with a little work.")
                                                           )
                                         ),
                           ),
                     Field("db_type", "integer",
                           default = 2,
                           label = T("Database"),
                           represent = S3Represent(options = DB_SERVERS),
                           requires = IS_IN_SET(DB_SERVERS),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Database"),
                                                           T("Currently only PostgreSQL is supported by this tool, although MySQL should be possible with a little work.")
                                                           )
                                         ),
                           ),
                     # Set automatically
                     Field("db_password", "password",
                           readable = False,
                           writable = False,
                           ),
                     self.setup_cloud_id(),
                     self.setup_dns_id(),
                     *s3_meta_fields()
                     )

        crud_strings[tablename] = Storage(
            label_create = T("Create Deployment"),
            title_display = T("Deployment Details"),
            title_list =  T("Deployments"),
            title_update = T("Edit Deployment"),
            label_list_button =  T("List Deployments"),
            label_delete_button = T("Delete Deployment"),
            msg_record_created = T("Deployment added"),
            msg_record_modified = T("Deployment updated"),
            msg_record_deleted = T("Deployment deleted"),
            msg_list_empty = T("No Deployments currently registered"))

        configure(tablename,
                  #editable = False,
                  listadd = False, # Create method customises form
                  create_onaccept = self.setup_deployment_create_onaccept,
                  create_next = URL(c="setup", f="deployment",
                                    args = ["[id]", "instance"],
                                    ),
                  list_fields = ["production.url",
                                 "country",
                                 "template",
                                 "webserver_type",
                                 "db_type",
                                 ],
                  )

        add_components(tablename,
                       setup_instance = (# All instances:
                                         "deployment_id",
                                         # Production instance:
                                         {"name": "production",
                                          "joinby": "deployment_id",
                                          "filterby": {
                                              "type": 1,
                                              },
                                          "multiple": False,
                                          },
                                         ),
                       setup_monitor_task = "deployment_id",
                       setup_server = (# All instances:
                                       "deployment_id",
                                       # Production instance:
                                       {"name": "production_server",
                                        "joinby": "deployment_id",
                                        "filterby": {
                                            "role": 1,
                                            },
                                        "multiple": False,
                                        },
                                       ),
                       setup_setting = "deployment_id",
                       )

        set_method("setup", "deployment",
                   method = "wizard",
                   action = self.setup_server_wizard)

        represent = setup_DeploymentRepresent()

        deployment_id = S3ReusableField("deployment_id", "reference %s" % tablename,
                                        label = T("Deployment"),
                                        ondelete = "CASCADE",
                                        represent = represent,
                                        requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "setup_deployment.id",
                                                              represent,
                                                              sort=True
                                                              )),
                                        sortby = "name",
                                        )

        # ---------------------------------------------------------------------
        # Servers
        #
        SERVER_ROLES = {1: "all",
                        2: "db",
                        #3: "webserver",
                        #4: "eden",
                        }

        tablename = "setup_server"
        define_table(tablename,
                     # @ToDo: Server Groups
                     #group_id(),
                     deployment_id(),
                     Field("name",
                           label = T("Name"),
                           # Can do this in templates if-required
                           #requires = IS_NOT_IN_DB(db, "setup_server.name"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Name"),
                                                           # If not defined then can be automated by the Cloud integration, if-present
                                                           T("Optional.")
                                                           )
                                         ),
                           ),
                     Field("host_ip", length=24,
                           label = T("IP Address"),
                           # required for non-cloud deployments (set in controller)
                           requires = IS_EMPTY_OR(
                                        IS_IPV4(),
                                        ),
                           #writable = False,
                           comment = DIV(_class="tooltip",
                                         # If not defined then can be automated by the Cloud integration, if-present
                                         _title="%s|%s" % (T("IP Address"),
                                                           T("Currently only 127.0.0.1 is supported by this tool, although others should be possible with a little work.")
                                                           )
                                         ),
                           ),
                     Field("role", "integer",
                           default = 1,
                           label = T("Role"),
                           represent = S3Represent(options = SERVER_ROLES),
                           requires = IS_IN_SET(SERVER_ROLES),
                           writable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Role"),
                                                           T("Currently only 'all' is supported by this tool, although others should be possible with a little work.")
                                                           )
                                         ),
                           ),
                     Field("remote_user",
                           default = "admin",
                           label = T("Remote User"),
                           ),
                     Field("private_key", "upload",
                           label = T("SSH Private Key"),
                           length = current.MAX_FILENAME_LENGTH,
                           requires = IS_EMPTY_OR(IS_UPLOAD_FILENAME()),
                           uploadfolder = path_join(folder, "uploads"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("SSH Private Key"),
                                                           T("if you wish to configure servers other than the one hosting the co-app then you need to provide a PEM-encoded SSH private key")
                                                           )
                                         ),
                           ),
                     *s3_meta_fields()
                     )

        crud_strings[tablename] = Storage(
            label_create = T("Add Server"),
            title_display = T("Server Details"),
            title_list =  T("Servers"),
            title_update = T("Edit Server"),
            label_list_button =  T("List Servers"),
            label_delete_button = T("Delete Server"),
            msg_record_created = T("Server added"),
            msg_record_modified = T("Server updated"),
            msg_record_deleted = T("Server deleted"),
            msg_list_empty = T("No Servers currently registered"))

        add_components(tablename,
                       setup_aws_server = {"joinby": "server_id",
                                           "multiple": False,
                                           },
                       setup_monitor_run = {"name": "monitor_log",
                                            "joinby": "server_id",
                                            },
                       setup_monitor_server = {"joinby": "server_id",
                                               "multiple": False,
                                               },
                       setup_monitor_task = "server_id",
                       )

        # @ToDo: Add represented Deployment/Role
        represent = S3Represent(lookup=tablename, fields=["host_ip"])

        server_id = S3ReusableField("server_id", "reference %s" % tablename,
                                    label = T("Server"),
                                    ondelete = "CASCADE",
                                    represent = represent,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "setup_server.id",
                                                          represent,
                                                          sort=True
                                                          )),
                                    sortby = "host_ip",
                                    )

        set_method("setup", "server",
                   method = "enable",
                   action = setup_monitor_server_enable_interactive)

        set_method("setup", "server",
                   method = "disable",
                   action = setup_monitor_server_disable_interactive)

        set_method("setup", "server",
                   method = "check",
                   action = setup_monitor_server_check)

        # ---------------------------------------------------------------------
        # Instances
        #
        # @ToDo: Allow a Test instance to source Prod data from a different deployment
        #        - to allow it to be run on different hosts (or even different cloud)
        #
        type_represent = S3Represent(options = INSTANCE_TYPES)

        tablename = "setup_instance"
        define_table(tablename,
                     deployment_id(),
                     Field("type", "integer",
                           default = 1,
                           label = T("Type"),
                           represent = type_represent,
                           requires = IS_IN_SET(INSTANCE_TYPES),
                           ),
                     Field("url",
                           label = T("URL"),
                           requires = IS_URL(),
                           represent = lambda opt: A(opt,
                                                     _href = opt,
                                                     _target="_blank",
                                                     ),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("URL"),
                                                           T("The Public URL which will be used to access the instance")
                                                           )
                                         ),
                           ),
                     # @ToDo: Allow upload of SSL as well as auto-generated Let's Encrypt
                     #Field("ssl_cert", "upload",
                     #      label = T("SSL Certificate"),
                     #      length = current.MAX_FILENAME_LENGTH,
                     #      requires = IS_EMPTY_OR(IS_UPLOAD_FILENAME()),
                     #      uploadfolder = path_join(folder, "uploads"),
                     #      comment = DIV(_class="tooltip",
                     #                    _title="%s|%s" % (T("SSL Certificate"),
                     #                                      T("If not using Let's Encrypt e.g. you wish to use an OV or EV certificate")
                     #                                      )
                     #                    ),
                     #      ),
                     #Field("ssl_key", "upload",
                     #      label = T("SSL Key"),
                     #      length = current.MAX_FILENAME_LENGTH,
                     #      requires = IS_EMPTY_OR(IS_UPLOAD_FILENAME()),
                     #      uploadfolder = path_join(folder, "uploads"),
                     #      comment = DIV(_class="tooltip",
                     #                    _title="%s|%s" % (T("SSL Key"),
                     #                                      T("If not using Let's Encrypt e.g. you wish to use an OV or EV certificate")
                     #                                      )
                     #                    ),
                     #      ),
                     Field("sender",
                           label = T("Email Sender"),
                           requires = IS_EMPTY_OR(
                                        IS_EMAIL()),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Email Sender"),
                                                           T("The Address which you want Outbound Email to be From. Not setting this means that Outbound Email is Disabled.")
                                                           )
                                         ),
                           ),
                     # @ToDo: Action post-deployment changes
                     Field("start", "boolean",
                           default = True, # default = False in Controller for additional instances
                           label = T("Start at Boot"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("task_id", "reference scheduler_task",
                           label = T("Scheduled Task"),
                           represent = lambda opt: \
                            A(opt,
                              _href = URL(c="appadmin", f="update",
                                          args = ["db", "scheduler_task", opt]),
                              ) if opt else current.messages["NONE"],
                           writable = False,
                           ),
                     Field("log_file", "upload",
                           label = T("Log File"),
                           length = current.MAX_FILENAME_LENGTH,
                           requires = IS_EMPTY_OR(IS_UPLOAD_FILENAME()),
                           uploadfolder = path_join(folder, "uploads"),
                           writable = False,
                           ),
                     # Has the Configuration Wizard been run?
                     Field("configured", "boolean",
                           default = False,
                           #represent = s3_yes_no_represent,
                           readable = False,
                           writable = False,
                           ),
                     *s3_meta_fields()
                     )

        crud_strings[tablename] = Storage(
            label_create = T("Add Instance"),
            title_display = T("Instance Details"),
            title_list =  T("Instances"),
            title_update = T("Edit Instance"),
            label_list_button =  T("List Instances"),
            label_delete_button = T("Delete Instance"),
            msg_record_created = T("Instance added"),
            msg_record_modified = T("Instance updated"),
            msg_record_deleted = T("Instance deleted"),
            msg_list_empty = T("No Instances currently registered"))

        configure(tablename,
                  list_fields = ["type",
                                 "url",
                                 "start",
                                 "task_id",
                                 "log_file",
                                 ],
                  ondelete = self.setup_instance_ondelete,
                  )

        set_method("setup", "deployment",
                   component_name = "instance",
                   method = "deploy",
                   action = self.setup_instance_deploy,
                   )

        set_method("setup", "deployment",
                   component_name = "instance",
                   method = "settings",
                   action = self.setup_instance_settings,
                   )

        set_method("setup", "deployment",
                   component_name = "instance",
                   method = "start",
                   action = self.setup_instance_start,
                   )

        set_method("setup", "deployment",
                   component_name = "instance",
                   method = "stop",
                   action = self.setup_instance_stop,
                   )

        set_method("setup", "deployment",
                   component_name = "instance",
                   method = "clean",
                   action = self.setup_instance_clean,
                   )

        set_method("setup", "deployment",
                   component_name = "instance",
                   method = "wizard",
                   action = self.setup_instance_wizard,
                   )

        represent = S3Represent(lookup = tablename,
                                fields = ["type"],
                                labels = lambda row: type_represent(row.type))

        instance_id = S3ReusableField("instance_id", "reference %s" % tablename,
                                      label = T("Instance"),
                                      ondelete = "CASCADE",
                                      represent = represent,
                                      requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "setup_instance.id",
                                                              represent,
                                                              sort=True
                                                              )),
                                      sortby = "name",
                                      )

        # ---------------------------------------------------------------------
        # Settings in models/000_config.py
        #
        tablename = "setup_setting"
        define_table(tablename,
                     deployment_id(),
                     instance_id(),
                     Field("setting",
                           label = T("Setting"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("current_value",
                           label = T("Current Value"),
                           writable = False,
                           ),
                     Field("new_value",
                           label = T("New Value"),
                           ),
                     *s3_meta_fields()
                     )

        crud_strings[tablename] = Storage(
            label_create = T("Add Setting"),
            title_display = T("Setting Details"),
            title_list =  T("Settings"),
            title_update = T("Edit Setting"),
            label_list_button =  T("List Settings"),
            label_delete_button = T("Delete Setting"),
            msg_record_created = T("Setting added"),
            msg_record_modified = T("Setting updated"),
            msg_record_deleted = T("Setting deleted"),
            msg_list_empty = T("No Settings currently registered"))

        set_method("setup", "deployment",
                   component_name = "setting",
                   method = "apply",
                   action = self.setup_setting_apply,
                   )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return {"setup_deployment_id": deployment_id,
                "setup_server_id": server_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_deployment_create_onaccept(form):
        """
            New deployments:
                Assign a random DB password
                Configure localhost to have all tiers (for 1st deployment)
        """

        db = current.db
        s3db = current.s3db
        table = s3db.setup_deployment

        deployment_id = form.vars.id

        # Assign a random DB password
        chars = string.ascii_letters + string.digits + string.punctuation
        # Ensure that " isn't included otherwise we get a syntax error in 000_config.py
        chars = chars.replace('"', "")
        # Ensure that ' isn't included otherwise we get a syntax error in pgpass.sql
        chars = chars.replace("'", "")
        # Ensure that @ isn't included as Web2Py doesn't like this
        chars = chars.replace("@", "")
        # Ensure that \ isn't included as control characters can cause the settings.database.password to not match pgpass (e.g. \a -> ^G)
        chars = chars.replace("\\", "")
        password = "".join(random.choice(chars) for _ in range(12))
        db(table.id == deployment_id).update(db_password = password)

        current.session.information = current.T("Press 'Deploy' when you are ready")

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_get_countries(path):
        """
            Return a List of Countries for which we have Locale settings defined

            @ToDo: Read the list of templates from the selected repo URL!
                   - locations.txt
        """

        p = os.path
        basename = p.basename
        isdir = p.isdir
        join = p.join

        path = join(path, "locations")
        available_countries = [basename(c) for c in os.listdir(path) if isdir(join(path, c))]
        all_countries = current.gis.get_countries(key_type="code")
        countries = OrderedDict([(c, all_countries[c]) for c in all_countries if c in available_countries])

        return countries

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_get_templates(path):
        """
            Return a List of Templates for the user to select between

            @ToDo: Read the list of templates from the selected repo URL!
                   - templates.txt
        """

        p = os.path
        basename = p.basename
        join = p.join
        isdir = p.isdir
        listdir = os.listdir

        # All subdirectories in the path that contain a config.py are
        # templates - except skeleton/skeletontheme
        dirs = next(os.walk(path))[1]
        templates = [d for d in dirs
                         if d[:8] != "skeleton" and
                         p.isfile(join(path, d, "config.py"))
                         ]

        subtemplates = []
        sappend = subtemplates.append
        for template in templates:
            tpath = join(path, template)
            for d in listdir(tpath):
                if isdir(join(tpath, d)):
                    for f in listdir(join(tpath, d)):
                        if f == "config.py":
                            sappend("%s.%s" % (template, d))
                            continue

        templates += subtemplates
        templates.sort()
        return templates

    # -------------------------------------------------------------------------
    def setup_server_wizard(self, r, **attr):
        """
            Custom S3Method to select an Instance to Configure
        """

        db = current.db
        deployment_id = r.id
        itable = db.setup_instance

        instances = db(itable.deployment_id == deployment_id).select(itable.id,
                                                                     itable.type,
                                                                     )

        if len(instances) == 1:
            # Redirect to the Instance Wizard
            redirect(URL(c="setup", f="deployment",
                         args = [deployment_id, "instance", instances.first().id, "wizard"],
                         ))

        # Provide a Dropdown of Instances for the user to select
        dropdown = SELECT(OPTION(_value=""),
                          _id = "instances",
                          )
        for instance in instances:
            dropdown.append(OPTION(INSTANCE_TYPES[instance.type],
                                   _value="%s" % instance.id))

        script = '''
var dropdown = $('#instances');
dropdown.change(function() {
 var url = S3.Ap.concat('/setup/deployment/%s/instance/' + this.value + '/wizard');
 $(location).prop('href', url);
})''' % deployment_id
        response = current.response
        response.s3.jquery_ready.append(script)
        response.view = "simple.html"
        output = {"item": DIV(P(current.T("Select the instance you wish to configure")),
                              dropdown),
                  }
        return output

    # -------------------------------------------------------------------------
    def setup_instance_wizard(self, r, **attr):
        """
            Custom S3Method to Configure an Instance

            @ToDo: Option to Propagate settings from Prod to Demo &/or Test
                   - on by default
        """

        from gluon import IS_IN_SET, SQLFORM
        from gluon.sqlhtml import RadioWidget
        from s3 import s3_mark_required
        from s3dal import Field

        T = current.T
        response = current.response
        settings = current.deployment_settings

        questions = settings.get_setup_wizard_questions()

        fields = []
        fappend = fields.append
        for q in questions:
            setting = q["setting"]
            fname = setting.replace(".", "_")
            fappend(Field(fname,
                          label = T(q["question"]),
                          requires = IS_IN_SET(q["options"]),
                          widget = RadioWidget.widget,
                          #widget = lambda f, v: RadioWidget.widget(f, v, style="divs"),
                          _id = "setting",
                          ))

        labels, required = s3_mark_required(fields)
        response.s3.has_required = required
        response.form_label_separator = ""

        form = SQLFORM.factory(#formstyle = settings.get_ui_formstyle(),
                               submit_button = T("Submit"),
                               labels = labels,
                               separator = "",
                               table_name = "options", # Dummy table name
                               _id = "options",
                               *fields
                               )

        if form.accepts(r.post_vars, current.session):
            # Processs Form
            result = self.setup_settings_apply(r.id, form.vars)
            if result:
                response.confirmation = T("Settings Applied")

        current.response.view = "simple.html"
        output = {"item": form,
                  "title": T("Configuration Wizard"),
                  }
        return output

    # -------------------------------------------------------------------------
    def setup_instance_deploy(self, r, **attr):
        """
            Custom S3Method to Deploy an Instance
        """

        db = current.db
        s3db = current.s3db

        deployment_id = r.id

        # Get Instance details
        # - we read all instances for Certbot configuration
        instance_id = r.component_id
        itable = s3db.setup_instance
        query = (itable.deployment_id == deployment_id) & \
                (itable.deleted == False)
        instances = db(query).select(itable.id,
                                     itable.type,
                                     itable.url,
                                     itable.sender,
                                     itable.start,
                                     )
        all_sites = []
        all_append = all_sites.append
        for instance in instances:
            url = instance.url
            if "://" in url:
                protocol, url = url.split("://", 1)
            all_append(url)
            if str(instance.id) == instance_id:
                sitename = url
                sender = instance.sender
                start = instance.start
                instance_type = instance.type
            if instance.type == 1:
                sitename_prod = url

        # Default to SSL
        # (plain http requests will still work as automatically redirected to https)
        protocol = "https"

        # Get Deployment details
        dtable = s3db.setup_deployment
        deployment = db(dtable.id == deployment_id).select(dtable.webserver_type,
                                                           dtable.db_type,
                                                           dtable.db_password,
                                                           dtable.template,
                                                           dtable.cloud_id,
                                                           dtable.dns_id,
                                                           limitby = (0, 1)
                                                           ).first()

        # Get Server(s) details
        stable = s3db.setup_server
        query = (stable.deployment_id == deployment_id)
        cloud_id = deployment.cloud_id
        if cloud_id:
            # Get AWS details
            # @ToDo: Will need extending when we support multiple Cloud Providers
            atable = s3db.setup_aws_cloud
            aws = db(atable.id == cloud_id).select(atable.access_key,
                                                   atable.secret_key,
                                                   limitby = (0, 1)
                                                   ).first()

            # Get Server(s) details
            astable = s3db.setup_aws_server
            left = astable.on(astable.server_id == stable.id)
            servers = db(query).select(stable.id,
                                       stable.name,
                                       stable.role,
                                       stable.host_ip,
                                       stable.remote_user,
                                       stable.private_key,
                                       astable.region,
                                       astable.instance_type,
                                       astable.image,
                                       astable.security_group,
                                       astable.instance_id,
                                       left = left,
                                       )
        else:
            # Get Server(s) details
            servers = db(query).select(#stable.name,
                                       stable.role,
                                       stable.host_ip,
                                       stable.remote_user,
                                       stable.private_key,
                                       )

        # Build Playbook data structure
        roles_path = os.path.join(r.folder, "private", "eden_deploy", "roles")

        appname = "eden" # @ToDo: Allow this to be configurable
        hostname = sitename.split(".", 1)[0]
        db_password = deployment.db_password
        web_server = WEB_SERVERS[deployment.webserver_type]
        db_type = DB_SERVERS[deployment.db_type]
        instance_type = INSTANCE_TYPES[instance_type]
        template = deployment.template

        if len(servers) == 1:
            # All-in-one deployment
            server = servers.first()
            playbook = []
            if cloud_id:
                tasks = []
                connection = "smart"
                # @ToDo: Will need extending when we support multiple Cloud Providers
                access_key = aws.access_key
                secret_key = aws.secret_key
                aws_server = server["setup_aws_server"]
                region = aws_server.region
                server = server["setup_server"]
                remote_user = server.remote_user
                server_name = server.name
                private_key = "/tmp/%s" % server_name
                public_key = "%s.pub" % private_key
                provided_key = server.private_key
                if provided_key:
                    delete_ssh_key = False
                    provided_key = os.path.join(r.folder, "uploads", provided_key)
                    # Generate the Public Key
                    command = "openssl rsa -in %(provided_key)s -pubout > %(public_key)s" % \
                        {provided_key: provided_key,
                         public_key: public_key,
                         }
                    tasks.append({"command": command,
                                  })
                else:
                    delete_ssh_key = True
                    # Generate an OpenSSH keypair with the default values (4096 bits, rsa)
                    tasks.append({"openssh_keypair": {"path": private_key,
                                                      },
                                  })
                # Upload Public Key to AWS
                tasks.append({"ec2_key": {"aws_access_key": access_key,
                                          "aws_secret_key": secret_key,
                                          "region": region,
                                          "name": server_name,
                                          "key_material": "{{ lookup('file', '%s') }}" % public_key,
                                          },
                              })
                if aws_server.instance_id:
                    # Terminate old AWS instance
                    # @ToDo: Allow deployment on existing instances?
                    tasks.append({"ec2": {"aws_access_key": access_key,
                                          "aws_secret_key": secret_key,
                                          "region": region,
                                          "instance_ids": aws_server.instance_id,
                                          "state": "absent",
                                          },
                                  })
                # Launch AWS instance
                request = current.request
                command = "python web2py.py -S %(appname)s -M -R %(appname)s/private/eden_deploy/tools/update_server.py -A %(server_id)s {{ item.id }} {{ item.public_ip }} %(server_name)s" % \
                            {"appname": request.application,
                             "server_id": server.id,
                             "server_name": server_name,
                             }
                tasks += [# Launch AWS Instance
                          {"ec2": {"aws_access_key": access_key,
                                   "aws_secret_key": secret_key,
                                   "key_name": server_name,
                                   "region": region,
                                   "instance_type": aws_server.instance_type,
                                   "image": aws_server.image,
                                   "group": aws_server.security_group,
                                   "wait": "yes",
                                   "count": 1,
                                   "instance_tags": {"Name": server_name,
                                                     },
                                   },
                           "register": "ec2",
                           },
                          # Add new instance to host group (to associate private_key)
                          {"add_host": {"hostname": "{{ item.public_ip }}",
                                        "groupname": "launched",
                                        "ansible_ssh_private_key_file": "/tmp/%s" % server_name,
                                        },
                           "loop": "{{ ec2.instances }}",
                           },
                          # Update Server record
                          {"command": {"cmd": command,
                                       "chdir": request.env.web2py_path,
                                       },
                           "become": "yes",
                           "become_method": "sudo",
                           "become_user": "web2py",
                           "loop": "{{ ec2.instances }}",
                           },
                          ]
                dns_id = deployment.dns_id
                if dns_id:
                    # @ToDo: Will need extending when we support multiple DNS Providers
                    gtable = s3db.setup_gandi_dns
                    gandi = db(gtable.id == dns_id).select(gtable.api_key,
                                                           gtable.domain,
                                                           gtable.zone,
                                                           limitby = (0, 1)
                                                           ).first()
                    gandi_api_key = gandi.api_key
                    url = "https://dns.api.gandi.net/api/v5/zones/%s/records" % gandi.zone
                    dns_record = sitename.split(".%s" % gandi.domain, 1)[0]
                    tasks += [# Delete any existing record
                              {"uri": {"url": "%s/%s" % (url, dns_record),
                                       "method": "DELETE",
                                       "headers": {"X-Api-Key": gandi_api_key,
                                                   },
                                       },
                               # Don't worry if it didn't exist
                               "ignore_errors": "yes",
                               },
                              # Create new record
                              {"uri": {"url": url,
                                       "method": "POST",
                                       "headers": {"X-Api-Key": gandi_api_key,
                                                   },
                                       "body_format": "json", # Content-Type: application/json
                                       "body": '{"rrset_name": "%s", "rrset_type": "A", "rrset_ttl": 10800, "rrset_values": ["{{ item.public_ip }}"]}' % dns_record
                                       },
                               "loop": "{{ ec2.instances }}",
                               },
                              ]
                else:
                    current.session.warning = current.T("Deployment will not have SSL: No DNS Provider configured to link to new server IP Address")
                    # @ToDo: Support Elastic IPs
                    protocol = "http"
                playbook.append({"hosts": "localhost",
                                 "connection": "local",
                                 "gather_facts": "no",
                                 "tasks": tasks,
                                 })
                host_ip = "launched"
                # Wait for Server to become available
                playbook.append({"hosts": "launched",
                                 "connection": "smart",
                                 "remote_user": remote_user,
                                 "gather_facts": "no",
                                 "tasks": [{"wait_for_connection": {"timeout": 300, # seconds
                                                                    },
                                            },
                                           ],
                                 })
            else:
                # No Cloud
                delete_ssh_key = False
                remote_user = server.remote_user
                host_ip = server.host_ip
                # Check if DNS is already configured properly
                import socket
                try:
                    ip_addr = socket.gethostbyname(sitename)
                except socket.gaierror:
                    current.session.warning = current.T("Deployment will not have SSL: URL doesn't resolve in DNS")
                    protocol = "http"
                # @ToDo Check that ip_addr is correct
                #       - if host_ip == "127.0.0.1" then we can check the contents 
                if host_ip != "127.0.0.1":
                    # We may wish to administer via a private IP, so shouldn't do this:
                    #if protocol == "https" and ip_addr != host_ip:
                    #    current.session.warning = current.T("Deployment will not have SSL: URL doesn't match server IP Address")
                    #    protocol = "http"
                    # We will need the SSH key
                    connection = "smart"
                    private_key = server.private_key
                    if not private_key:
                        # Abort
                        current.session.error = current.T("Deployment failed: SSH Key needed when deploying away from localhost")
                        redirect(URL(c="setup", f="deployment",
                                     args = [deployment_id, "instance"],
                                     ))
                    # Add instance to host group (to associate private_key)
                    host_ip = "launched"
                    private_key = os.path.join(r.folder, "uploads", private_key)
                    playbook.append({"hosts": "localhost",
                                     "connection": "local",
                                     "gather_facts": "no",
                                     "tasks": [{"add_host": {"hostname": host_ip,
                                                             "groupname": "launched",
                                                             "ansible_ssh_private_key_file": private_key,
                                                             },
                                                },
                                               ],
                                     })
                else:
                    connection = "local"
                    
            # Deploy to Server
            playbook.append({"hosts": host_ip,
                             "connection": connection,
                             "remote_user": remote_user,
                             "become_method": "sudo",
                             #"become_user": "root",
                             "vars": {"appname": appname,
                                      "all_sites": ",".join(all_sites),
                                      "db_ip": "127.0.0.1",
                                      "db_type": db_type,
                                      "hostname": hostname,
                                      "password": db_password,
                                      "protocol": protocol,
                                      "sender": sender,
                                      "sitename": sitename,
                                      "sitename_prod": sitename_prod,
                                      "start": start,
                                      "template": template,
                                      "type": instance_type,
                                      "web_server": web_server,
                                      },
                             "roles": [{"role": "%s/common" % roles_path },
                                       {"role": "%s/exim" % roles_path },
                                       {"role": "%s/%s" % (roles_path, db_type) },
                                       {"role": "%s/uwsgi" % roles_path },
                                       {"role": "%s/%s" % (roles_path, web_server) },
                                       {"role": "%s/final" % roles_path },
                                       ]
                             })
            if delete_ssh_key:
                # Delete SSH private key from the filesystem
                playbook.append({"hosts": "localhost",
                                 "connection": "local",
                                 "gather_facts": "no",
                                 "tasks": [{"file": {"path": private_key,
                                                     "state": "absent",
                                                     },
                                            },
                                           ],
                                 })
        else:
            # Separate Database
            # @ToDo: Needs completing
            # Abort
            current.session.error = current.T("Deployment failed: Currently only All-in-one deployments supported with this tool")
            redirect(URL(c="setup", f="deployment",
                         args = [deployment_id, "instance"],
                         ))
            for server in servers:
                if server.role == 2:
                    db_ip = server.host_ip
                    private_key = server.private.key
                    remote_user = server.remote_user
                else:
                    webserver_ip = server.host_ip
            playbook = [{"hosts": db_ip,
                         "remote_user": remote_user,
                         "become_method": "sudo",
                         #"become_user": "root",
                         "vars": {"db_type": db_type,
                                  "password": db_password,
                                  "type": instance_type
                                  },
                         "roles": [{ "role": "%s/%s" % (roles_path, db_type) },
                                   ]
                         },
                        {"hosts": webserver_ip,
                         #"remote_user": remote_user,
                         "become_method": "sudo",
                         #"become_user": "root",
                         "vars": {"appname": appname,
                                  "all_sites": ",".join(all_sites),
                                  "db_ip": db_ip,
                                  "db_type": db_type,
                                  "hostname": hostname,
                                  "password": db_password,
                                  "protocol": protocol,
                                  "sitename": sitename,
                                  "sender": sender,
                                  "start": start,
                                  "template": template,
                                  "type": instance_type,
                                  "web_server": web_server,
                                  },
                         "roles": [{"role": "%s/common" % roles_path },
                                   {"role": "%s/exim" % roles_path },
                                   {"role": "%s/uwsgi" % roles_path },
                                   {"role": "%s/%s" % (roles_path, web_server) },
                                   {"role": "%s/final" % roles_path },
                                   ],
                         },
                        ]

        # Write Playbook
        name = "deployment_%d" % int(time.time())
        if instance_type == "prod":
            tags = []
        else:
            tags = [instance_type]
        task_vars = setup_write_playbook("%s.yml" % name,
                                         playbook,
                                         tags,
                                         )

        # Run Playbook
        task_vars["instance_id"] = instance_id
        task_id = current.s3task.schedule_task(name,
                                               vars = task_vars,
                                               function_name = "setup_run_playbook",
                                               repeats = None,
                                               timeout = 6000,
                                               #sync_output = 300
                                               )

        # Link scheduled task to current record
        # = allows us to monitor deployment progress
        db(itable.id == instance_id).update(task_id = task_id)

        current.session.confirmation = current.T("Deployment initiated")
        redirect(URL(c="setup", f="deployment",
                     args = [deployment_id, "instance"],
                     ))

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_instance_settings(r, **attr):
        """
            Custom interactive S3Method to Read the Settings for an instance
            from models/000_config.py
        """

        deployment_id = r.id

        setup_instance_settings_read(r.component_id, deployment_id)

        current.session.confirmation = current.T("Settings Read")

        redirect(URL(c="setup", f="deployment",
                     args = [deployment_id, "setting"]),
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_instance_start(r, **attr):
        """
            Custom interactive S3Method to Start an Instance
        """

        setup_instance_method(r.component_id)

        current.session.confirmation = current.T("Instance Started")

        redirect(URL(c="setup", f="deployment",
                     args = [r.id, "instance"]),
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_instance_stop(r, **attr):
        """
            Custom interactive S3Method to Stop an Instance
        """

        setup_instance_method(r.component_id, "stop")

        current.session.confirmation = current.T("Instance Stopped")

        redirect(URL(c="setup", f="deployment",
                     args = [r.id, "instance"]),
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_instance_clean(r, **attr):
        """
            Custom interactive S3Method to Clean an Instance
        """

        setup_instance_method(r.component_id, "clean")

        current.session.confirmation = current.T("Instance Clean Started")

        redirect(URL(c="setup", f="deployment",
                     args = [r.id, "instance"]),
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_instance_ondelete(row):
        """
            Cleanup Tasks when an Instance is Deleted
            - DNS
        """

        db = current.db
        s3db = current.s3db

        dtable = s3db.setup_deployment
        deployment = db(dtable.id == row.deployment_id).select(dtable.dns_id,
                                                               limitby = (0, 1)
                                                               ).first()

        dns_id = deployment.dns_id

        if dns_id is None:
            # Nothing to cleanup
            return

        # Read URL (only deleted_fks are in the row object)
        itable = s3db.setup_instance
        instance = db(itable.id == row.id).select(itable.url,
                                                  limitby = (0, 1)
                                                  ).first()

        # @ToDo: Will need extending when we support multiple DNS Providers
        # Get Gandi details
        gtable = s3db.setup_gandi_dns
        gandi = db(gtable.id == dns_id).select(gtable.api_key,
                                               gtable.domain,
                                               gtable.zone,
                                               limitby = (0, 1)
                                               ).first()
        gandi_api_key = gandi.api_key
        domain = gandi.domain
        url = "https://dns.api.gandi.net/api/v5/zones/%s/records" % gandi.zone

        # Delete DNS record
        parts = instance.url.split("://")
        if len(parts) == 1:
            sitename = parts[0]
        else:
            sitename = parts[1]
        dns_record = sitename.split(".%s" % domain, 1)[0]

        playbook = [{"hosts": "localhost",
                     "connection": "local",
                     "gather_facts": "no",
                     "tasks": [{"uri": {"url": "%s/%s" % (url, dns_record),
                                        "method": "DELETE",
                                        "headers": {"X-Api-Key": gandi_api_key,
                                                    },
                                        },
                                # Don't worry if it didn't exist
                                "ignore_errors": "yes",
                                },
                               ],
                     },
                    ]

        # Write Playbook
        name = "instance_ondelete_%d" % int(time.time())
        task_vars = setup_write_playbook("%s.yml" % name,
                                         playbook,
                                         )

        # Run Playbook
        current.s3task.schedule_task(name,
                                     vars = task_vars,
                                     function_name = "setup_run_playbook",
                                     repeats = None,
                                     timeout = 6000,
                                     #sync_output = 300
                                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_setting_apply(r, **attr):
        """
            Custom interactive S3Method to Apply a Setting to an instance
            via models/000_config.py
        """

        db = current.db
        s3db = current.s3db

        deployment_id = r.id
        setting_id = r.component_id

        stable = s3db.setup_setting
        setting = db(stable.id == setting_id).select(stable.id,
                                                     stable.instance_id,
                                                     stable.setting,
                                                     stable.new_value,
                                                     limitby = (0, 1)
                                                     ).first()
        new_value = setting.new_value
        instance_id = setting.instance_id

        itable = s3db.setup_instance
        instance = db(itable.id == instance_id).select(itable.type,
                                                       limitby = (0, 1)
                                                       ).first()
        instance_type = INSTANCE_TYPES[instance.type]

        # Lookup Server Details
        # @ToDo: Support multiple Eden servers used as Load-balancers
        svtable = s3db.setup_server
        query = (svtable.deployment_id == deployment_id) & \
                (svtable.role.belongs((1, 4)))
        server = db(query).select(svtable.host_ip,
                                  svtable.remote_user,
                                  svtable.private_key,
                                  limitby = (0, 1)
                                  ).first()
        host_ip = server.host_ip
        remote_user = server.remote_user
        private_key = server.private_key

        # Build Playbook data structure:
        the_setting = setting.setting
        if new_value is True or new_value is False:
            new_line = "settings.%s = %s" % (the_setting, new_value)
        else:
            # @ToDo: Handle lists/dicts (load into JSONS3?)
            new_line = 'settings.%s = "%s"' % (the_setting, new_value)

        appname = r.application

        playbook = [{"hosts": host_ip,
                     # @ToDo: "smart" & SSH Keys for non-localhost
                     "connection": "local",
                     "remote_user": remote_user,
                     "become_method": "sudo",
                     #"become_user": "root",
                     "tasks": [{"name": "Edit 000_config.py",
                                "lineinfile": {"dest": "/home/%s/applications/%s/models/000_config.py" % (instance_type, appname),
                                               "regexp": "^settings.%s =" % the_setting,
                                               "line": new_line,
                                               "state": "present",
                                               },
                                },
                               # @ToDo: Handle case where need to restart multiple webservers
                               {"name": "Compile & Restart WebServer",
                                #"command": "sudo -H -u web2py python web2py.py -S %(appname)s -M -R applications/%(appname)s/static/scripts/tools/compile.py" % {"appname": appname},
                                #"args": {"chdir": "/home/%s" % instance_type,
                                #         },
                                # We don't want to restart the UWSGI process running the Task until after the Task has completed
                                "command": 'echo "/usr/local/bin/compile %s" | at now + 1 minutes' % instance_type,
                                "become": "yes",
                                },
                               ]
                     },
                    ]

        # Write Playbook
        name = "apply_%d" % int(time.time())
        task_vars = setup_write_playbook("%s.yml" % name,
                                         playbook,
                                         )

        # Run the Playbook
        task_vars["instance_id"] = instance_id
        current.s3task.schedule_task(name,
                                     vars = task_vars,
                                     function_name = "setup_run_playbook",
                                     repeats = None,
                                     timeout = 6000,
                                     #sync_output = 300
                                     )

        # Update the DB to show that the setting has been applied
        # @ToDo: Do this as a callback from the async task
        setting.update_record(current_value = new_value,
                              new_value = None,
                              )

        current.session.confirmation = current.T("Setting Applied")

        redirect(URL(c="setup", f="deployment",
                     args = [deployment_id, "setting"]),
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_settings_apply(instance_id, settings):
        """
            Method to Apply Settings to an instance
            via models/000_config.py
        """

        db = current.db
        s3db = current.s3db
        appname = current.request.application

        itable = s3db.setup_instance
        instance = db(itable.id == instance_id).select(itable.id,
                                                       itable.deployment_id,
                                                       itable.type,
                                                       limitby = (0, 1)
                                                       ).first()
        deployment_id = instance.deployment_id
        instance_type = INSTANCE_TYPES[instance.type]

        # Lookup Server Details
        # @ToDo: Support multiple Eden servers used as Load-balancers
        svtable = s3db.setup_server
        query = (svtable.deployment_id == deployment_id) & \
                (svtable.role.belongs((1, 4)))
        server = db(query).select(svtable.host_ip,
                                  svtable.remote_user,
                                  svtable.private_key,
                                  limitby = (0, 1)
                                  ).first()
        host_ip = server.host_ip
        remote_user = server.remote_user
        private_key = server.private_key

        # Build Playbook data structure:
        tasks = []
        tappend = tasks.append
        for setting in settings:
            the_setting = setting.replace("_", ".", 1)
            new_value = settings[setting]
            if new_value == "True" or new_value == "False":
                new_line = "settings.%s = %s" % (the_setting, new_value)
            else:
                # @ToDo: Handle lists/dicts (load into JSONS3?)
                new_line = 'settings.%s = "%s"' % (the_setting, new_value)
            tappend({"name": "Edit 000_config.py",
                     "lineinfile": {"dest": "/home/%s/applications/%s/models/000_config.py" % (instance_type, appname),
                                    "regexp": "^settings.%s =" % the_setting,
                                    "line": new_line,
                                    "state": "present",
                                    },
                     })

        # @ToDo: Handle case where need to restart multiple webservers
        tappend({"name": "Compile & Restart WebServer",
                 #"command": "sudo -H -u web2py python web2py.py -S %(appname)s -M -R applications/%(appname)s/static/scripts/tools/compile.py" % {"appname": appname},
                 #"args": {"chdir": "/home/%s" % instance_type,
                 #         },
                 # We don't want to restart the UWSGI process running the Task until after the Task has completed
                 "command": 'echo "/usr/local/bin/compile %s" | at now + 1 minutes' % instance_type,
                 "become": "yes",
                 })

        playbook = [{"hosts": host_ip,
                     # @ToDo: "smart" & SSH Keys for non-localhost
                     "connection": "local",
                     "remote_user": remote_user,
                     "become_method": "sudo",
                     #"become_user": "root",
                     "tasks": tasks,
                     },
                    ]

        # Write Playbook
        name = "apply_%d" % int(time.time())
        task_vars = setup_write_playbook("%s.yml" % name,
                                         playbook,
                                         )

        # Run the Playbook
        task_vars["instance_id"] = instance_id
        current.s3task.schedule_task(name,
                                     vars = task_vars,
                                     function_name = "setup_run_playbook",
                                     repeats = None,
                                     timeout = 6000,
                                     #sync_output = 300
                                     )

        # Update the DB to show that the settings have been applied
        # @ToDo: Do this as a callback from the async task
        instance.update_record(configured = True)
        stable = s3db.setup_setting
        q = (stable.instance_id == instance_id)
        for setting in settings:
            the_setting = setting.replace("_", ".", 1)
            new_value = settings[setting]
            db(q & (stable.setting == the_setting)).update(current_value = new_value,
                                                           new_value = None)

        return True

# =============================================================================
class S3SetupMonitorModel(S3Model):

    names = ("setup_monitor_server",
             "setup_monitor_check",
             "setup_monitor_task",
             "setup_monitor_run",
             #"setup_monitor_alert",
             )

    def model(self):

        T = current.T
        db = current.db

        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        set_method = self.set_method
        server_id = self.setup_server_id

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        STATUS_OPTS = {0 : T("Unknown"),
                       1 : T("OK"),
                       2 : T("Warning"),
                       3 : T("Critical"),
                       }

        status_id = S3ReusableField("status", "integer", notnull=True,
                                    default = 0,
                                    label = T("Status"),
                                    represent = lambda opt: \
                                                    STATUS_OPTS.get(opt,
                                                                    UNKNOWN_OPT),
                                    requires = IS_IN_SET(STATUS_OPTS,
                                                         zero=None),
                                    writable = False,
                                    )

        # =====================================================================
        # Servers
        # - extensions for Monitoring:
        #       Are checks Enabled?
        #       Overall Server Status
        #
        tablename = "setup_monitor_server"
        define_table(tablename,
                     #Field("name", unique=True, length=255,
                     #      label = T("Name"),
                     #      ),
                     server_id(),
                     Field("enabled", "boolean",
                           default = True,
                           label = T("Enabled?"),
                           represent = s3_yes_no_represent,
                           ),
                     status_id(),
                     s3_comments(),
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = self.setup_monitor_server_onaccept,
                  )

        # =====================================================================
        # Checks
        # - monitoring scripts available
        #
        tablename = "setup_monitor_check"
        define_table(tablename,
                     Field("name", unique=True, length=255,
                           label = T("Name"),
                           ),
                     # Name of a function in modules.<settings.get_setup_monitor_template()>.monitor[.py]
                     # List populated in controllers/setup/monitor_check()
                     Field("function_name",
                           label = T("Script"),
                           ),
                     # Default Options for this Check
                     Field("options", "json",
                           label = T("Options"),
                           requires = IS_EMPTY_OR(
                                        IS_JSONS3()
                                        ),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
                label_create = T("Create Check"),
                title_display = T("Check Details"),
                title_list =  T("Checks"),
                title_update = T("Edit Check"),
                title_upload = T("Import Checks"),
                label_list_button =  T("List Checks"),
                label_delete_button = T("Delete Check"),
                msg_record_created = T("Check added"),
                msg_record_modified = T("Check updated"),
                msg_record_deleted = T("Check deleted"),
                msg_list_empty = T("No Checks currently registered"))

        represent = S3Represent(lookup = tablename)
        check_id = S3ReusableField("check_id", "reference %s" % tablename,
                                   label = T("Check"),
                                   ondelete = "CASCADE",
                                   represent = represent,
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "setup_monitor_check.id",
                                                          represent)),
                                   )

        add_components(tablename,
                       setup_monitor_task = "check_id",
                       )

        # =====================================================================
        # Tasks
        #
        tablename = "setup_monitor_task"
        define_table(tablename,
                     self.setup_deployment_id(readable = False,
                                              writable = False,
                                              ),
                     server_id(),
                     check_id(),
                     # Options for this Check on this Server
                     Field("options", "json",
                           label = T("Options"),
                           requires = IS_EMPTY_OR(
                                        IS_JSONS3()
                                        ),
                           ),
                     Field("enabled", "boolean",
                           default = True,
                           label = T("Enabled?"),
                           represent = s3_yes_no_represent,
                           ),
                     status_id(),
                     Field("result", "json",
                           label = T("Result"),
                           requires = IS_EMPTY_OR(
                                        IS_JSONS3()
                                        ),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Task"),
            title_display = T("Task Details"),
            title_list =  T("Tasks"),
            title_update = T("Edit Task"),
            title_upload = T("Import Tasks"),
            label_list_button =  T("List Tasks"),
            label_delete_button = T("Delete Task"),
            msg_record_created = T("Task added"),
            msg_record_modified = T("Task updated"),
            msg_record_deleted = T("Task deleted"),
            msg_list_empty = T("No Tasks currently registered"))

        configure(tablename,
                  # Open the Options after creation
                  create_next = URL(c="setup", f="monitor_task",
                                    args = ["[id]", "option"],
                                    ),
                  onaccept = self.setup_monitor_task_onaccept,
                  )

        # @ToDo: Fix represent
        represent = S3Represent(lookup = tablename,
                                fields = ["server_id", "check_id"],
                                )
        task_id = S3ReusableField("task_id", "reference %s" % tablename,
                                  label = T("Task"),
                                  ondelete = "CASCADE",
                                  represent = represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "setup_monitor_task.id",
                                                          represent)),
                                  )

        add_components(tablename,
                       setup_monitor_alert = "task_id",
                       setup_monitor_run = "task_id",
                       )

        set_method("monitor", "task",
                   method = "enable",
                   action = self.setup_monitor_task_enable_interactive)

        set_method("monitor", "task",
                   method = "disable",
                   action = self.setup_monitor_task_disable_interactive)

        set_method("monitor", "task",
                   method = "check",
                   action = self.setup_monitor_task_run)

        # =====================================================================
        # Runs
        #
        tablename = "setup_monitor_run"
        define_table(tablename,
                     server_id(writable = False),
                     task_id(writable = False),
                     status_id(),
                     Field("result", "json",
                           label = T("Result"),
                           requires = IS_EMPTY_OR(
                                        IS_JSONS3()
                                        ),
                           ),
                     s3_comments(),
                     *s3_meta_fields()#,
                     #on_define = lambda table: \
                     #   [table.created_on.set_attributes(represent = \
                     #       lambda dt: S3DateTime.datetime_represent(dt, utc=True)),
                     #   ]
                     )

        crud_strings[tablename] = Storage(
            #label_create = T("Create Log Entry"),
            title_display = T("Log Entry Details"),
            title_list =  T("Log Entries"),
            title_update = T("Edit Log Entry"),
            #title_upload = T("Import Log Entries"),
            label_list_button =  T("List Log Entries"),
            label_delete_button = T("Delete Log Entry"),
            #msg_record_created = T("Log Entry added"),
            msg_record_modified = T("Log Entry updated"),
            msg_record_deleted = T("Log Entry deleted"),
            msg_list_empty = T("No Log Entries currently registered"))

        configure(tablename,
                  # Logs inserted automatically
                  insertable = False,
                  list_fields = ["created_on",
                                 "server_id",
                                 "task_id",
                                 "status",
                                 "comments",
                                 ],
                  orderby = "setup_monitor_run.created_on desc",
                  )

        # =============================================================================
        # Alerts
        #  - what threshold to raise an alert on
        #
        # @ToDo: UI to wrap normal Subscription / Notifications

        #tablename = "setup_monitor_alert"
        #define_table(tablename,
        #             task_id(),
        #             self.pr_person_id(),
        #             # @ToDo: Threshold
        #             s3_comments(),
        #             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_monitor_server_onaccept(form):
        """
            Process the Enabled Flag
        """

        form_vars = form.vars
        if form.record:
            # Update form
            # process of changed
            if form.record.enabled and not form_vars.enabled:
                setup_monitor_server_disable(form_vars.id)
            elif form_vars.enabled and not form.record.enabled:
                setup_monitor_server_enable(form_vars.id)
        else:
            # Create form
            # Process only if enabled
            if form_vars.enabled:
                setup_monitor_server_enable(form_vars.id)

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_monitor_task_enable(task_id):
        """
            Enable a Task
            - Schedule Check

            CLI API for shell scripts & to be called by S3Method
        """

        db = current.db
        table = current.s3db.setup_monitor_task

        record = db(table.id == task_id).select(table.id,
                                                table.enabled,
                                                limitby = (0, 1),
                                                ).first()

        if not record.enabled:
            # Flag it as enabled
            record.update_record(enabled = True)

        # Is the task already Scheduled?
        ttable = db.scheduler_task
        args = "[%s]" % task_id
        query = ((ttable.function_name == "setup_monitor_run_task") & \
                 (ttable.args == args) & \
                 (ttable.status.belongs(["RUNNING",
                                         "QUEUED",
                                         "ALLOCATED"])))
        exists = db(query).select(ttable.id,
                                  limitby = (0, 1)
                                  ).first()
        if exists:
            return "Task already enabled"
        else:
            current.s3task.schedule_task("setup_monitor_run_task",
                                         args = [task_id],
                                         period = 300,  # seconds
                                         timeout = 300, # seconds
                                         repeats = 0    # unlimited
                                         )
            return "Task enabled"

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_monitor_task_enable_interactive(r, **attr):
        """
            Enable a Task
            - Schedule Check

            S3Method for interactive requests
        """

        result = S3SetupMonitorModel.setup_monitor_task_enable(r.id)
        current.session.confirmation = result
        redirect(URL(f="task"))

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_monitor_task_disable(task_id):
        """
            Disable a Check
            - Remove Schedule for Check

            CLI API for shell scripts & to be called by S3Method
        """

        db = current.db
        table = current.s3db.setup_monitor_task

        record = db(table.id == task_id).select(table.id, # needed for update_record
                                                table.enabled,
                                                limitby = (0, 1),
                                                ).first()

        if record.enabled:
            # Flag it as disabled
            record.update_record(enabled = False)

        # Is the task already Scheduled?
        ttable = db.scheduler_task
        args = "[%s]" % task_id
        query = ((ttable.function_name == "setup_monitor_run_task") & \
                 (ttable.args == args) & \
                 (ttable.status.belongs(["RUNNING",
                                         "QUEUED",
                                         "ALLOCATED"])))
        exists = db(query).select(ttable.id,
                                  limitby = (0, 1)
                                  ).first()
        if exists:
            # Disable all
            db(query).update(status = "STOPPED")
            return "Task disabled"
        else:
            return "Task already disabled"

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_monitor_task_disable_interactive(r, **attr):
        """
            Disable a Task
            - Remove Schedule for Check

            S3Method for interactive requests
        """

        result = S3SetupMonitorModel.setup_monitor_task_disable(r.id)
        current.session.confirmation = result
        redirect(URL(f="monitor_task"))

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_monitor_task_onaccept(form):
        """
            Process the Enabled Flag
            Create Form:
                Set deployment_id
                PrePopulate Task Options from Check Options
        """

        form_vars = form.vars
        if form.record:
            # Update form
            # Process if changed
            if form.record.enabled and not form_vars.enabled:
                S3SetupMonitorModel.setup_monitor_task_disable(form_vars.id)
            elif form_vars.enabled and not form.record.enabled:
                S3SetupMonitorModel.setup_monitor_task_enable(form_vars.id)
        else:
            # Create form
            db = current.db
            record_id = form_vars.id
            if form_vars.enabled:
                # Process only if enabled
                S3SetupMonitorModel.setup_monitor_task_enable(record_id)

            # Read default check options
            ctable = db.setup_monitor_check
            check = db(ctable.id == form_vars.check_id).select(ctable.options,
                                                               limitby = (0, 1)
                                                               ).first()

            # Read deployment_id
            ttable = db.setup_monitor_task
            server_id = form_vars.server_id
            if server_id:
                task = None
            else:
                # Read record
                task = db(ttable.id == record_id).select(ttable.id,
                                                         ttable.server_id,
                                                         limitby = (0, 1)
                                                         ).first()
                server_id = task.server_id
            stable = db.setup_server
            server = db(stable.id == server_id).select(stable.deployment_id,
                                                       limitby = (0, 1)
                                                       ).first()
            deployment_id = server.deployment_id

            # Update record
            if task:
                task.update_record(deployment_id = deployment_id,
                                   options = check.options,
                                   )
            else:
                db(ttable.id == record_id).update(deployment_id = deployment_id,
                                                  options = check.options,
                                                  )

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_monitor_task_run(r, **attr):
        """
            Run a Task

            S3Method for interactive requests
        """

        task_id = r.id
        current.s3task.run_async("setup_monitor_task_run",
                                 args = [task_id])
        current.session.confirmation = \
            current.T("The check request has been submitted, so results should appear shortly - refresh to see them")

        redirect(URL(c="setup", f="monitor_task",
                     args = [task_id, "log"],
                     ))

# =============================================================================
def setup_monitor_server_enable(server_id):
    """
        Enable Monitoring for a Server
        - Schedule all enabled Tasks

        CLI API for shell scripts & to be called by S3Method
    """

    db = current.db

    stable = current.s3db.setup_monitor_server
    record = db(stable.server_id == server_id).select(stable.id,
                                                      stable.enabled,
                                                      limitby = (0, 1)
                                                      ).first()

    if not record.enabled:
        # Flag it as enabled
        record.update_record(enabled = True)

    table = db.setup_monitor_task
    query = (table.server_id == server_id) & \
            (table.enabled == True) & \
            (table.deleted == False)
    tasks = db(query).select(table.id)

    # Do we have any Tasks already Scheduled?
    args = []
    for task in tasks:
        args.append("[%s]" % task.id)
    ttable = db.scheduler_task
    query = ((ttable.function_name == "setup_monitor_run_task") & \
             (ttable.args.belongs(args)) & \
             (ttable.status.belongs(["RUNNING",
                                     "QUEUED",
                                     "ALLOCATED"])))
    exists = db(query).select(ttable.id)
    exists = [r.id for r in exists]
    for task in tasks:
        task_id = task.id
        if task_id not in exists:
            current.s3task.schedule_task("setup_monitor_run_task",
                                         args = [task_id],
                                         period = 300,  # seconds
                                         timeout = 300, # seconds
                                         repeats = 0    # unlimited
                                         )
    return "Server Monitoring enabled"

# =============================================================================
def setup_monitor_server_enable_interactive(r, **attr):
    """
        Enable Monitoring for a Server
        - Schedule all enabled Tasks

        S3Method for interactive requests
    """

    result = setup_monitor_server_enable(r.id)
    current.session.confirmation = result
    redirect(URL(f="server"))

# =============================================================================
def setup_monitor_server_disable(server_id):
    """
        Disable Monitoring for a Server
        - Remove all related Tasks

        CLI API for shell scripts & to be called by S3Method
    """

    db = current.db

    stable = current.s3db.setup_monitor_server
    record = db(stable.server_id == server_id).select(stable.id,
                                                      stable.enabled,
                                                      limitby = (0, 1)
                                                      ).first()

    if record.enabled:
        # Flag it as disabled
        record.update_record(enabled = False)

    table = db.setup_monitor_task
    query = (table.server_id == server_id) & \
            (table.enabled == True) & \
            (table.deleted == False)
    tasks = db(query).select(table.id)

    # Do we have any Tasks already Scheduled?
    args = []
    for task in tasks:
        args.append("[%s]" % task.id)
    ttable = db.scheduler_task
    query = ((ttable.function_name == "setup_monitor_run_task") & \
             (ttable.args.belongs(args)) & \
             (ttable.status.belongs(["RUNNING",
                                     "QUEUED",
                                     "ALLOCATED"])))
    exists = db(query).select(ttable.id,
                              limitby = (0, 1)
                              ).first()
    if exists:
        # Disable all
        db(query).update(status = "STOPPED")
        return "Server Monitoring disabled"
    else:
        return "Server Monitoring already disabled"

# =============================================================================
def setup_monitor_server_disable_interactive(r, **attr):
    """
        Disable Monitoring for a Server
        - Remove all related Tasks

        S3Method for interactive requests
    """

    result = setup_monitor_server_disable(r.id)
    current.session.confirmation = result
    redirect(URL(f="server"))

# =============================================================================
def setup_monitor_server_check(r, **attr):
    """
        Run all enabled Tasks for this server

        S3Method for interactive requests
    """

    server_id = r.id
    table = current.s3db.setup_monitor_task
    query = (table.server_id == server_id) & \
            (table.enabled == True) & \
            (table.deleted == False)
    tasks = current.db(query).select(table.id)
    run_async = current.s3task.run_async
    for task in tasks:
        run_async("setup_monitor_run_task",
                  args = [task.id])
    current.session.confirmation = \
        current.T("The check requests have been submitted, so results should appear shortly - refresh to see them")

    redirect(URL(c="setup", f="server",
                 args = [server_id, "monitor_log"],
                 ))

# =============================================================================
def setup_monitor_run_task(task_id):
    """
        Check a Service
    """

    db = current.db
    table = current.s3db.setup_monitor_task
    ctable = db.setup_monitor_check

    query = (table.id == task_id) & \
            (table.check_id == ctable.id)
    row = db(query).select(table.server_id,
                           ctable.function_name,
                           limitby = (0, 1)
                           ).first()
    server_id = row["setup_monitor_task.server_id"]
    function_name = row["setup_monitor_check.function_name"]

    # Load the Monitor template for this deployment
    template = current.deployment_settings.get_setup_monitor_template()
    module_name = "applications.%s.modules.templates.%s.monitor" \
        % (current.request.application, template)
    __import__(module_name)
    mymodule = sys.modules[module_name]
    S3Monitor = mymodule.S3Monitor()

    # Get the Check Script
    try:
        fn = getattr(S3Monitor, function_name)
    except:
        current.log.error("Check Script not found: %s" % function_name)
        return None

    # Create an entry in the monitor_run table
    rtable = db.setup_monitor_run
    run_id = rtable.insert(server_id = server_id,
                           task_id = task_id,
                           )

    try:
        # Run the script
        result = fn(task_id, run_id)
    except Exception:
        result = {"traceback": sys.exc_info()[2],
                  }
        status = 3 # Critical
    else:
        try:
            status = result.get("status")
        except AttributeError:
            status = 3 # Critical
        else:
            del result["status"]

    # Store the Result & Status
    # ... in Run
    db(rtable.id == run_id).update(result = result,
                                   status = status)

    # ...in Task
    db(table.id == task_id).update(result = result,
                                   status = status)

    # ...in Host
    check_lower = None
    stable = db.setup_monitor_server
    if status == 3:
        # Task at Critical => Server -> Critical
        db(stable.id == server_id).update(status = status)
    else:
        server = db(stable.id == server_id).select(stable.id,
                                                   stable.status,
                                                   limitby = (0, 1),
                                                   ).first()
        if status == server.status:
            pass
        elif status > server.status:
            # Increase Server Status to match Task Status
            server.update_record(status = status)
        else:
            # status < server.status
            # Check if we should Lower the Server Status to match Task Status
            query = (table.id != task_id) & \
                    (table.server_id == server_id) & \
                    (table.status > status) & \
                    (table.enabled == True) & \
                    (table.deleted == False)
            higher = db(query).select(table.id,
                                      limitby = (0, 1)
                                      ).first()
            if higher is None:
                server.update_record(status = status)

    return result

# =============================================================================
def setup_monitor_check_email_reply(run_id):
    """
        Check whether we have received a reply to an Email check
    """

    rtable = current.s3db.setup_monitor_run
    record = current.db(rtable.id == run_id).select(rtable.id,
                                                    rtable.status,
                                                    limitby = (0, 1)
                                                    ).first()
    try:
        status = record.status
    except:
        # Can't find run record!
        # @ToDo: Send Alert
        pass
    else:
        if status == 2:
            # Still in Warning State: Make it go Critical
            record.update_record(status = 3)
            # @ToDo: Send Alert

# =============================================================================
def setup_write_playbook(playbook_name,
                         playbook_data,
                         tags = None,
                         ):
    """
        Write an Ansible Playbook file
    """

    try:
        import yaml
    except ImportError:
        error = "PyYAML module needed for Setup"
        current.log.error(error)
        current.response.error = error
        return

    folder = current.request.folder
    os_path = os.path
    os_path_join = os_path.join

    playbook_folder = os_path_join(folder, "uploads", "playbook")
    if not os_path.isdir(playbook_folder):
        os.mkdir(playbook_folder)

    playbook_path = os_path_join(playbook_folder, playbook_name)

    with open(playbook_path, "w") as yaml_file:
        yaml_file.write(yaml.dump(playbook_data, default_flow_style=False))

    task_vars = {"playbook": playbook_path,
                 }
    if tags:
        # only_tags
        task_vars["tags"] = tags

    return task_vars

# =============================================================================
def setup_run_playbook(playbook, instance_id=None, tags=None, hosts=None):
    """
        Run an Ansible Playbook & return the result
        - designed to be run as a Scheduled Task

        http://docs.ansible.com/ansible/latest/dev_guide/developing_api.html
        https://serversforhackers.com/c/running-ansible-2-programmatically
    """

    # No try/except here as we want ImportErrors to raise
    import shutil
    import yaml
    from ansible.module_utils.common.collections import ImmutableDict
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars.manager import VariableManager
    from ansible.inventory.manager import InventoryManager
    from ansible.playbook.play import Play
    from ansible.playbook.task_include import TaskInclude
    from ansible.executor.task_queue_manager import TaskQueueManager
    from ansible.plugins.callback import CallbackBase
    from ansible import context
    import ansible.constants as C

    #W2P_TASK = current.W2P_TASK

    if hosts is None:
        # NB This is the only current usecase as we always start on localhost
        #    - remote servers are then accessed once we have the SSH private_key available
        hosts = ["127.0.0.1"]

    # Logging
    class PlayLogger:
        """
            Store log output in a single String object.
            We create a new object per Ansible run
        """
        def __init__(self):
            self.log = ""

        def append(self, log_line):
            """ Append to log """
            self.log += log_line + "\n\n"

    logger = PlayLogger()

    class ResultCallback(CallbackBase):
        CALLBACK_VERSION = 2.0
        CALLBACK_TYPE = "stored"
        CALLBACK_NAME = "database"

        def __init__(self):

            self._last_task_banner = None
            self._last_task_name = None
            self._task_type_cache = {}
            super(ResultCallback, self).__init__()

        @staticmethod
        def _handle_exception(result):
            # Catch an exception
            # This may never be called because default handler deletes
            # the exception, since Ansible thinks it knows better
            traceback = result.get("exception")
            if traceback:
                # Extract the error message and log it
                #error = traceback.strip().split("\n")[-1]
                #logger.append(error)
                # Log the whole Traceback
                logger.append(traceback)
                # Remove the exception from the result so it's not shown every time
                del result["exception"]
                #current.s3task.scheduler.stop_task(W2P_TASK.id)
                # @ToDo: If this happens during a deploy from co-app and after nginx has replaced co-app on Port 80 then revert to co-app

        def _print_task_banner(self, task):
            args = u", ".join(u"%s=%s" % a for a in task.args.items())
            prefix = self._task_type_cache.get(task._uuid, "TASK")

            # Use cached task name
            task_name = self._last_task_name
            if task_name is None:
                task_name = task.get_name().strip()

            logger.append(u"%s: %s\n[%s]" % (prefix, task_name, args))

        def v2_runner_on_failed(self, result, ignore_errors=False):
            if self._last_task_banner != result._task._uuid:
                self._print_task_banner(result._task)

            self._handle_exception(result._result)

            if result._task.loop and "results" in result._result:
                self._process_items(result)
            else:
                logger.append("fatal: [%s]: FAILED!\n%s" % \
                    (result._host.get_name(),
                     self._dump_results(result._result, indent=4)))

        def v2_runner_on_ok(self, result):
            if isinstance(result._task, TaskInclude):
                return
            if self._last_task_banner != result._task._uuid:
                self._print_task_banner(result._task)
            if result._result.get("changed", False):
                msg = "changed: [%s]" % result._host.get_name()
            else:
                msg = "ok: [%s]" % result._host.get_name()

            if result._task.loop and "results" in result._result:
                self._process_items(result)
            else:
                self._clean_results(result._result, result._task.action)
                msg += "\n%s" % self._dump_results(result._result, indent=4)
                logger.append(msg)
                
        def v2_runner_on_unreachable(self, result):
            if self._last_task_banner != result._task._uuid:
                self._print_task_banner(result._task)
            logger.append("fatal: [%s]: UNREACHABLE!\n%s" % \
                (result._host.get_name(),
                 self._dump_results(result._result, indent=4)))

        def v2_runner_item_on_failed(self, result):
            if self._last_task_banner != result._task._uuid:
                self._print_task_banner(result._task)

            self._handle_exception(result._result)

            msg = "failed: [%s]" % (result._host.get_name())

            logger.append(msg + " (item=%s)\n%s" % \
                (self._get_item_label(result._result),
                 self._dump_results(result._result, indent=4)))

        def v2_runner_item_on_ok(self, result):
            if isinstance(result._task, TaskInclude):
                return
            if self._last_task_banner != result._task._uuid:
                self._print_task_banner(result._task)
            if result._result.get("changed", False):
                msg = "changed"
            else:
                msg = "ok"

            msg += ": [%s] (item=%s)\n%s" % \
                (result._host.get_name(),
                 self._get_item_label(result._result),
                 self._dump_results(result._result, indent=4))
            logger.append(msg)

    # Copy the current working directory to revert back to later
    cwd = os.getcwd()

    # Change working directory
    roles_path = os.path.join(current.request.folder, "private", "eden_deploy")
    os.chdir(roles_path)

    # Since the API is constructed for CLI it expects certain options to always be set in the context object
    if tags is None:
        tags = [] # Needs to be an iterable
    context.CLIARGS = ImmutableDict(module_path = [roles_path],
                                    forks = 10,
                                    become = None,
                                    become_method = None,
                                    become_user = None,
                                    check = False,
                                    diff = False,
                                    tags = tags,
                                    )

    # Initialize needed objects
    loader = DataLoader() # Takes care of finding and reading yaml, json and ini files

    # Instantiate Logging for handling results as they come in
    results_callback = ResultCallback()

    # Create Inventory and pass to Var manager
    if len(hosts) == 1:
        # Ensure that we have a comma to tell Ansible that this is a list of hosts not a file to read from
        sources = "%s," % hosts[0]
    else:
        sources = ",".join(hosts)

    inventory = InventoryManager(loader = loader,
                                 sources = sources)
    variable_manager = VariableManager(loader = loader,
                                       inventory = inventory)

    # Load Playbook
    with open(playbook, "r") as yaml_file:
        # https://msg.pyyaml.org/load
        playbooks = yaml.full_load(yaml_file)

    for play_source in playbooks:
        # Create play object, playbook objects use .load instead of init or new methods,
        # this will also automatically create the task objects from the info provided in play_source
        play = Play().load(play_source,
                           variable_manager = variable_manager,
                           loader = loader)

        # Run it - instantiate task queue manager, which takes care of forking and setting up all objects to iterate over host list and tasks
        tqm = None
        try:
            tqm = TaskQueueManager(inventory = inventory,
                                   variable_manager = variable_manager,
                                   loader = loader,
                                   passwords = None,
                                   # Use our custom callback instead of the ``default`` callback plugin, which prints to stdout
                                   stdout_callback = results_callback,
                                   )
            result = tqm.run(play) # Most interesting data for a play is actually sent to the callback's methods
        finally:
            # we always need to cleanup child procs and the structures we use to communicate with them
            if tqm is not None:
                tqm.cleanup()

            # Remove ansible tmpdir
            shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

    # Change working directory back
    os.chdir(cwd)

    # Dump Logs to File
    # Logs are in eden/uploads/playbook instead of /tmp, however it works
    log_file_name = "%s.log" % playbook.split(".")[0]
    log_path = os.path.join("/", "tmp", log_file_name)
    with open(log_path, "w") as log_file:
        log_file.write(logger.log)

    # Dump Logs to Database
    # This gets deleted:
    #current.db(current.s3db.scheduler_run.id == W2P_TASK.run_id).update(run_output = logger.log)

    if instance_id:
        # Upload logs to Database
        table = current.s3db.setup_instance
        field = table.log_file
        with open(log_path, "r") as log_file:
            newfilename = field.store(log_file,
                                      log_file_name,
                                      field.uploadfolder)
            current.db(table.id == instance_id).update(log_file = newfilename)

    return result

# =============================================================================
def setup_instance_settings_read(instance_id, deployment_id):
    """
        Read the Settings for an instance from models/000_config.py
        - called onaccept from instance creation
        - called by interactive method to read
    """

    from gluon.cfs import getcfs
    from gluon.compileapp import build_environment
    from gluon.globals import Request, Response, Session
    from gluon.restricted import restricted

    # Read current settings from file
    folder = current.request.folder
    model = "%s/models/000_config.py" % folder
    code = getcfs(model, model, None)
    request = Request({})
    request.controller = "dontrunany"
    request.folder = folder
    response = Response()
    session = Session()
    #session.connect(request, response)
    environment = build_environment(request, response, session, store_current=False)
    environment["settings"] = Storage2()
    restricted(code, environment, layer=model)
    nested_settings = environment["settings"]

    # Flatten settings
    file_settings = {}
    for section in nested_settings:
        if section == "database":
            # Filter out DB settings as these need special handling
            continue
        subsection = nested_settings[section]
        for setting in subsection:
            if setting in ("hmac_key", "template"):
                # Filter out settings which need special handling
                continue
            file_settings["%s.%s" % (section, setting)] = subsection[setting]

    # Read Settings currently in Database
    db = current.db
    stable = current.s3db.setup_setting
    id_field = stable.id
    query = (stable.instance_id == instance_id) & \
            (stable.deleted == False)
    db_settings = db(query).select(id_field,
                                   stable.setting,
                                   #stable.current_value,
                                   stable.new_value,
                                   ).as_dict(key = "setting")
    db_get = db_settings.get

    # Ensure that database looks like file
    checked_settings = []
    cappend = checked_settings.append
    from gluon.serializers import json as jsons # Need support for T()
    for setting in file_settings:
        current_value = file_settings[setting]
        if not isinstance(current_value, basestring):
            # NB Storage & OrderedDict will come out as dict
            current_value = jsons(current_value)
        s = db_get(setting)
        if s:
            # We update even if not changed so as to update modified_on
            db(id_field == s["id"]).update(current_value = current_value)
        else:
            stable.insert(deployment_id = deployment_id,
                          instance_id = instance_id,
                          setting = setting,
                          current_value = current_value,
                          )
        cappend(setting)

    # Handle db_settings not in file_settings
    for setting in db_settings:
        if setting in checked_settings:
            continue
        s = db_get(setting)
        if s["new_value"] is not None:
            db(id_field == s["id"]).update(current_value = None)
        else:
            db(id_field == s["id"]).update(deleted = True)

# =============================================================================
def setup_instance_method(instance_id, method="start"):
    """
        Run individual Ansible Roles ('methods')
            e.g. Start, Stop or Clean an Instance
            - called by interactive method to start/stop
    """

    # Read Data
    db = current.db
    s3db = current.s3db
    itable = s3db.setup_instance
    instance = db(itable.id == instance_id).select(itable.deployment_id,
                                                   itable.type,
                                                   limitby = (0, 1)
                                                   ).first()

    deployment_id = instance.deployment_id

    # Get Server(s) details
    stable = s3db.setup_server
    query = (stable.deployment_id == deployment_id) & \
            (stable.role == 1)
    server = db(query).select(stable.host_ip,
                              stable.private_key,
                              stable.remote_user,
                              limitby = (0, 1)
                              ).first()
    host_ip = server.host_ip

    # Get Deployment details
    dtable = s3db.setup_deployment
    deployment = db(dtable.id == deployment_id).select(dtable.db_type,
                                                       dtable.webserver_type,
                                                       limitby=(0, 1)
                                                       ).first()

    # Build Playbook data structure
    roles_path = os.path.join(current.request.folder, "private", "eden_deploy", "roles")

    playbook = [{"hosts": host_ip,
                 # @ToDo: "smart" & SSH Keys for non-localhost
                 "connection": "local",
                 "remote_user": server.remote_user,
                 "become_method": "sudo",
                 #"become_user": "root",
                 "vars": {"db_type": DB_SERVERS[deployment.db_type],
                          "web_server": WEB_SERVERS[deployment.webserver_type],
                          "type": INSTANCE_TYPES[instance.type],
                          },
                 "roles": [{ "role": "%s/%s" % (roles_path, method) },
                           ]
                 },
                ]

    # Write Playbook
    name = "%s_%d" % (method, int(time.time()))
    task_vars = setup_write_playbook("%s.yml" % name,
                                     playbook,
                                     )

    # Run the Playbook
    task_vars["instance_id"] = instance_id
    current.s3task.schedule_task(name,
                                 vars = task_vars,
                                 function_name = "setup_run_playbook",
                                 repeats = None,
                                 timeout = 6000,
                                 #sync_output = 300
                                 )

# =============================================================================
class Storage2(Storage):
    """
        Read settings.x.y without needing to first create settings.x
    """

    def __getattr__(self, key):
        value = dict.get(self, key)
        if value is None:
            self[key] = value = Storage2()
        return value

    def __call__(self):
        """
            settings.import_template()
        """
        return

# =============================================================================
class setup_DeploymentRepresent(S3Represent):

    def __init__(self):
        """
            Constructor
        """

        super(setup_DeploymentRepresent, self).__init__(lookup = "setup_deployment",
                                                        )

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom look-up of rows

            @param key: the key field
            @param values: the values to look up
            @param fields: unused (retained for API compatibility)
        """

        dtable = self.table
        itable = current.s3db.setup_instance

        count = len(values)
        if count == 1:
            query = (dtable.id == values[0])
        else:
            query = (dtable.id.belongs(values))

        left = itable.on((itable.deployment_id == dtable.id) & (itable.type == 1))
        rows = current.db(query).select(dtable.id,
                                        itable.url,
                                        left = left,
                                        limitby = (0, count),
                                        )
        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        if not hasattr(row, "setup_instance"):
            return str(row.id)

        return row.setup_instance.url

# =============================================================================
def setup_rheader(r, tabs=None):
    """ Resource component page header """

    rheader = None
    if r.representation == "html" and r.id:

        T = current.T
        r_name = r.name

        if r_name == "deployment":
            tabs = [(T("Deployment Details"), None),
                    (T("Servers"), "server"),
                    (T("Instances"), "instance"),
                    (T("Settings"), "setting"),
                    (T("Monitoring"), "monitor_task"),
                    ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            button = A(T("Configuration Wizard"),
                       _class="action-btn",
                       _href=URL(c="setup", f="deployment",
                                 args=[r.id, "wizard"],
                                 ),
                       )

            rheader = DIV(button,
                          rheader_tabs)

        if r_name == "server":
            tabs = [(T("Server Details"), None),
                    # Inline form instead of Tab
                    #(T("Monitoring"), "monitor_server"),
                    (T("Monitor Tasks"), "monitor_task"),
                    (T("Monitor Logs"), "monitor_log"),
                    ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            rheader = DIV(rheader_tabs)

        elif r_name == "monitor_check":
            #tabs = [(T("Check Details"), None),
            #        ]
            #rheader_tabs = s3_rheader_tabs(r, tabs)

            #record = r.record
            #table = r.table
            #rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
            #                       record.name),
            #                    TR(TH("%s: " % table.function_name.label),
            #                       record.function_name),
            #                    TR(TH("%s: " % table.comments.label),
            #                       record.comments or ""),
            #                    ), rheader_tabs)
            # No tabs => No need for rheader
            rheader = None

        elif r_name == "monitor_task":
            tabs = [(T("Task Details"), None),
                    (T("Logs"), "run"),
                    ]
            rheader_tabs = s3_rheader_tabs(r, tabs)

            record = r.record
            table = r.table
            rheader = DIV(TABLE(TR(TH("%s: " % table.server_id.label),
                                   table.server_id.represent(record.server_id)),
                                TR(TH("%s: " % table.check_id.label),
                                   table.check_id.represent(record.check_id)),
                                TR(TH("%s: " % table.status.label),
                                   table.status.represent(record.status)),
                                TR(TH("%s: " % table.enabled.label),
                                   record.enabled),
                                TR(TH("%s: " % table.comments.label),
                                   record.comments or ""),
                                ), rheader_tabs)

        return rheader

# END =========================================================================
