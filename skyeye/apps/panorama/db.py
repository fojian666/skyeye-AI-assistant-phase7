# _*_ coding: utf-8 _*_
# @Time : 2025/4/21 13:51 
# @Author : xxx 
# @Version：V 0.1
# @File : db.py
# @desc :
from django.db import connection


def fetch_all_point_locations():
    """
    查询 t_point_location 表中的所有记录。
    :return: 查询结果列表，每个元素是一个字典，表示一行数据。
    """
    sql = "SELECT * FROM t_point_location where is_del=1;"
    return execute_query(sql)


def fetch_point_locations_by_grid_id(grid_id):
    """
    查询 t_point_location 表中的所有记录。
    :return: 查询结果列表，每个元素是一个字典，表示一行数据。
    """
    sql = "SELECT * FROM t_point_location where grid_id=%s and is_del=1;"
    return execute_query(sql, [grid_id])


def fetch_resource_by_batch_id(batch_id):
    """
    查询 t_resource 表中的记录。
    :return: 查询结果列表，每个元素是一个字典，表示一行数据。
    """
    sql = "SELECT r.* FROM t_resource r JOIN t_batch_resource br ON r.pk_id=br.resource_id where br.batch_id=%s and br.is_del=1;"
    return execute_query(sql, [batch_id])


def fetch_panorama_image_by_point_id(point_id, image_id):
    """
    根据全景点和当前全景图片获取上一个批次的全景图片
    Args:
        point_id:
        image_id:

    Returns:

    """
    sql = """
            SELECT *
            FROM t_panorama_image
            WHERE point_id = %s
              AND pk_id != %s
            ORDER BY create_date DESC
            LIMIT 1;
        """
    return execute_query(sql, [point_id, image_id], fetch_one=True)


def fetch_panorama_image_by_image_id(image_id):
    """
    根据全景编号查询 t_panorama_image 表中的记录。
    Args:
        image_id:

    Returns:

    """
    sql = "SELECT * FROM t_panorama_image WHERE pk_id = %s;"
    return execute_query(sql, [image_id], fetch_one=True)


def fetch_frame_area_by_point_id(point_id):
    """
    根据全景编号查询 t_point_location 表中的记录。
    :param point_id: 全景编号
    :return: 查询结果，单行数据为字典格式。
    """
    sql = "SELECT * FROM t_frame_area WHERE point_id = %s;"
    return execute_query(sql, [point_id])

def fetch_all_frame_area():
    """
    根据全景编号查询 t_point_location 表中的记录。
    :param point_id: 全景编号
    :return: 查询结果，单行数据为字典格式。
    """
    sql = "SELECT * FROM t_frame_area;"
    return execute_query(sql)
def fetch_point_location_by_id(point_id):
    """
    根据全景编号查询 t_point_location 表中的记录。
    :param point_id: 全景编号
    :return: 查询结果，单行数据为字典格式。
    """
    sql = "SELECT * FROM t_point_location WHERE pk_id = %s;"
    return execute_query(sql, [point_id], fetch_one=True)


def insert_point_location(point_id, point_name, grid_id, longitude, latitude, point_type):
    """
    插入一条新的全景点位记录。
    :param point_id: 全景编号
    :param point_name: 全景名称
    :param grid_id: 关联网格的 ID
    :param longitude: 经度
    :param latitude: 纬度
    :param point_type: 点位类型
    :return: None
    """
    sql = """
    INSERT INTO t_point_location (point_id, point_name, grid_id, longitude, latitude, point_type)
    VALUES (%s, %s, %s, %s, %s, %s);
    """
    execute_query(sql, [point_id, point_name, grid_id, longitude, latitude, point_type])


def fetch_clues_by_panorama_image_id(panorama_image_id):
    """
    根据全景编号查询 t_clue 表中的记录。
    Args:
        panorama_image_id: 全景图ID

    Returns:

    """
    sql = "SELECT * FROM t_clue WHERE panorama_image_id = %s;"
    return execute_query(sql, [panorama_image_id])


def update_batch_status(batch_id, status):
    """
    更新批次状态。
    @param batch_id:
    @param status:
    @return:
    """
    fields = []
    values = []

    if status is not None:
        fields.append("status = %s")
        values.append(status)

    if not fields:
        raise ValueError("No fields to update.")

    sql = f"UPDATE t_batch SET {', '.join(fields)} WHERE pk_id = %s;"
    values.append(batch_id)
    execute_query(sql, values)


def update_task_status(project_id, status):
    """
    更新任务状态。
    """
    sql = "UPDATE t_interpretation_task SET status = %s WHERE pk_id = %s;"
    execute_query(sql, [status, project_id])


def execute_query(sql, params=None, fetch_one=False):
    """
    执行原生 SQL 查询。
    :param sql: SQL 查询语句
    :param params: 参数列表（可选）
    :param fetch_one: 是否只获取一行数据
    :return: 查询结果
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        if sql.strip().lower().startswith("select"):
            columns = [col[0] for col in cursor.description]
            if fetch_one:
                row = cursor.fetchone()
                return dict(zip(columns, row)) if row else None
            else:
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
