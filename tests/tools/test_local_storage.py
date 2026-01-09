import os
import shutil
import pytest

from pengent.utility.storage.local_storage import LocalStorage


@pytest.fixture(scope="function")
def local_storage():
    # テスト用バケット名
    bucket_name = "test_bucket"
    storage = LocalStorage(bucket_name=bucket_name)
    yield storage
    # テスト終了後にクリーンアップ
    shutil.rmtree(storage.storage_path, ignore_errors=True)


def test_upload_file(local_storage):
    test_file_path = "test_upload.txt"
    content = "Hello, Local Storage!"

    # ファイルを作成
    with open(test_file_path, "w") as f:
        f.write(content)

    try:
        # アップロード
        local_storage.upload_file(test_file_path)

        # ファイルが存在するか確認
        assert local_storage.exists_file("test_upload.txt")
    finally:
        # 後始末
        os.remove(test_file_path)


def test_upload_bytes(local_storage):
    data = b"Hello, Bytes!"
    object_name = "bytes_file.txt"

    local_storage.upload_bytes(data, object_name)

    # ファイルが存在しているか確認
    assert local_storage.exists_file(object_name)


def test_download_file(local_storage):
    # まずバイナリでファイルをアップロード
    data = b"Download me!"
    object_name = "download_test.txt"
    local_storage.upload_bytes(data, object_name)

    # ダウンロード
    download_path = "downloaded.txt"
    local_storage.download_file(object_name, download_path)

    try:
        # 内容確認
        with open(download_path, "rb") as f:
            assert f.read() == data
    finally:
        # 後始末
        os.remove(download_path)


def test_delete_file(local_storage):
    # まずファイルを作る
    data = b"Delete me!"
    object_name = "delete_test.txt"
    local_storage.upload_bytes(data, object_name)

    # 存在確認
    assert local_storage.exists_file(object_name)

    # 削除
    local_storage.delete_file(object_name)

    # 存在しないことを確認
    assert not local_storage.exists_file(object_name)


def test_list_files(local_storage):
    # ファイルを2つ作成
    files = {
        "file1.txt": b"File 1",
        "file2.txt": b"File 2",
    }
    for name, content in files.items():
        local_storage.upload_bytes(content, name)

    file_list = local_storage.list_files()

    # アップロードしたファイルがリストに存在するか確認
    assert "file1.txt" in file_list
    assert "file2.txt" in file_list


def test_exists_file_false(local_storage):
    # 存在しないファイルを確認
    assert not local_storage.exists_file("non_existent_file.txt")
