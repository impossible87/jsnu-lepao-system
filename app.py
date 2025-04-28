from flask import Flask, render_template, request, send_file, jsonify
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import math
import random
import os
import zipfile
import io
import calendar

app = Flask(__name__)

def generate_tcx(start_time, total_laps=None, single_lap_distance=400.0):
    # 随机生成总圈数（5-6圈之间的小数）
    if total_laps is None:
        total_laps = round(random.uniform(5, 6), 2)  # 在5-6之间随机生成小数，保留两位
        total_distance = round(total_laps * single_lap_distance, 2)  # 计算总距离并保留两位小数
    else:
        total_distance = total_laps * single_lap_distance
    
    # 随机生成每圈配速
    time_per_lap_seconds = random.randint(120, 200)
    total_time_seconds = time_per_lap_seconds * total_laps
    
    # 其他参数保持不变
    points_per_lap = 100
    n_points = int(points_per_lap * total_laps)  # 转换为整数
    straight_length = 100.0
    curve_length = 100.0
    radius_meters = curve_length / math.pi
    
    # GPS中心坐标保持不变
    center_lat = 34.197550
    center_lon = 117.173188
    
    meter_to_deg_lat = 1 / 111111.0
    meter_to_deg_lon = 1 / (111111.0 * math.cos(math.radians(center_lat)))
    
    # 计算跑道关键点几何位置
    lon_offset_deg = radius_meters * meter_to_deg_lon
    lat_offset_deg = (straight_length / 2.0) * meter_to_deg_lat
    
    north_curve_center_lat = center_lat + lat_offset_deg
    south_curve_center_lat = center_lat - lat_offset_deg
    curve_center_lon = center_lon
    
    # 创建TCX文件结构
    root = ET.Element("TrainingCenterDatabase", 
                     xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2",
                     **{"xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                        "xsi:schemaLocation": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd"})
    
    activities = ET.SubElement(root, "Activities")
    activity = ET.SubElement(activities, "Activity", Sport="Running")
    id_elem = ET.SubElement(activity, "Id")
    id_elem.text = start_time.isoformat()
    
    lap = ET.SubElement(activity, "Lap", StartTime=start_time.isoformat())
    total_time_elem = ET.SubElement(lap, "TotalTimeSeconds")
    total_time_elem.text = str(float(total_time_seconds))
    distance_elem = ET.SubElement(lap, "DistanceMeters")
    distance_elem.text = str(total_distance)  # 使用计算出的总距离
    intensity = ET.SubElement(lap, "Intensity")
    intensity.text = "Active"
    trigger_method = ET.SubElement(lap, "TriggerMethod")
    trigger_method.text = "Manual"
    track = ET.SubElement(lap, "Track")
    
    # 生成轨迹点
    dt = total_time_seconds / n_points
    
    # 定义单圈内各段的累积距离
    dist_straight1_end = straight_length
    dist_curve1_end = straight_length + curve_length
    dist_straight2_end = straight_length + curve_length + straight_length
    dist_curve2_end = single_lap_distance
    
    # 起点坐标
    start_lat_coord = south_curve_center_lat
    start_lon_coord = center_lon - lon_offset_deg
    
    # 生成非线性心率数据
    hr_values = []
    for i in range(n_points + 1):
        x = i / n_points
        hr = 75 + int(45 * (1 - math.cos(x * math.pi))) + random.randint(-5, 5)
        hr = max(75, min(120, hr))
        hr_values.append(hr)
    
    # 生成轨迹点
    for i in range(n_points + 1):
        current_total_dist = total_distance * i / n_points
        if i == n_points:
            current_total_dist = total_distance
        
        point_time = start_time + timedelta(seconds=dt * i)
        
        # 计算当前点在单圈内的相对距离
        if math.isclose(current_total_dist, 0.0):
            dist_in_current_lap = 0.0
        elif math.isclose(current_total_dist % single_lap_distance, 0.0) and current_total_dist > 0:
            dist_in_current_lap = single_lap_distance
        else:
            dist_in_current_lap = current_total_dist % single_lap_distance
        
        # 根据dist_in_current_lap计算GPS坐标
        lat = 0.0
        lon = 0.0
        
        if 0 <= dist_in_current_lap < dist_straight1_end:
            # 第一段：西侧直道 (向北)
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
            lon = center_lon + lon_offset_deg
        
        elif dist_straight2_end <= dist_in_current_lap <= dist_curve2_end:
            # 第四段：南侧弯道 (向西)
            dist_on_curve = dist_in_current_lap - dist_straight2_end
            dist_on_curve = max(0.0, min(dist_on_curve, curve_length))
            angle_rad = (dist_on_curve / curve_length) * math.pi
            current_angle = 2 * math.pi - angle_rad
            lat = south_curve_center_lat + (radius_meters * meter_to_deg_lat) * math.sin(current_angle)
            lon = curve_center_lon + (radius_meters * meter_to_deg_lon) * math.cos(current_angle)
            
            if math.isclose(dist_in_current_lap, single_lap_distance):
                lat = start_lat_coord
                lon = start_lon_coord
        
        # 创建Trackpoint节点
        trackpoint = ET.SubElement(track, "Trackpoint")
        time_elem = ET.SubElement(trackpoint, "Time")
        time_elem.text = point_time.isoformat()
        
        position = ET.SubElement(trackpoint, "Position")
        lat_elem = ET.SubElement(position, "LatitudeDegrees")
        lat_elem.text = f"{lat:.8f}"
        lon_elem = ET.SubElement(position, "LongitudeDegrees")
        lon_elem.text = f"{lon:.8f}"
        
        distance_tp = ET.SubElement(trackpoint, "DistanceMeters")
        distance_tp.text = f"{current_total_dist:.2f}"  # 保留两位小数
        
        hr = ET.SubElement(trackpoint, "HeartRateBpm")
        hr_val = ET.SubElement(hr, "Value")
        hr_val.text = str(hr_values[i])
    
    return ET.ElementTree(root)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        start_times = []
        
        for time_data in data['times']:
            # 验证输入数据
            year = int(time_data['year'])
            month = int(time_data['month'])
            day = int(time_data['day'])
            hour = int(time_data['hour'])
            minute = int(time_data['minute'])
            second = int(time_data['second'])
            
            # 验证时间范围
            if not (2000 <= year <= 2100):
                raise ValueError("年份必须在2000-2100之间")
            if not (1 <= month <= 12):
                raise ValueError("月份必须在1-12之间")
            if not (1 <= day <= 31):
                raise ValueError("日期必须在1-31之间")
            if not (0 <= hour <= 23):
                raise ValueError("小时必须在0-23之间")
            if not (0 <= minute <= 59):
                raise ValueError("分钟必须在0-59之间")
            if not (0 <= second <= 59):
                raise ValueError("秒数必须在0-59之间")
            
            # 验证具体月份的天数
            last_day = calendar.monthrange(year, month)[1]
            if day > last_day:
                raise ValueError(f"{year}年{month}月只有{last_day}天")
            
            start_time = datetime(year, month, day, hour, minute, second)
            start_times.append(start_time)
        
        if len(start_times) == 1:
            # 单个文件
            tree = generate_tcx(start_times[0])
            output = io.BytesIO()
            tree.write(output, encoding="UTF-8", xml_declaration=True)
            output.seek(0)
            return send_file(
                output,
                mimetype='application/xml',
                as_attachment=True,
                download_name=f"run_{start_times[0].strftime('%Y%m%d_%H%M%S')}.tcx"
            )
        else:
            # 多个文件打包
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for start_time in start_times:
                    tree = generate_tcx(start_time)
                    output = io.BytesIO()
                    tree.write(output, encoding="UTF-8", xml_declaration=True)
                    output.seek(0)
                    zip_file.writestr(
                        f"run_{start_time.strftime('%Y%m%d_%H%M%S')}.tcx",
                        output.getvalue()
                    )
            
            zip_buffer.seek(0)
            return send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name='runs.zip'
            )
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': '生成文件时出错'}), 500

if __name__ == '__main__':
    import sys
    import os
    import webbrowser
    import threading
