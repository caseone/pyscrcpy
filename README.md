# pyscrcpy
# 1. 简介

简单的adb设备可视化管理，批量管理设备，可以调用scrcpy查看安卓画面

# 2. 用法

1. adb 和scrcpy加到环境变量
2. 直接打开应用（可以通过本地配置文件加载设备列表）
3. 右键选择设备adb connect、disconnect、scrcpy等操作
4. 默认配置文件`pyscrcpy.json`
   ``` json
   {
    "devices": [
        {
            "DeviceId": "127.0.0.1:5555",
            "Name": "备注1",
            "Status": "Unknown",
            "Order": 0
        },
        {
            "DeviceId": "127.0.0.3:5555",
            "Name": "备注2",
            "Status": "Unknown",
            "Order": 0
        }
    ],
    "scrcpyOptions": ""
   }
   ```

# 3. 打包

可打包成二进制文件，直接使用

``` bash 
python -m PyInstaller --onefile  --noconsole --windowed --icon=pyscrcpy.jpg pyscrcpy.py
```

