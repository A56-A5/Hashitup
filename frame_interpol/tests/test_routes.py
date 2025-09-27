import pytest
from unittest.mock import patch, MagicMock
from demo.app import create_app
import os
from werkzeug.utils import secure_filename
import json

@pytest.fixture(autouse=True)
def mock_utils(error_type=None):
    gemini_cache = {}
    interpolation_cache = {}

    def mock_os_path_exists(path):
        if "gemini" in path and path in gemini_cache:
            return True
        if "interpolation" in path and path in interpolation_cache:
            return True
        return False

    def mock_json_load_func(f):
        path = f.name
        if "gemini" in path and path in gemini_cache:
            return gemini_cache[path]
        if "interpolation" in path and path in interpolation_cache:
            return interpolation_cache[path]
        raise FileNotFoundError(f"No such file or directory: '{path}'")

    def mock_json_dump_func(data, f):
        path = f.name
        if "gemini" in path:
            gemini_cache[path] = data
        elif "interpolation" in path:
            interpolation_cache[path] = data

    def mock_os_listdir(path):
        if "interpolation" in path and path in interpolation_cache:
            return interpolation_cache[path]
        return []

    with patch('demo.app.utils.generate_gemini_prompt') as mock_gemini:
        with patch('demo.app.utils.interpolate_frames') as mock_interpolate:
            with patch('demo.app.utils.generate_pollinations_video') as mock_pollinations:
                with patch('demo.app.routes.os.makedirs') as mock_makedirs:
                    with patch('demo.app.routes.os.path.exists', side_effect=mock_os_path_exists) as mock_exists:
                        with patch('demo.app.routes.secure_filename') as mock_secure_filename:
                            with patch('werkzeug.datastructures.FileStorage.save') as mock_file_save:
                                with patch('builtins.open') as mock_open:
                                    mock_file_handle = MagicMock()
                                    mock_open.return_value.__enter__.return_value = mock_file_handle
                                    mock_file_handle.write.return_value = None
                                    with patch('json.load', side_effect=mock_json_load_func) as mock_json_load:
                                        with patch('json.dump', side_effect=mock_json_dump_func) as mock_json_dump:
                                            with patch('demo.app.routes.os.listdir', side_effect=mock_os_listdir) as mock_listdir:

                                                mock_gemini.return_value = "A descriptive prompt"
                                                mock_interpolate.return_value = [f"frame_{i}.png" for i in range(10)]
                                                mock_pollinations.return_value = "video_url.mp4"
                                                mock_makedirs.return_value = None # Prevent actual directory creation
                                                mock_secure_filename.side_effect = lambda x: x # Don't change filename during testing
                                                mock_file_save.return_value = None # Prevent actual file saving

                                                if error_type == "gemini":
                                                    mock_gemini.side_effect = Exception("Gemini Error")
                                                elif error_type == "interpolation":
                                                    mock_interpolate.side_effect = Exception("Interpolation Error")
                                                elif error_type == "pollinations":
                                                    mock_pollinations.side_effect = Exception("Pollinations Error")

                                                yield mock_gemini, mock_interpolate, mock_pollinations, mock_makedirs, mock_exists, mock_secure_filename, mock_file_save, mock_open, mock_json_load, mock_json_dump, mock_listdir, gemini_cache, interpolation_cache

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_transform_video_get(client):
    response = client.get('/transform_video')
    assert response.status_code == 405

def test_transform_video_post_missing_files(client):
    response = client.post('/transform_video', data={})
    assert response.status_code == 400
    assert b'Missing one or both image files' in response.data

