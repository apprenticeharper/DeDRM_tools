1.1 get AmazonSecureStorage.xml from /data/data/com.amazon.kindle/shared_prefs/AmazonSecureStorage.xml

1.2 on android 4.0+, run `adb backup com.amazon.kindle` from PC will get backup.ab
    now android.py can convert backup.ab to AmazonSecureStorage.xml

2. run `k4mobidedrm.py -a AmazonSecureStorage.xml <infile> <outdir>'
