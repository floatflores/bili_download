import sys, re
from downloader import Audio_Downloader

def validate_bv_id(bv_id):
    """
    验证B站视频ID是否有效。
    :param bv_id: 输入的B站视频ID
    :return: 如果有效则返回True，否则返回False
    """
    return bool(re.match(r"^BV\d+", bv_id))

def __main__():
    bv_ids = input("请输入要处理的BV号(多个请用空格分隔): ").strip().split()
    
    valid_bv_ids = [bv_id for bv_id in bv_ids if validate_bv_id(bv_id)]
    
    if not valid_bv_ids:
        print("检测到无效的BV号。")
        sys.exit(1)
    
    print(f"检测到{len(valid_bv_ids)}个有效的BV号: {', '.join(valid_bv_ids)}")
    
    download_choice = input("请选择操作: \n1. 下载音频 \n2. 下载视频 \n3. 下载视频并合并音频 \n(请输入数字): ").strip()
    
    if download_choice not in ['1', '2', '3']:
        print("无效选择。")
        sys.exit(1)
    
    for bv_id in valid_bv_ids:
        downloader = Audio_Downloader(bv_id)
        
        if download_choice == '1':
            downloader.run_download_audio()
        elif download_choice == '2':
            downloader.run_download_video()
        elif download_choice == '3':
            downloader.merge_video_audio()

if __name__ == "__main__":
    __main__()