def test_transform_video_post_success(client, mock_utils):
    mock_gemini, mock_interpolate, mock_pollinations, mock_makedirs, mock_exists, mock_secure_filename, mock_file_save, mock_open, mock_json_load, mock_json_dump, mock_listdir, gemini_cache, interpolation_cache = mock_utils
    # Simulate cache hit for Gemini and interpolation
    gemini_cache["gemini_cache_path"] = {'prompt': "Cached prompt"}
    interpolation_cache["interpolation_cache_path"] = [f"frame_{i}.png" for i in range(10)]
    mock_exists.side_effect = lambda path: path in gemini_cache or path in interpolation_cache
    mock_json_load.side_effect = lambda f: gemini_cache[f.name] if "gemini" in f.name else interpolation_cache[f.name]
    mock_listdir.side_effect = lambda path: interpolation_cache[path] if "interpolation" in path else []

    data = {
        'image1': (MagicMock(spec=bytes), 'test_image1.jpg'),
        'image2': (MagicMock(spec=bytes), 'test_image2.jpg'),
        'year1': '2000',
        'year2': '2010',
        'location': 'TestLocation'
    }
    response = client.post('/transform_video', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    assert b'video_url.mp4' in response.data
    mock_gemini.assert_not_called() # Should not be called if cache hit
    mock_json_load.assert_called_once()
    mock_interpolate.assert_not_called() # Should not be called if cache hit
    mock_pollinations.assert_called_once()
    mock_file_save.assert_called()

def test_transform_video_post_success_no_cache(client, mock_utils):
    mock_gemini, mock_interpolate, mock_pollinations, mock_makedirs, mock_exists, mock_secure_filename, mock_file_save, mock_open, mock_json_load, mock_json_dump, mock_listdir, gemini_cache, interpolation_cache = mock_utils
    mock_exists.side_effect = lambda path: False # Simulate cache miss for Gemini and interpolation
    mock_listdir.side_effect = lambda path: []

    data = {
        'image1': (MagicMock(spec=bytes), 'test_image1.jpg'),
        'image2': (MagicMock(spec=bytes), 'test_image2.jpg'),
        'year1': '2000',
        'year2': '2010',
        'location': 'TestLocation'
    }
    response = client.post('/transform_video', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    assert b'video_url.mp4' in response.data
    mock_gemini.assert_called_once()
    mock_json_dump.assert_called_once()
    mock_interpolate.assert_called_once()
    mock_pollinations.assert_called_once()
    mock_file_save.assert_called()

def test_transform_video_post_invalid_years(client, mock_utils):
    _, _, _, _, _, _, _, _, _, _, _, _, _ = mock_utils
    data = {
        'image1': (MagicMock(spec=bytes), 'test_image1.jpg'),
        'image2': (MagicMock(spec=bytes), 'test_image2.jpg'),
        'year1': 'abcd',
        'year2': '2010',
        'location': 'TestLocation'
    }
    response = client.post('/transform_video', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert b'Missing year or location metadata' in response.data

@pytest.mark.parametrize("mock_utils", ["gemini"], indirect=True)
def test_transform_video_post_gemini_error(client, mock_utils):
    mock_gemini, _, _, _, _, _, mock_file_save, _, _, _, _, _, _ = mock_utils
    mock_gemini.side_effect = Exception("Gemini Error")
    data = {
        'image1': (MagicMock(spec=bytes), 'test_image1.jpg'),
        'image2': (MagicMock(spec=bytes), 'test_image2.jpg'),
        'year1': '2000',
        'year2': '2010',
        'location': 'TestLocation'
    }
    response = client.post('/transform_video', data=data, content_type='multipart/form-data')
    assert response.status_code == 500
    assert b'Error generating Gemini prompt' in response.data
    mock_file_save.assert_called()

@pytest.mark.parametrize("mock_utils", ["interpolation"], indirect=True)
def test_transform_video_post_interpolation_error(client, mock_utils):
    _, mock_interpolate, _, _, _, _, mock_file_save, _, _, _, _, _, _ = mock_utils
    mock_interpolate.side_effect = Exception("Interpolation Error")
    data = {
        'image1': (MagicMock(spec=bytes), 'test_image1.jpg'),
        'image2': (MagicMock(spec=bytes), 'test_image2.jpg'),
        'year1': '2000',
        'year2': '2010',
        'location': 'TestLocation'
    }
    response = client.post('/transform_video', data=data, content_type='multipart/form-data')
    assert response.status_code == 500
    assert b'Error during frame interpolation' in response.data
    mock_file_save.assert_called()

@pytest.mark.parametrize("mock_utils", ["pollinations"], indirect=True)
def test_transform_video_post_pollinations_error(client, mock_utils):
    _, _, mock_pollinations, _, _, _, mock_file_save, _, _, _, _, _, _ = mock_utils
    mock_pollinations.side_effect = Exception("Pollinations Error")
    data = {
        'image1': (MagicMock(spec=bytes), 'test_image1.jpg'),
        'image2': (MagicMock(spec=bytes), 'test_image2.jpg'),
        'year1': '2000',
        'year2': '2010',
        'location': 'TestLocation'
    }
    response = client.post('/transform_video', data=data, content_type='multipart/form-data')
    assert response.status_code == 500
    assert b'Error generating Pollinations video' in response.data
    mock_file_save.assert_called()