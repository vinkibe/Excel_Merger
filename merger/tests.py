import os
import json
import uuid
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from io import BytesIO

import pandas as pd
from django.test import TestCase, RequestFactory, Client
from django.http import Http404
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from merger.views import index, analyse, merge, download, reset


class IndexViewTests(TestCase):
    """Tests for the index view"""

    def setUp(self):
        self.factory = RequestFactory()

    def test_index_flushes_session_and_renders_template(self):
        """Should flush session and render index page on GET request"""
        request = self.factory.get('/')
        request.session = {}
        request.session['test_key'] = 'test_value'

        response = index(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn('merger/index.html', response.template_name)

    def test_index_clears_all_session_data(self):
        """Should clear all session data when accessing index"""
        request = self.factory.get('/')
        request.session = {'session_id': 'old_id', 'file1_path': '/path/to/file'}

        index(request)

        # Session should be flushed
        self.assertEqual(len(request.session), 0)


class AnalyseViewTests(TestCase):
    """Tests for the analyse view"""

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()

    def test_analyse_redirects_on_non_post_request(self):
        """Should redirect to index on non-POST request"""
        request = self.factory.get('/analyse/')
        request.session = {}

        response = analyse(request)

        self.assertEqual(response.status_code, 302)
        self.assertIn('index', response.url)

    def test_analyse_rejects_missing_file1(self):
        """Should reject file uploads when file1 is not provided"""
        request = self.factory.post('/analyse/')
        request.FILES = {'file2': SimpleUploadedFile('test.xlsx', b'content')}
        request.session = {}

        response = analyse(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        self.assertIn('both files', response.context['error'].lower())

    def test_analyse_rejects_missing_file2(self):
        """Should reject file uploads when file2 is not provided"""
        request = self.factory.post('/analyse/')
        request.FILES = {'file1': SimpleUploadedFile('test.xlsx', b'content')}
        request.session = {}

        response = analyse(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        self.assertIn('both files', response.context['error'].lower())

    def test_analyse_rejects_invalid_file_extension_xlsx(self):
        """Should reject files with invalid extensions"""
        request = self.factory.post('/analyse/')
        request.FILES = {
            'file1': SimpleUploadedFile('test.txt', b'content'),
            'file2': SimpleUploadedFile('test.xlsx', b'content'),
        }
        request.session = {}

        response = analyse(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        self.assertIn('Invalid file type', response.context['error'])

    def test_analyse_rejects_invalid_file_extension_both(self):
        """Should reject both files if either has invalid extension"""
        request = self.factory.post('/analyse/')
        request.FILES = {
            'file1': SimpleUploadedFile('test.pdf', b'content'),
            'file2': SimpleUploadedFile('test.doc', b'content'),
        }
        request.session = {}

        response = analyse(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)

    def test_analyse_accepts_xlsx_files(self):
        """Should accept .xlsx files"""
        mock_df = pd.DataFrame({'id': [1, 2], 'name': ['A', 'B']})

        with patch('merger.views.Path.mkdir'), \
             patch('builtins.open', mock_open()), \
             patch('merger.views.pd.read_excel', return_value=mock_df):

            request = self.factory.post('/analyse/')
            request.FILES = {
                'file1': SimpleUploadedFile('test1.xlsx', b'content'),
                'file2': SimpleUploadedFile('test2.xlsx', b'content'),
            }
            request.session = {}

            response = analyse(request)

            self.assertEqual(response.status_code, 200)
            self.assertNotIn('error', response.context)

    def test_analyse_accepts_csv_files(self):
        """Should accept .csv files"""
        mock_df = pd.DataFrame({'id': [1, 2], 'name': ['A', 'B']})

        with patch('merger.views.Path.mkdir'), \
             patch('builtins.open', mock_open()), \
             patch('merger.views.pd.read_csv', return_value=mock_df):

            request = self.factory.post('/analyse/')
            request.FILES = {
                'file1': SimpleUploadedFile('test1.csv', b'content'),
                'file2': SimpleUploadedFile('test2.csv', b'content'),
            }
            request.session = {}

            response = analyse(request)

            self.assertEqual(response.status_code, 200)
            self.assertNotIn('error', response.context)

    def test_analyse_accepts_xls_files(self):
        """Should accept .xls files"""
        mock_df = pd.DataFrame({'id': [1, 2], 'name': ['A', 'B']})

        with patch('merger.views.Path.mkdir'), \
             patch('builtins.open', mock_open()), \
             patch('merger.views.pd.read_excel', return_value=mock_df):

            request = self.factory.post('/analyse/')
            request.FILES = {
                'file1': SimpleUploadedFile('test1.xls', b'content'),
                'file2': SimpleUploadedFile('test2.xls', b'content'),
            }
            request.session = {}

            response = analyse(request)

            self.assertEqual(response.status_code, 200)
            self.assertNotIn('error', response.context)

    def test_analyse_handles_file_read_errors(self):
        """Should handle errors when reading files"""
        with patch('merger.views.Path.mkdir'), \
             patch('builtins.open', mock_open()), \
             patch('merger.views.pd.read_excel', side_effect=Exception('Read error')):

            request = self.factory.post('/analyse/')
            request.FILES = {
                'file1': SimpleUploadedFile('test1.xlsx', b'content'),
                'file2': SimpleUploadedFile('test2.xlsx', b'content'),
            }
            request.session = {}

            response = analyse(request)

            self.assertEqual(response.status_code, 200)
            self.assertIn('error', response.context)
            self.assertIn('Error reading files', response.context['error'])

    def test_analyse_extracts_dataframe_metadata(self):
        """Should successfully analyze and extract metadata from uploaded files"""
        mock_df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', None],
            'age': [25, 30, 35]
        })

        with patch('merger.views.Path.mkdir'), \
             patch('builtins.open', mock_open()), \
             patch('merger.views.pd.read_excel', return_value=mock_df):

            request = self.factory.post('/analyse/')
            request.FILES = {
                'file1': SimpleUploadedFile('test1.xlsx', b'content'),
                'file2': SimpleUploadedFile('test2.xlsx', b'content'),
            }
            request.session = {}

            response = analyse(request)

            self.assertEqual(response.status_code, 200)
            analysis1 = response.context['analysis1']

            self.assertEqual(analysis1['rows'], 3)
            self.assertEqual(analysis1['col_count'], 3)
            self.assertIn('id', analysis1['columns'])
            self.assertIn('name', analysis1['columns'])
            self.assertEqual(analysis1['null_counts']['name'], 1)
            self.assertEqual(analysis1['duplicates'], 0)

    def test_analyse_identifies_common_columns(self):
        """Should identify common columns between files"""
        df1 = pd.DataFrame({'id': [1, 2], 'name': ['A', 'B'], 'col1': [10, 20]})
        df2 = pd.DataFrame({'id': [1, 2], 'name': ['A', 'B'], 'col2': [30, 40]})

        with patch('merger.views.Path.mkdir'), \
             patch('builtins.open', mock_open()), \
             patch('merger.views.pd.read_excel', side_effect=[df1, df2]):

            request = self.factory.post('/analyse/')
            request.FILES = {
                'file1': SimpleUploadedFile('test1.xlsx', b'content'),
                'file2': SimpleUploadedFile('test2.xlsx', b'content'),
            }
            request.session = {}

            response = analyse(request)

            common_cols = response.context['common_cols']
            self.assertIn('id', common_cols)
            self.assertIn('name', common_cols)
            self.assertNotIn('col1', common_cols)
            self.assertNotIn('col2', common_cols)

    def test_analyse_suggests_merge_keys(self):
        """Should suggest merge keys based on column names and uniqueness"""
        df1 = pd.DataFrame({'id': [1, 2, 3], 'name': ['A', 'B', 'C']})
        df2 = pd.DataFrame({'id': [1, 2, 3], 'name': ['A', 'B', 'C']})

        with patch('merger.views.Path.mkdir'), \
             patch('builtins.open', mock_open()), \
             patch('merger.views.pd.read_excel', side_effect=[df1, df2]):

            request = self.factory.post('/analyse/')
            request.FILES = {
                'file1': SimpleUploadedFile('test1.xlsx', b'content'),
                'file2': SimpleUploadedFile('test2.xlsx', b'content'),
            }
            request.session = {}

            response = analyse(request)

            key_suggestions = response.context['key_suggestions']
            self.assertGreater(len(key_suggestions), 0)
            # 'id' should be suggested as it contains 'id' keyword
            suggested_cols = [s['col'] for s in key_suggestions]
            self.assertIn('id', suggested_cols)

    def test_analyse_stores_file_paths_in_session(self):
        """Should store file paths in session for later use"""
        mock_df = pd.DataFrame({'id': [1, 2], 'name': ['A', 'B']})

        with patch('merger.views.Path.mkdir'), \
             patch('builtins.open', mock_open()), \
             patch('merger.views.pd.read_excel', return_value=mock_df):

            request = self.factory.post('/analyse/')
            request.FILES = {
                'file1': SimpleUploadedFile('test1.xlsx', b'content'),
                'file2': SimpleUploadedFile('test2.xlsx', b'content'),
            }
            request.session = {}

            analyse(request)

            self.assertIn('session_id', request.session)
            self.assertIn('file1_path', request.session)
            self.assertIn('file2_path', request.session)
            self.assertIn('file1_name', request.session)
            self.assertIn('file2_name', request.session)


class MergeViewTests(TestCase):
    """Tests for the merge view"""

    def setUp(self):
        self.factory = RequestFactory()

    def test_merge_redirects_on_non_post_request(self):
        """Should redirect to index on non-POST request"""
        request = self.factory.get('/merge/')
        request.session = {}

        response = merge(request)

        self.assertEqual(response.status_code, 302)
        self.assertIn('index', response.url)

    def test_merge_redirects_when_files_not_in_session(self):
        """Should redirect when file paths are not in session"""
        request = self.factory.post('/merge/')
        request.session = {}
        request.POST = {'merge_key': 'id', 'merge_type': 'inner'}

        response = merge(request)

        self.assertEqual(response.status_code, 302)
        self.assertIn('index', response.url)

    def test_merge_rejects_invalid_merge_key(self):
        """Should validate merge key exists in both files before merging"""
        mock_df = pd.DataFrame({'id': [1, 2], 'name': ['A', 'B']})

        with patch('merger.views.pd.read_excel', return_value=mock_df):
            request = self.factory.post('/merge/')
            request.session = {
                'file1_path': '/path/to/file1.xlsx',
                'file2_path': '/path/to/file2.xlsx',
                'file1_name': 'File1',
                'file2_name': 'File2',
                'session_id': 'test-session',
            }
            request.POST = {'merge_key': 'invalid_key', 'merge_type': 'inner'}

            response = merge(request)

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertIn('error', data)
            self.assertIn('not found', data['error'].lower())

    def test_merge_performs_inner_join(self):
        """Should perform merge operations with correct merge type"""
        df1 = pd.DataFrame({'id': [1, 2, 3], 'name': ['A', 'B', 'C']})
        df2 = pd.DataFrame({'id': [2, 3, 4], 'value': [20, 30, 40]})

        with patch('merger.views.pd.read_excel', side_effect=[df1, df2]), \
             patch('merger.views.Path.mkdir'), \
             patch('merger.views.pd.ExcelWriter') as mock_writer:

            request = self.factory.post('/merge/')
            request.session = {
                'file1_path': '/path/to/file1.xlsx',
                'file2_path': '/path/to/file2.xlsx',
                'file1_name': 'File1',
                'file2_name': 'File2',
                'session_id': 'test-session',
            }
            request.POST = {
                'merge_key': 'id',
                'merge_type': 'inner',
                'handle_duplicates': 'keep_first',
                'output_name': 'merged',
            }

            response = merge(request)

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data['success'])

    def test_merge_performs_outer_join(self):
        """Should support outer merge type"""
        df1 = pd.DataFrame({'id': [1, 2], 'name': ['A', 'B']})
        df2 = pd.DataFrame({'id': [2, 3], 'value': [20, 30]})

        with patch('merger.views.pd.read_excel', side_effect=[df1, df2]), \
             patch('merger.views.Path.mkdir'), \
             patch('merger.views.pd.ExcelWriter'):

            request = self.factory.post('/merge/')
            request.session = {
                'file1_path': '/path/to/file1.xlsx',
                'file2_path': '/path/to/file2.xlsx',
                'file1_name': 'File1',
                'file2_name': 'File2',
                'session_id': 'test-session',
            }
            request.POST = {
                'merge_key': 'id',
                'merge_type': 'outer',
                'handle_duplicates': 'keep_first',
                'output_name': 'merged',
            }

            response = merge(request)

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data['success'])

    def test_merge_handles_duplicates_keep_first(self):
        """Should handle duplicates with keep_first strategy"""
        df1 = pd.DataFrame({'id': [1, 1, 2], 'name': ['A', 'A', 'B']})
        df2 = pd.DataFrame({'id': [1, 2], 'value': [10, 20]})

        with patch('merger.views.pd.read_excel', side_effect=[df1, df2]), \
             patch('merger.views.Path.mkdir'), \
             patch('merger.views.pd.ExcelWriter'):

            request = self.factory.post('/merge/')
            request.session = {
                'file1_path': '/path/to/file1.xlsx',
                'file2_path': '/path/to/file2.xlsx',
                'file1_name': 'File1',
                'file2_name': 'File2',
                'session_id': 'test-session',
            }
            request.POST = {
                'merge_key': 'id',
                'merge_type': 'inner',
                'handle_duplicates': 'keep_first',
                'output_name': 'merged',
            }

            response = merge(request)

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data['success'])

    def test_merge_handles_duplicates_keep_last(self):
        """Should handle duplicates with keep_last strategy"""
        df1 = pd.DataFrame({'id': [1, 1, 2], 'name': ['A', 'A', 'B']})
        df2 = pd.DataFrame({'id': [1, 2], 'value': [10, 20]})

        with patch('merger.views.pd.read_excel', side_effect=[df1, df2]), \
             patch('merger.views.Path.mkdir'), \
             patch('merger.views.pd.ExcelWriter'):

            request = self.factory.post('/merge/')
            request.session = {
                'file1_path': '/path/to/file1.xlsx',
                'file2_path': '/path/to/file2.xlsx',
                'file1_name': 'File1',
                'file2_name': 'File2',
                'session_id': 'test-session',
            }
            request.POST = {
                'merge_key': 'id',
                'merge_type': 'inner',
                'handle_duplicates': 'keep_last',
                'output_name': 'merged',
            }

            response = merge(request)

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data['success'])

    def test_merge_handles_duplicates_keep_all(self):
        """Should handle duplicates with keep_all strategy"""
        df1 = pd.DataFrame({'id': [1, 1, 2], 'name': ['A', 'A', 'B']})
        df2 = pd.DataFrame({'id': [1, 2], 'value': [10, 20]})

        with patch('merger.views.pd.read_excel', side_effect=[df1, df2]), \
             patch('merger.views.Path.mkdir'), \
             patch('merger.views.pd.ExcelWriter'):

            request = self.factory.post('/merge/')
            request.session = {
                'file1_path': '/path/to/file1.xlsx',
                'file2_path': '/path/to/file2.xlsx',
                'file1_name': 'File1',
                'file2_name': 'File2',
                'session_id': 'test-session',
            }
            request.POST = {
                'merge_key': 'id',
                'merge_type': 'inner',
                'handle_duplicates': 'keep_all',
                'output_name': 'merged',
            }

            response = merge(request)

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data['success'])

    def test_merge_generates_styled_excel_output(self):
        """Should generate styled Excel output with multiple sheets"""
        df1 = pd.DataFrame({'id': [1, 2], 'name': ['A', 'B']})
        df2 = pd.DataFrame({'id': [1, 2], 'value': [10, 20]})

        with patch('merger.views.pd.read_excel', side_effect=[df1, df2]), \
             patch('merger.views.Path.mkdir'), \
             patch('merger.views.pd.ExcelWriter') as mock_writer_class:

            mock_writer = MagicMock()
            mock_writer_class.return_value.__enter__.return_value = mock_writer
            mock_writer.book = MagicMock()
            mock_writer.book.__getitem__ = MagicMock(return_value=MagicMock())

            request = self.factory.post('/merge/')
            request.session = {
                'file1_path': '/path/to/file1.xlsx',
                'file2_path': '/path/to/file2.xlsx',
                'file1_name': 'File1',
                'file2_name': 'File2',
                'session_id': 'test-session',
            }
            request.POST = {
                'merge_key': 'id',
                'merge_type': 'inner',
                'handle_duplicates': 'keep_first',
                'output_name': 'merged',
            }

            response = merge(request)

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data['success'])

    def test_merge_sanitizes_output_filename(self):
        """Should sanitize output filename to prevent invalid characters"""
        df1 = pd.DataFrame({'id': [1, 2], 'name': ['A', 'B']})
        df2 = pd.DataFrame({'id': [1, 2], 'value': [10, 20]})

        with patch('merger.views.pd.read_excel', side_effect=[df1, df2]), \
             patch('merger.views.Path.mkdir'), \
             patch('merger.views.pd.ExcelWriter'):

            request = self.factory.post('/merge/')
            request.session = {
                'file1_path': '/path/to/file1.xlsx',
                'file2_path': '/path/to/file2.xlsx',
                'file1_name': 'File1',
                'file2_name': 'File2',
                'session_id': 'test-session',
            }
            request.POST = {
                'merge_key': 'id',
                'merge_type': 'inner',
                'handle_duplicates': 'keep_first',
                'output_name': 'merged@#$%^&*()',
            }

            response = merge(request)

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data['success'])
            # Filename should be sanitized
            self.assertNotIn('@', data['output_name'])
            self.assertNotIn('#', data['output_name'])

    def test_merge_returns_statistics(self):
        """Should return merge statistics in response"""
        df1 = pd.DataFrame({'id': [1, 2, 3], 'name': ['A', 'B', 'C']})
        df2 = pd.DataFrame({'id': [1, 2, 3], 'value': [10, 20, 30]})

        with patch('merger.views.pd.read_excel', side_effect=[df1, df2]), \
             patch('merger.views.Path.mkdir'), \
             patch('merger.views.pd.ExcelWriter'):

            request = self.factory.post('/merge/')
            request.session = {
                'file1_path': '/path/to/file1.xlsx',
                'file2_path': '/path/to/file2.xlsx',
                'file1_name': 'File1',
                'file2_name': 'File2',
                'session_id': 'test-session',
            }
            request.POST = {
                'merge_key': 'id',
                'merge_type': 'inner',
                'handle_duplicates': 'keep_first',
                'output_name': 'merged',
            }

            response = merge(request)

            data = json.loads(response.content)
            stats = data['stats']
            self.assertIn('total_rows', stats)
            self.assertIn('columns', stats)
            self.assertIn('file1_rows', stats)
            self.assertIn('file2_rows', stats)
            self.assertIn('filename', stats)

    def test_merge_handles_read_errors(self):
        """Should handle errors when reading files during merge"""
        with patch('merger.views.pd.read_excel', side_effect=Exception('Read error')):
            request = self.factory.post('/merge/')
            request.session = {
                'file1_path': '/path/to/file1.xlsx',
                'file2_path': '/path/to/file2.xlsx',
                'file1_name': 'File1',
                'file2_name': 'File2',
                'session_id': 'test-session',
            }
            request.POST = {
                'merge_key': 'id',
                'merge_type': 'inner',
                'handle_duplicates': 'keep_first',
                'output_name': 'merged',
            }

            response = merge(request)

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertIn('error', data)


