import os
import zipfile

def unzip_file(zip_save_path, unzip_dir_path):
    """
    解压zip文件：解决编码问题
    """
    r = zipfile.is_zipfile(zip_save_path)
    if r:
        try:
            with zipfile.ZipFile(file=zip_save_path, mode='r') as zf:
                # 解压到指定⽬录,⾸先创建⼀个解压⽬录
                if os.path.exists(unzip_dir_path) is False:
                    os.mkdir(unzip_dir_path)
                for old_name in zf.namelist():
                    # 获取⽂件⼤⼩，⽬的是区分⽂件夹还是⽂件，如果是空⽂件应该不好⽤。
                    file_size = zf.getinfo(old_name).file_size
                    # 由于源码遇到中⽂是cp437⽅式，所以解码成gbk，windows即可正常
                    new_name = old_name.encode('cp437').decode('gbk')
                    # 拼接⽂件的保存路径
                    new_path = os.path.join(unzip_dir_path, new_name)
                    # 判断⽂件是⽂件夹还是⽂件
                    if file_size > 0:
                        # 是⽂件，通过open创建⽂件，写⼊数据
                        with open(file=new_path, mode='wb') as f:
                            # zf.read 是读取压缩包⾥的⽂件内容
                            f.write(zf.read(old_name))
                    else:
                        # 是⽂件夹，就创建
                        os.mkdir(new_path)
        except:
            fz = zipfile.ZipFile(zip_save_path, 'r')
            fz.extractall(unzip_dir_path)
        return True
    else:
        print('This is not zip')
        return False
