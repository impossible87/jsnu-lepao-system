import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import math

# --- 跑步活动参数 ---
start_time = datetime(2023, 3, 8, 12, 15, 4)  # 起始时间
total_laps = 5                                  # 总圈数
single_lap_distance = 400.0                     # 单圈距离
distance_meters = single_lap_distance * total_laps # 总距离 (2000.0)

# 假设每圈配速与之前一致 (800秒/400米)
time_per_lap_seconds = 200
total_time_seconds = time_per_lap_seconds * total_laps # 总时间 (4000)

# 按比例增加点数以保持轨迹平滑度
points_per_lap = 100
n_points = points_per_lap * total_laps          # 总轨迹点个数 (500)

# --- 椭圆跑道几何参数 (与单圈相同) ---
straight_length = 100.0                         # 直道长度 (米)
curve_length = 100.0                            # 半圆弯道弧长 (米)
total_length_check = 2 * straight_length + 2 * curve_length
if not math.isclose(total_length_check, single_lap_distance):
    print(f"Warning: Defined segment lengths ({total_length_check}m) do not sum to single lap distance ({single_lap_distance}m).")

radius_meters = curve_length / math.pi         # 弯道半径

# --- GPS 中心坐标和转换因子 (与单圈相同) ---
center_lat = 34.197550
center_lon = 117.173188

meter_to_deg_lat = 1 / 111111.0
meter_to_deg_lon = 1 / (111111.0 * math.cos(math.radians(center_lat)))

# --- 计算跑道关键点几何位置 (与单圈相同) ---
lon_offset_deg = radius_meters * meter_to_deg_lon
lat_offset_deg = (straight_length / 2.0) * meter_to_deg_lat

north_curve_center_lat = center_lat + lat_offset_deg
south_curve_center_lat = center_lat - lat_offset_deg
curve_center_lon = center_lon

# --- 创建 TCX 文件结构 ---
root = ET.Element("TrainingCenterDatabase", xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2",
                   **{"xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                      "xsi:schemaLocation": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd"})
activities = ET.SubElement(root, "Activities")
activity = ET.SubElement(activities, "Activity", Sport="Running")
id_elem = ET.SubElement(activity, "Id")
id_elem.text = start_time.isoformat() + "Z"

# 创建一个覆盖整个活动的 Lap
lap = ET.SubElement(activity, "Lap", StartTime=start_time.isoformat() + "Z")
total_time_elem = ET.SubElement(lap, "TotalTimeSeconds")
total_time_elem.text = str(float(total_time_seconds)) # 使用总时间
distance_elem = ET.SubElement(lap, "DistanceMeters")
distance_elem.text = str(distance_meters) # 使用总距离
intensity = ET.SubElement(lap, "Intensity")
intensity.text = "Active"
trigger_method = ET.SubElement(lap, "TriggerMethod")
trigger_method.text = "Manual" # 或者 'Distance' if lap splits were desired
track = ET.SubElement(lap, "Track")

# --- 生成轨迹点 ---
dt = total_time_seconds / n_points # 每个点的时间间隔

# 定义单圈内各段的累积距离
dist_straight1_end = straight_length
dist_curve1_end = straight_length + curve_length
dist_straight2_end = straight_length + curve_length + straight_length
dist_curve2_end = single_lap_distance # 单圈结束距离

# 起点坐标 (用于闭合和参考)
start_lat_coord = south_curve_center_lat
start_lon_coord = center_lon - lon_offset_deg

