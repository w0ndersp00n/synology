import os
import time

from .api import Api


class FileStation(Api):
    """Access Synology FileStation information"""
    add = 'real_path,size,owner,time,perm'

    def get_info(self):
        """Provide File Station information"""
        return self.req(self.endpoint('SYNO.FileStation.Info',
                        cgi='entry.cgi', method='getinfo'))

    def list_share(self, writable_only=False, limit=25, offset=0,
                   sort_by='name', sort_direction='asc', additional=False):
        """List all shared folders"""
        return self.req(self.endpoint(
            'SYNO.FileStation.List',
            cgi='entry.cgi',
            method='list_share',
            extra={
                'onlywritable': writable_only,
                'limit': limit,
                'offset': offset,
                'sort_by': sort_by,
                'sort_direction': sort_direction,
                'additional': self.add if additional else ''
            }
        ))

    def list(self, path, limit=25, offset=0, sort_by='name',
             sort_direction='asc', pattern='', filetype='all',
             additional=False):
        """Enumerate files in a given folder"""
        return self.req(self.endpoint(
            'SYNO.FileStation.List',
            cgi='entry.cgi',
            method='list',
            extra={
                'folder_path': path,
                'limit': limit,
                'offset': offset,
                'sort_by': sort_by,
                'sort_direction': sort_direction,
                'pattern': pattern,
                'filetype': filetype,
                'additional': self.add if additional else ''
            }
        ))

    def get_file_info(self, path, additional=False):
        """Get information of file(s)"""
        return self.req(self.endpoint(
            'SYNO.FileStation.List',
            cgi='entry.cgi',
            method='getinfo',
            extra={
                'path': path,
                'additional': self.add if additional else ''
            }
        ))

    def search(self, path, pattern):
        """Search for files/folders"""
        start = self.req(self.endpoint(
            'SYNO.FileStation.Search',
            cgi='entry.cgi',
            method='start',
            extra={
                'folder_path': path,
                'pattern': pattern
            }
        ))
        if not 'taskid' in start.keys():
            raise NameError('taskid not in response')

        while True:
            time.sleep(0.5)
            file_list = self.req(self.endpoint(
                'SYNO.FileStation.Search',
                cgi='entry.cgi',
                method='list',
                extra={
                    'taskid': start['taskid'],
                    'limit': -1
                }
            ))
            if file_list['finished']:
                result_list = []
                for item in file_list['files']:
                    result_list.append(item['path'])
                return result_list

    def dir_size(self, path):
        """
        Get the accumulated size of files/folders within folder(s)

        Returns:
            size in octets
        """
        start = self.req(self.endpoint(
            'SYNO.FileStation.DirSize',
            cgi='entry.cgi',
            method='start',
            extra={'path': path}
        ))
        if not 'taskid' in start.keys():
            raise NameError('taskid not in response')

        while True:
            time.sleep(10)
            status = self.req(self.endpoint(
                'SYNO.FileStation.DirSize',
                cgi='entry.cgi',
                method='status',
                extra={'taskid': start['taskid']}
            ))
            if status['finished']:
                return int(status['total_size'])

    def md5(self, path):
        """Get MD5 of a file"""
        start = self.req(self.endpoint(
            'SYNO.FileStation.MD5',
            cgi='entry.cgi',
            method='start',
            extra={'file_path': path}
        ))
        if not 'taskid' in start.keys():
            raise NameError('taskid not in response')

        while True:
            time.sleep(10)
            status = self.req(self.endpoint(
                'SYNO.FileStation.MD5',
                cgi='entry.cgi',
                method='status',
                extra={'taskid': start['taskid']}
            ))
            if status['finished']:
                return status['md5']

    def permission(self, path):
        """Check if user has permission to write to a path"""
        return self.req(self.endpoint(
            'SYNO.FileStation.CheckPermission',
            cgi='entry.cgi',
            method='write',
            extra={
                'path': path,
                'create_only': 'false'
            }
        ))

    def delete(self, path):
        """
        Delete file(s)/folder(s)

        Using the blocking method for now
        """
        self.req(self.endpoint(
            'SYNO.FileStation.Delete',
            cgi='entry.cgi',
            method='delete',
            extra={'path': path}
        ))

    def create(self, path, name, force_parent=True, additional=False):
        """
        Create folders

        Does not support several path/name tuple as the API does
        """
        return self.req(self.endpoint(
            'SYNO.FileStation.CreateFolder',
            cgi='entry.cgi',
            method='create',
            extra={
                'name': name,
                'folder_path': path,
                'force_parent': force_parent,
                'additional': self.add if additional else ''
            }
        ))

    def rename(self, path, name, additional=False):
        """Rename a file/folder"""
        return self.req(self.endpoint(
            'SYNO.FileStation.Rename',
            cgi='entry.cgi',
            method='rename',
            extra={
                'name': name,
                'path': path,
                'additional': self.add if additional else ''
            }
        ))

    def thumb(self, path, size='small', rotate='0'):
        """Get thumbnail of file"""
        return self.req_binary(self.endpoint(
            'SYNO.FileStation.Thumb',
            cgi='entry.cgi',
            method='get',
            extra={
                'path': path,
                'size': size,
                'rotate': rotate
            }
        ))

    def download(self, path, mode='open', **kwargs):
        """Download files/folders"""
        return self.req_binary(self.endpoint(
            'SYNO.FileStation.Download',
            cgi='entry.cgi',
            method='download',
            extra={
                'path': path,
                'mode': mode
            }
        ), **kwargs)

    def upload(self, path, data, overwrite=True):
        """Upload file"""
        dir = os.path.dirname(path)
        file = os.path.basename(path)
        return self.req_post(self.base_endpoint('entry.cgi'),
            data={
                'api': 'SYNO.FileStation.Upload',
                'version': '1',
                'method': 'upload',
                'create_parents': True,
                # None tells API to throw an error if file exists
                'overwrite': True if overwrite else None,
                'dest_folder_path': dir,
                '_sid': self.sid
            },
            files={
                'file': (file, data, 'application/octet-stream')
            }
        )
