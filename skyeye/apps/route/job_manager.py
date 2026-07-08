import json
import os
import re
import tempfile
import time
import uuid
from datetime import datetime

from django.conf import settings


JOB_ID_PATTERN = re.compile(r'^[a-f0-9]{32}$')
JSON_READ_ATTEMPTS = 10


def job_root():
    path = os.path.join(settings.BASE_DIR, 'static', 'route_jobs')
    os.makedirs(path, exist_ok=True)
    return path


def validate_job_id(job_id):
    if not JOB_ID_PATTERN.fullmatch(str(job_id or '')):
        raise ValueError('无效的任务编号')
    return str(job_id)


def job_dir(job_id):
    return os.path.join(job_root(), validate_job_id(job_id))


def job_file(job_id, name):
    return os.path.join(job_dir(job_id), name)


def _write_json_atomic(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, temp_path = tempfile.mkstemp(
        prefix='.route-job-',
        suffix='.json',
        dir=os.path.dirname(path),
    )
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as file_obj:
            json.dump(data, file_obj, ensure_ascii=False)
            file_obj.flush()
            os.fsync(file_obj.fileno())
        last_error = None
        for attempt in range(8):
            try:
                os.replace(temp_path, path)
                break
            except PermissionError as exc:
                last_error = exc
                time.sleep(0.03 * (attempt + 1))
        else:
            raise last_error
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except PermissionError:
                pass


def _read_json_with_retry(path, attempts=JSON_READ_ATTEMPTS):
    """读取后台任务 JSON，规避 Windows 原子替换时的瞬时访问冲突。"""
    last_error = None
    for attempt in range(attempts):
        try:
            with open(path, 'r', encoding='utf-8') as file_obj:
                return json.load(file_obj)
        except (PermissionError, FileNotFoundError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < attempts - 1:
                time.sleep(0.02 * (attempt + 1))
    raise last_error


def create_job(job_type, payload):
    job_id = uuid.uuid4().hex
    os.makedirs(job_dir(job_id), exist_ok=True)
    _write_json_atomic(job_file(job_id, 'payload.json'), payload)
    update_status(
        job_id,
        status='pending',
        progress=0,
        message='任务等待执行',
        jobType=job_type,
    )
    return job_id


def read_payload(job_id):
    return _read_json_with_retry(job_file(job_id, 'payload.json'))


def update_status(job_id, **values):
    path = job_file(job_id, 'status.json')
    current = {}
    if os.path.exists(path):
        try:
            current = _read_json_with_retry(path)
        except (OSError, json.JSONDecodeError):
            current = {}
    current.update(values)
    current['jobId'] = job_id
    current['updatedAt'] = datetime.now().isoformat(timespec='seconds')
    _write_json_atomic(path, current)
    return current


def write_result(job_id, result):
    _write_json_atomic(job_file(job_id, 'result.json'), result)


def read_job(job_id):
    status_path = job_file(job_id, 'status.json')
    if not os.path.exists(status_path):
        raise FileNotFoundError('任务不存在')
    status = _read_json_with_retry(status_path)
    result_path = job_file(job_id, 'result.json')
    if status.get('status') == 'completed' and os.path.exists(result_path):
        status['result'] = _read_json_with_retry(result_path)
    return status