class DownloadViewTests(TestCase):
    """Tests for the download view"""

    def setUp(self):
        self.factory = RequestFactory()

    def test_download_enforces_session_security(self):
        """Should enforce security by only allowing download of session-specific files"""
        request = self.factory.get('/download/some_file.xlsx')
        request.session = {'output_file': 'different_file.xlsx'}

        with self.assertRaises(Http404):
            download(request, 'some_file.xlsx')

    def test_download_allows_session_file(self):
        """Should allow download of file matching session output_file"""
        with patch('merger.views.OUTPUT_DIR') as mock_output_dir, \
             patch('builtins.open', mock_open(read_data=b'file content')):

            mock_file_path = MagicMock()
            mock_file_path.exists.return_value = True
            mock_output_dir.__truediv__.return_value = mock_file_path

            request = self.factory.get('/download/test_file.xlsx')
            request.session = {'output_file': 'test_file.xlsx'}

            response = download(request, 'test_file.xlsx')

            self.assertEqual(response.status_code, 200)

    def test_download_raises_404_for_missing_file(self):
        """Should raise 404 when file does not exist"""
        with patch('merger.views.OUTPUT_DIR') as mock_output_dir:
            mock_file_path = MagicMock()
            mock_file_path.exists.return_value = False
            mock_output_dir.__truediv__.return_value = mock_file_path

            request = self.factory.get('/download/missing_file.xlsx')
            request.session = {'output_file': 'missing_file.xlsx'}

            with self.assertRaises(Http404):
                download(request, 'missing_file.xlsx')

    def test_download_sets_correct_content_type(self):
        """Should set correct content type for Excel files"""
        with patch('merger.views.OUTPUT_DIR') as mock_output_dir, \
             patch('builtins.open', mock_open(read_data=b'file content')):

            mock_file_path = MagicMock()
            mock_file_path.exists.return_value = True
            mock_output_dir.__truediv__.return_value = mock_file_path

            request = self.factory.get('/download/test_file.xlsx')
            request.session = {'output_file': 'test_file.xlsx'}

            response = download(request, 'test_file.xlsx')

            self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         response['Content-Type'])

    def test_download_sets_attachment_header(self):
        """Should set Content-Disposition header for file download"""
        with patch('merger.views.OUTPUT_DIR') as mock_output_dir, \
             patch('builtins.open', mock_open(read_data=b'file content')):

            mock_file_path = MagicMock()
            mock_file_path.exists.return_value = True
            mock_output_dir.__truediv__.return_value = mock_file_path

            request = self.factory.get('/download/test_file.xlsx')
            request.session = {'output_file': 'test_file.xlsx'}

            response = download(request, 'test_file.xlsx')

            self.assertIn('attachment', response['Content-Disposition'])


class ResetViewTests(TestCase):
    """Tests for the reset view"""

    def setUp(self):
        self.factory = RequestFactory()

    def test_reset_flushes_session_and_redirects(self):
        """Should flush session and redirect to index"""
        request = self.factory.get('/reset/')
        request.session = {'session_id': 'test', 'file1_path': '/path'}

        response = reset(request)

        self.assertEqual(response.status_code, 302)
        self.assertIn('index', response.url)
