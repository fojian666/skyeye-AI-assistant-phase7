import geopandas as gpd
import pandas as pd
from shapely import Point
import numpy as np


# ===================== 核心辅助函数：转换bytes为中文字符串 =====================
def convert_bytes_to_str(gdf, encoding="gbk"):
    """
    遍历GeoDataFrame，将所有bytes/np.bytes_类型的字段转为中文字符串
    :param gdf: 待处理的GeoDataFrame
    :param encoding: 编码格式（中文SHP优先用gbk，其次utf-8）
    :return: 处理后的GeoDataFrame
    """
    for col in gdf.columns:
        if col == "geometry":  # 跳过几何列
            continue
        # 处理普通bytes类型
        gdf[col] = gdf[col].apply(
            lambda x: x.decode(encoding) if isinstance(x, bytes) else x
        )
        # 处理numpy的bytes类型（np.bytes_）
        gdf[col] = gdf[col].apply(
            lambda x: x.decode(encoding) if isinstance(x, np.bytes_) else x
        )
    return gdf


# ===================== 1. 配置文件路径 =====================
scenic_shp_path = r"E:\04data\XZQQJD\xzqqjd.shp"  # 点SHP文件路径
xzqh_shp_path = r"E:\04data\新站区数据\界线\街道界线.shp"  # 面SHP文件路径
output_shp_path = "XZQQJD.shp"  # 输出文件路径

# 第一步：读取景点数据（中文SHP优先用gbk编码读取）
df_scenic = gpd.read_file(scenic_shp_path, encoding="gbk")
# 检查经纬度字段（改为ZXDX/ZXDY，和你的代码一致）
if "ZXDX" not in df_scenic.columns or "ZXDY" not in df_scenic.columns:
    raise KeyError("景点数据缺少ZXDX（经度）或ZXDY（纬度）字段")

# 第二步：转换bytes字段为中文字符串
df_scenic = convert_bytes_to_str(df_scenic, encoding="gbk")

# 第三步：从ZXDX/ZXDY构建Point几何对象（WGS84）
# 注意：确认ZXDX是经度、ZXDY是纬度，若匹配失败可交换顺序（Point(row["ZXDY"], row["ZXDX"])）
df_scenic["geometry"] = df_scenic.apply(
    lambda row: Point(row["ZXDX"], row["ZXDY"]), axis=1
)

# 第四步：转为GeoDataFrame，指定坐标系为WGS84
gdf_scenic = gpd.GeoDataFrame(
    df_scenic,
    geometry="geometry",
    crs="EPSG:4326"
)

# ===================== 3. 读取行政区划数据 =====================
# 第一步：读取行政区划SHP
gdf_xzqh = gpd.read_file(xzqh_shp_path, encoding="gbk")

# 【关键】先打印行政区划所有字段，确认实际字段名（避免字段名写错）
print("行政区划SHP的所有字段：", gdf_xzqh.columns.tolist())
if gdf_xzqh.crs != "EPSG:4326":
    print("⚠️  行政区划坐标系非WGS84，已自动转换")
    gdf_xzqh = gdf_xzqh.to_crs("EPSG:4326")
# 检查行政区划的核心字段（根据实际字段名修改！比如原字段是XZQMC/XZQDM，就写这两个）
# 如果你想把行政区划的【XXX字段】赋值给点位的WGNAME，【YYY字段】赋值给JDID，就改这里
required_fields = ["WGNAME", "JDID"]  # 替换为你实际的字段名（比如["XZQMC","XZQDM"]）
missing_fields = [f for f in required_fields if f not in gdf_xzqh.columns]
if missing_fields:
    raise KeyError(f"行政区划数据缺少字段：{missing_fields}，实际字段：{gdf_xzqh.columns.tolist()}")

# 第二步：转换bytes类型的字段为中文字符串
gdf_xzqh = convert_bytes_to_str(gdf_xzqh, encoding="gbk")


print("✅ 数据读取&几何构建成功")
print(f"景点点位数量：{len(gdf_scenic)}")
print(f"行政区划面数量：{len(gdf_xzqh)}")

# 验证行政区划字段值是否正常
print("\n行政区划名称&编码示例：")
print(gdf_xzqh[required_fields].head(5).to_string())

# ===================== 4. 空间匹配：点在面内 =====================
# 保留geometry+核心字段（WGNAME/JDID）
gdf_joined = gpd.sjoin(
    gdf_scenic,
    gdf_xzqh[["geometry"] + required_fields],  # 动态保留需要的字段
    how="left",
    predicate="within"
)

# ===================== 5. 字段赋值（核心修正） =====================
# 1. JDNAME：等于行政区划的WGNAME，未匹配填"未匹配"
gdf_joined["JDNAME"] = gdf_joined["WGNAME"].fillna("未匹配").astype(str)
# 2. WGNAME：直接复用行政区划的WGNAME（不覆盖，未匹配填"未匹配"）
gdf_joined["WGNAME"] = gdf_joined["JDNAME"].fillna("未匹配").astype(str)
# 3. JDID：等于行政区划的JDID，未匹配填空字符串
gdf_joined["JDID"] = gdf_joined["JDID"].fillna("").astype(str)

# ===================== 6. 清理冗余字段 =====================
# 只删除sjoin自动生成的index_right，保留WGNAME/JDID/JDNAME
gdf_result = gdf_joined.drop(columns=["index_right"], errors="ignore")

# 最终兜底：转换bytes字段+处理空值
gdf_result = convert_bytes_to_str(gdf_result, encoding="gbk")
gdf_result = gdf_result.fillna("")

# ===================== 7. 保存结果 =====================
gdf_result.to_file(output_shp_path, encoding="gbk", driver="ESRI Shapefile")
print(f"\n✅ 处理完成！结果保存至：{output_shp_path}")
print(f"匹配成功的点位：{len(gdf_result[gdf_result['JDNAME'] != '未匹配'])}")
print(f"未匹配的点位：{len(gdf_result[gdf_result['JDNAME'] == '未匹配'])}")

# 验证最终字段
print("\n最终输出的字段：", gdf_result.columns.tolist())
print("\n新增字段示例：")
print(gdf_result[["JDNAME", "WGNAME", "JDID"]].head(10).to_string())

