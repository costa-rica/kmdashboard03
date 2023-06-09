import os
from km03_config import ConfigLocal, ConfigDev, ConfigProd

if os.environ.get('CONFIG_TYPE')=='local':
    config = ConfigLocal()
    print('- kmDashboard03/app_pacakge/config: Local')
elif os.environ.get('CONFIG_TYPE')=='dev':
    config = ConfigDev()
    print('- kmDashboard03/app_pacakge/config: Development')
elif os.environ.get('CONFIG_TYPE')=='prod':
    config = ConfigProd()
    print('- kmDashboard03/app_pacakge/config: Production')

print(f"webpackage location: {os.environ.get('WEB_ROOT')}")
print(f"config location: {os.path.join(os.environ.get('CONFIG_PATH'),os.environ.get('CONFIG_FILE_NAME')) }")