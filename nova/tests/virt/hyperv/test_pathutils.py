#  Copyright 2014 IBM Corp.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os

import mock

from nova import test
from nova.virt.hyperv import constants
from nova.virt.hyperv import pathutils
from nova.virt.hyperv import vmutils


class PathUtilsTestCase(test.NoDBTestCase):
    """Unit tests for the Hyper-V PathUtils class."""

    def setUp(self):
        self.fake_instance_dir = os.path.join('C:', 'fake_instance_dir')
        self.fake_instance_name = 'fake_instance_name'
        self._pathutils = pathutils.PathUtils()
        super(PathUtilsTestCase, self).setUp()

    def _mock_lookup_configdrive_path(self, ext):
        self._pathutils.get_instance_dir = mock.MagicMock(
            return_value=self.fake_instance_dir)

        def mock_exists(*args, **kwargs):
            path = args[0]
            return True if path[(path.rfind('.') + 1):] == ext else False
        self._pathutils.exists = mock_exists
        configdrive_path = self._pathutils.lookup_configdrive_path(
            self.fake_instance_name)
        return configdrive_path

    def test_lookup_configdrive_path(self):
        for format_ext in constants.DISK_FORMAT_MAP:
            configdrive_path = self._mock_lookup_configdrive_path(format_ext)
            fake_path = os.path.join(self.fake_instance_dir,
                                     'configdrive.' + format_ext)
            self.assertEqual(configdrive_path, fake_path)

    def test_lookup_configdrive_path_non_exist(self):
        self._pathutils.get_instance_dir = mock.MagicMock(
            return_value=self.fake_instance_dir)
        self._pathutils.exists = mock.MagicMock(return_value=False)
        configdrive_path = self._pathutils.lookup_configdrive_path(
            self.fake_instance_name)
        self.assertIsNone(configdrive_path)

    @mock.patch('os.path.join')
    def test_get_instances_sub_dir(self, fake_path_join):

        class WindowsError(Exception):
            def __init__(self, winerror=None):
                self.winerror = winerror

        fake_dir_name = "fake_dir_name"
        fake_windows_error = WindowsError
        self._pathutils._check_create_dir = mock.MagicMock(
            side_effect=WindowsError(pathutils.ERROR_INVALID_NAME))
        with mock.patch('__builtin__.WindowsError',
                        fake_windows_error, create=True):
            self.assertRaises(vmutils.HyperVException,
                              self._pathutils._get_instances_sub_dir,
                              fake_dir_name)

    @mock.patch.object(pathutils.PathUtils, 'get_configdrive_path')
    @mock.patch.object(pathutils.PathUtils, 'copyfile')
    def test_copy_configdrive(self, mock_copyfile, mock_get_configdrive_path):
        mock_get_configdrive_path.side_effect = [mock.sentinel.FAKE_LOCAL_PATH,
                                                 mock.sentinel.FAKE_REMOTE_PATH
                                                ]
        self._pathutils.copy_configdrive(self.fake_instance_name,
                                         mock.sentinel.DEST_HOST)

        mock_get_configdrive_path.assert_has_calls(
            [mock.call(self.fake_instance_name, constants.IDE_DVD_FORMAT),
             mock.call(self.fake_instance_name, constants.IDE_DVD_FORMAT,
                       remote_server=mock.sentinel.DEST_HOST)])

        mock_copyfile.assert_called_once_with(mock.sentinel.FAKE_LOCAL_PATH,
                                              mock.sentinel.FAKE_REMOTE_PATH)
