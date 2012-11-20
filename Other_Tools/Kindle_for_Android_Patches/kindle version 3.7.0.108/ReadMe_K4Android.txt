Kindle for Android
------------------

Kindle for Android uses a different scheme to generate its books specific PIDs than Kindle for PC, Kindle for iPhone/iPad, and standalone Kindles.

Unfortunately, K4Android uses an "account secrets" file that would only be available if the device were jail-broken and even then someone would have to figure out how to decode this secret information in order to reverse the process.

Instead of trying to calculate the correct PIDs for each book from this primary data, "Me" (a commenter who posted to the ApprenticeAlf site)  came up with a wonderful idea to simply modify the Kindle 3 for Android application to store the PIDs it uses to decode each book in its "about activity" window.  This list of PIDS can then be provided to MobiDeDRM.py,  which in its latest incarnations allows a comma separated list of pids to be passed in, to successfully remove the DRM from that book.   Effectively "Me" has created an "Unswindle" for the Kindle for Android 3 application!

"Me"'s original patch was for Kindle for Android version 3.0.1.70. Now "Me II" has created a patch for Kindle for Android version 3.7.0.108 and new instructions, since some of the previous steps are no longer necessary.

From the ApprenticeAlf Comments:


"Me II" writes:

Since “Me”‘s old method for getting PIDs from Kindle for Android is outdated and no longer works with newer versions of the app, I decided I’d take a stab at bringing it up to date. It took a little fiddling to get everything working, considering how much has changed since the last patch, but I managed to do it. The process is pretty much identical to “Me”‘s original instructions, with a few minor changes.

1) You don’t need to build apktool from source. You can just grab the binaries from here for whatever OS you’re running: http://code.google.com/p/android-apktool/
2) When you sign the rebuilt APK, use the following command instead of the one in the instructions:
jarsigner -verbose -sigalg MD5withRSA -digestalg SHA1 -keystore kindle.keystore kindle3_patched.apk kindle
3) It no longer logs the PIDs, only displays them within the app.

You can get the new patch, for version 3.7.0.108, here: http://pastebin.com/6FN2cTSN

And here’s a screenshot of the updated menu: http://imgur.com/BbFVF (sorry for the Japanese, I was too lazy to change my phone’s language).

Subsequently, "s" wrote:

For others it would be useful to add the keystore generation command into the help file:
keytool -genkey -v -keystore kindle.keystore -alias kindle -keyalg RSA -keysize 2048 -validity 10000
As well as location of prc’s on android being (with sdcard):
/mnt/sdcard/Android/data/com.amazon.kindle/files/

"s" also reported success with using the patch on version 3.7.1.8, although I recommend using the 3.7.0.108 version just in case.


"Me"'s original instructions, from the ApprenticeAlf Comments:

"Me" writes:

A better solution seems to create a patched version of the Kindle apk which either logs or displays it’s PID. I created a patch to both log the pid list and show it in the Kindle application in the about activity screen. The pid list isn’t available until the DRMed book has been opened (and the list seem to differ for different books).

To create the patched kindle apk a certificate must be created (http://developer.android.com/guide/publishing/app-signing.html#cert) and the apktool must be build from source (all subprojects) as long as version 1.4.2 isn’t released (http://code.google.com/p/android-apktool/wiki/BuildApktool).

These are the steps to pull the original apk from the Android device, uninstall it, create a patched apk and install that (tested on a rooted device, but I think all steps should also work on non-rooted devices):

adb pull /data/app/com.amazon.kindle-1.apk kindle3.apk
adb uninstall com.amazon.kindle
apktool d kindle3.apk kindle3
cd kindle3
patch -p1 < ../kindle3.patch
cd ..
apktool b kindle3 kindle3_patched.apk
jarsigner -verbose -keystore kindle.keystore kindle3_patched.apk kindle
zipalign -v 4 kindle3_patched.apk kindle3_signed.apk
adb install kindle3_signed.apk

kindle3.patch (based on kindle version 3.0.1.70) is available on pastebin:
http://pastebin.com/LNpgkcpP

Have fun!

Comment by me — June 9, 2011 @ 9:01 pm | Reply

Hi me,
Wow! Great work!!!!

With your patch, you have created the equivalent of Unswindle for the Kindle for Android app and it does not even require jailbreaking!

Very nice work indeed!

Comment by some_updates — June 10, 2011 @ 4:28 am | Reply

