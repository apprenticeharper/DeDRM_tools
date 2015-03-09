1.1 get AmazonSecureStorage.xml from /data/data/com.amazon.kindle/shared_prefs/AmazonSecureStorage.xml
    or map_data_storage.db from /data/data/com.amazon.kindle/databases/map_data_storage.db

1.2 on android 4.0+, run `adb backup com.amazon.kindle` from PC will get backup.ab
    now android.py can convert backup.ab to AmazonSecureStorage.xml and map_data_storage.db

2. run `k4mobidedrm.py <infile> <outdir>'
