import cv2
import os
import time
import shutil
from termcolor import colored

# 定义ASCII字符集，用于灰度图转换
ASCII_CHARS = ['@', '#', 'S', '%', '?', '*', '+', ';', ':', ',', '.']

def create_output_folder(video_path):
    """创建保存灰度图的输出文件夹"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    folder_name = f"{video_name}_gary"
    output_folder = os.path.join(script_dir, folder_name)
    
    # 如果文件夹已存在，则删除重建
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder)
    
    return output_folder

def video_to_grayscale_frames(video_path, output_folder):
    """将视频转换为灰度图帧并保存"""
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("Error: 无法打开视频文件")
        return False
    
    # 获取视频的原始帧率
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"视频原始帧率: {original_fps:.2f} FPS")
    
    # 计算采样间隔（每多少帧取一帧）

    sample_interval = max(1, original_fps / 24)

    target_fps = 24
    time_interval = 1 / target_fps
    
    frame_count = 0
    saved_count = 0
    timestamps = []  # 保存每帧的时间戳（秒）
    
    print("正在转换为灰度图...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 当前帧的时间戳（秒）
        timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
        
        # 按时间间隔采样
        if frame_count == 0 or timestamp >= saved_count * time_interval:
            # 转换为灰度图
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 保存灰度图和时间戳
            frame_path = os.path.join(output_folder, f"frame_{saved_count:04d}.jpg")
            cv2.imwrite(frame_path, gray_frame)
            timestamps.append(timestamp)
            saved_count += 1
        
        frame_count += 1
    
    cap.release()
    print(f"成功从 {frame_count} 帧中保存 {saved_count} 帧灰度图到 {output_folder}")
    
    # 保存时间戳到文件
    timestamp_path = os.path.join(output_folder, "timestamps.txt")
    with open(timestamp_path, 'w') as f:
        f.write('\n'.join(map(str, timestamps)))
    
    return saved_count, original_fps

def resize_frame(frame):
    """智能调整帧大小，平衡横向和纵向分辨率"""
    try:
        # 获取终端尺寸
        terminal_size = shutil.get_terminal_size(fallback=(80, 24))
        term_width = terminal_size.columns 
        term_height = terminal_size.lines 
    except (OSError, ValueError):
        term_width = 150
        term_height = 40  # 默认终端高度
    
    # 计算帧的原始宽高比
    height, width = frame.shape
    frame_ratio = width / height
    

    term_ratio = term_width / (term_height)
    
    if frame_ratio > term_ratio:
        # 视频更宽: 以宽度为基准
        new_width = term_width
        new_height = int(new_width / frame_ratio)
    else:
        # 视频更高: 以高度为基准
        new_height = term_height
        new_width = int((new_height ) * frame_ratio)
    
    # 调整帧大小
    resized_frame = cv2.resize(frame, (new_width*2, new_height))
    return resized_frame

def pixel_to_ascii(pixel):
    """将像素值转换为对应的ASCII字符"""
    normalized_pixel = pixel / 255
    index = int(normalized_pixel * (len(ASCII_CHARS) - 1))
    return ASCII_CHARS[index]

def frame_to_ascii(frame):
    """将整个帧转换为ASCII字符"""
    ascii_frame = []
    for row in frame:
        ascii_row = ''.join([pixel_to_ascii(pixel) for pixel in row])
        ascii_frame.append(ascii_row)
    return '\n'.join(ascii_frame)

def play_ascii_video(frames_folder, frame_count, original_fps):
    """根据原始帧率精确控制播放速度"""
    # 读取时间戳
    timestamp_path = os.path.join(frames_folder, "timestamps.txt")
    try:
        with open(timestamp_path, 'r') as f:
            timestamps = [float(line.strip()) for line in f.readlines()]
    except FileNotFoundError:
        print("error: 未找到时间戳文件，使用固定帧率播放")
        timestamps = [i / 24 for i in range(frame_count)]
    
    start_time = time.perf_counter()  # 记录播放开始时间
    frame_index = 0
    
    try:
        while frame_index < frame_count:
            # 读取灰度图
            frame_path = os.path.join(frames_folder, f"frame_{frame_index:04d}.jpg")
            frame = cv2.imread(frame_path, cv2.IMREAD_GRAYSCALE)
            
            if frame is None:
                print(f"Error: 无法读取帧 {frame_path}")
                frame_index += 1
                continue
            
            # 调整大小并转换为ASCII
            resized_frame = resize_frame(frame)
            ascii_frame = frame_to_ascii(resized_frame)
            
            # 清屏并显示当前帧
            os.system('cls' if os.name == 'nt' else 'clear')
            print(colored(ascii_frame, 'white'))
            
            # 计算当前帧应该显示的时间点
            target_display_time = start_time + timestamps[frame_index]
            
            # 等待直到该显示这一帧的时间点
            current_time = time.perf_counter()
            if current_time < target_display_time:
                time.sleep(target_display_time - current_time)
            
            frame_index += 1
            
    except KeyboardInterrupt:
        print("\n播放已停止")

def main():
    print("made by LLGLang")
    print("最大化终端获得最佳体验~")
    video_path = input("请输入视频文件路径(或将视频拖入终端): ")
    if not os.path.exists(video_path):
        print("Error: 文件不存在")
        return

    output_folder = create_output_folder(video_path)
    frame_count, original_fps = video_to_grayscale_frames(video_path, output_folder)

    if frame_count > 0:
        print("5秒后播放ASCII视频...")
        print("按 Ctrl+C 停止播放")
        time.sleep(5)
        play_ascii_video(output_folder, frame_count, original_fps)

        # 删除存放灰度图的文件夹
        shutil.rmtree(output_folder)

        main()


if __name__ == "__main__":
    main()