import os


def read_file(file_path):
    """
    读取文件内容。
    参数:
        file_path (str): 要读取的文件路径。
    返回:
        file_data: 读取的原始数据（按行列表）。
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.readlines()


def process_file(file_data):
    """
    处理文件数据。
    参数:
        file_data: 读取的原始数据（按行列表）。
    返回:
        result: 处理后的平均值。
    """
    import re
    started = False
    total = 0.0
    count = 0
    pattern = re.compile(r'当前音量: ([\d.]+)')
    for line in file_data:
        if not started:
            if '当前音量' in line:
                started = True
        if started:
            match = pattern.search(line)
            if match:
                value = float(match.group(1))
                total += value
                count += 1
    if count == 0:
        return None
    return total / count

if __name__ == "__main__":

    file_path = "volume_data.txt"
    file_path = os.path.abspath(file_path)
    try:
        file_data = read_file(file_path)
        result = process_file(file_data)
        if result is not None:
            print(f"平均音量: {result:.2f}")
        else:
            print("没有找到有效的音量数据。")
    except Exception as e:
        print(f"处理文件时发生错误: {e}")