for i in range(n_points + 1): # n_points+1 个点，覆盖 0 到 n_points
    # 计算当前点的总累积距离
    current_total_dist = distance_meters * i / n_points
    # 确保最后一个点的距离精确为总距离
    if i == n_points:
        current_total_dist = distance_meters

    # 计算当前点的时间
    point_time = start_time + timedelta(seconds=dt * i)

    # --- 计算当前点在单圈内的相对距离 ---
    if math.isclose(current_total_dist, 0.0):
        dist_in_current_lap = 0.0
    # 如果总距离是 400 的倍数 (但不是0)，则圈内距离视为 400，用于几何定位在起点
    elif math.isclose(current_total_dist % single_lap_distance, 0.0) and current_total_dist > 0:
        dist_in_current_lap = single_lap_distance
    else:
        dist_in_current_lap = current_total_dist % single_lap_distance

    # --- 根据 dist_in_current_lap 计算 GPS 坐标 ---
    lat = 0.0
    lon = 0.0

    # 根据当前圈内距离判断在跑道的哪个部分
    if 0 <= dist_in_current_lap < dist_straight1_end:
        # 第一段：西侧直道 (向北)
        # 处理起点特殊情况 (dist_in_current_lap == 0)
        if math.isclose(dist_in_current_lap, 0.0):
            progress = 0.0
        else:
            progress = dist_in_current_lap / straight_length
        lat = start_lat_coord + progress * (north_curve_center_lat - south_curve_center_lat)
        lon = start_lon_coord

    elif dist_straight1_end <= dist_in_current_lap < dist_curve1_end:
        # 第二段：北侧弯道 (向东)
        dist_on_curve = dist_in_current_lap - dist_straight1_end
        angle_rad = (dist_on_curve / curve_length) * math.pi
        current_angle = math.pi - angle_rad
        lat = north_curve_center_lat + (radius_meters * meter_to_deg_lat) * math.sin(current_angle)
        lon = curve_center_lon + (radius_meters * meter_to_deg_lon) * math.cos(current_angle)

    elif dist_curve1_end <= dist_in_current_lap < dist_straight2_end:
        # 第三段：东侧直道 (向南)
        dist_on_straight = dist_in_current_lap - dist_curve1_end
        progress = dist_on_straight / straight_length
        lat = north_curve_center_lat - progress * (north_curve_center_lat - south_curve_center_lat)
        lon = center_lon + lon_offset_deg # 东侧经度

    elif dist_straight2_end <= dist_in_current_lap <= dist_curve2_end: # 包含单圈终点
        # 第四段：南侧弯道 (向西) - 修正后
        dist_on_curve = dist_in_current_lap - dist_straight2_end
        dist_on_curve = max(0.0, min(dist_on_curve, curve_length)) # 防超出
        angle_rad = (dist_on_curve / curve_length) * math.pi
        current_angle = 2 * math.pi - angle_rad
        lat = south_curve_center_lat + (radius_meters * meter_to_deg_lat) * math.sin(current_angle)
        lon = curve_center_lon + (radius_meters * meter_to_deg_lon) * math.cos(current_angle)

        # 如果正好是单圈结束点 (400m, 800m, ... 2000m), 强制坐标回到起点
        if math.isclose(dist_in_current_lap, single_lap_distance):
             lat = start_lat_coord
             lon = start_lon_coord
    else:
         # 理论上不应到达，除非 dist_in_current_lap 计算错误
         print(f"Warning: dist_in_current_lap {dist_in_current_lap} unexpected for total_dist {current_total_dist}.")
         lat = start_lat_coord # Default to start
         lon = start_lon_coord


    # --- 创建 Trackpoint 节点 ---
    trackpoint = ET.SubElement(track, "Trackpoint")
    time_elem = ET.SubElement(trackpoint, "Time")
    time_elem.text = point_time.isoformat() + "Z"

    position = ET.SubElement(trackpoint, "Position")
    lat_elem = ET.SubElement(position, "LatitudeDegrees")
    lat_elem.text = f"{lat:.8f}"
    lon_elem = ET.SubElement(position, "LongitudeDegrees")
    lon_elem.text = f"{lon:.8f}"

    distance_tp = ET.SubElement(trackpoint, "DistanceMeters")
    # 关键：写入的是总累积距离
    distance_tp.text = f"{current_total_dist:.2f}"

    # 添加心率 (可选)
    hr = ET.SubElement(trackpoint, "HeartRateBpm")
    hr_val = ET.SubElement(hr, "Value")
    # 可以让心率稍微变化，例如模拟跑步过程
    current_hr = 110 + int(40 * (current_total_dist / distance_meters)) # 简单线性增加示例
    hr_val.text = str(current_hr)

# --- 写入文件 ---
tree = ET.ElementTree(root)
# 注意修改输出文件名
tree.write("output_oval_2km.tcx", encoding="UTF-8", xml_declaration=True)

print("Oval track TCX file 'output_oval_2km.tcx' (2km / 5 laps) generated successfully.")
