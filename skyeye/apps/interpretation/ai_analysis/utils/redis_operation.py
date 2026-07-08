import json
import redis
# import django
# from django.conf import settings
import apps.interpretation.ai_config as cg
host = cg.REDISIP
redis_client = redis.Redis(host=host, port=6379, db=cg.AI_DB)
def query_thekey_tasks():

    # 获取所有任务键
    task_keys = redis_client.keys('*')
    print(task_keys)
    # 遍历每个任务队列键，获取任务数量
    for queue in task_keys:
        print("*"*40)
        key_type = redis_client.type(queue.decode())  # 将 bytes 类型解码为字符串
        print(queue,key_type)
        if key_type == b'list':
            task_count = redis_client.llen(queue)
            print(f"队列 {queue.decode()} 的任务数量为: {task_count}")
            # 使用 LRANGE 获取列表中的所有任务信息
            # 从索引 0 开始，-1 表示获取所有元素
            tasks = redis_client.lrange(queue, 0, -1)
            if queue.decode().split(":")[0] == "project":
                # 遍历任务列表
                for task_json in tasks:
                    # 假设每个任务是一个 JSON 序列化的字符串，需要解码和反序列化为字典
                    task_info = json.loads(task_json.decode('utf-8'))
                    # 打印并处理每个任务信息
                    print(f"任务 ID: {task_info['task_id']}")
                    # 可以添加更多处理逻辑
                    print("-" * 40)  # 打印分隔线以便区分不同任务的信息
            if  queue.decode() == "celery":
                # 打印任务
                for task in tasks:
                    print(task)
                    print("+" * 40)  # 打印分隔线以便区分不同任务的信息
        elif key_type == b'set':
            task_count = redis_client.scard(queue)
            # print(f"集合 {queue.decode()} 的元素数量为: {task_count}")
        else:
            print(f"键 {queue.decode()} 的类型不是列表或集合，类型为: {key_type}")

def empty_record():
    # 要移除特定 task_id 的键
    redis_key = 'celery'

    # 从列表中获取所有任务信息
    task_jsons = redis_client.lrange(redis_key, 0, -1)

    # 过滤掉 task_id 为 1 的记录
    new_task_jsons = [task_json for task_json in task_jsons if json.loads(task_json.decode()).get('task_id') != '36e7c3dd2d5211efad0308bfb870f86f']

    # 将剩余的任务信息重新写入列表
    # 这里使用 LRANGE 清空列表，然后使用 RPUSHX 写入剩余的任务信息
    redis_client.delete(redis_key)  # 清空列表
    for task_json in new_task_jsons:
        redis_client.rpush(redis_key, task_json)
    print(f"移除了键 {redis_key} 中 task_id 为 1 的记录。")
    print("剩余任务数量为：{}".format(redis_client.llen(redis_key)))


def celeryrecord():
    """
    只查一个队列中的任务
    Returns:

    """
    # 假设您的 Celery 任务队列名称是 'celery'
    queue_name = 'celery'
    # 使用 LRANGE 命令查看队列中的前 10 个任务
    tasks = redis_client.lrange(queue_name, 0, -1)
    count = len(tasks)
    print(len(tasks))
    # 打印任务
    taskid_list = []
    for task in tasks:
        task_data = json.loads(task.decode())
        task_id = task_data['properties'].get('correlation_id')
        taskid_list.append(task_id)
    print(taskid_list)
    return count,taskid_list

def delete_one_record(task_id):
    """"
    删除指定task_id的任务
    """
    # 要删除的任务的 correlation_id  其实就是task_id
    correlation_id_to_delete = task_id
    # 队列名称，通常是以 'celery' 开头的，加上您的项目名和队列名
    queue_name = 'celery'
    # 从队列中检索所有任务
    tasks = redis_client.lrange(queue_name, 0, -1)
    is_exitstask = False
    # 找到具有特定 correlation_id 的任务索引
    for index, task in enumerate(tasks):
        # if json.loads(task.decode())['properties']['correlation_id'] == correlation_id_to_delete:
        if json.loads(task.decode())['properties'].get('options') == correlation_id_to_delete:
            # 使用 LREM 命令删除任务
            redis_client.lrem(queue_name, 1, task)
            is_exitstask = True
            return True,f"任务 {correlation_id_to_delete} 已被删除"
            # break  # 假设只有一个任务具有该 correlation_id，找到后退出循环
    if not is_exitstask:
        return False,"没有找到要删除的任务。"

def delete_sameproject_tasks(queue_name, options_to_delete):
    """
    删除同一个项目下的所有任务
    Args:
        queue_name:
        options_to_delete:
    Returns:
    """
    # 从队列中检索所有任务
    tasks = redis_client.lrange(queue_name, 0, -1)
    # 如果找到了要删除的任务，使用 LREM 命令删除它们
    # if len(tasks) != len(new_tasks):
    for task in tasks:
        task_data = json.loads(task.decode())
        if task_data['properties'].get('options') == options_to_delete:
            # LREM 命令从列表中移除第一个匹配的元素
            redis_client.lrem(queue_name, 1, task)
        print(f"具有 options 值 {options_to_delete} 的任务已被删除。")

