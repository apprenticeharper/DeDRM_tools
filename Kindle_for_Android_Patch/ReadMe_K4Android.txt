Kindle for Android
------------------

Kindle for Android uses a different scheme to generate its books specific PIDs than Kindle for PC, Kindle for iPhone/iPad, and standalone Kindles.

Unfortunately, K4Android uses an "account secrets" file that would only be available if the device were jail-broken and even then someone would have to figure out how to decode this secret information in order to reverse the process.

Instead of trying to calculate the correct PIDs for each book from this primary data, "Me" (a commenter who posted to the ApprenticeAlf site)  came up with a wonderful idea to simply modify the Kindle 3 for Android application to store the PIDs it uses to decode each book in its "about activity" window.  This list of PIDS can then be provided to MobiDeDRM.py,  which in its latest incarnations allows a comma separated list of pids to be passed in, to successfully remove the DRM from that book.   Effectively "Me" has created an "Unswindle" for the Kindle for Android 3 application!

Obviously, to use "Me"'s approach, requires an Android Developer's Certificate (to sign the modified application) and access to and knowledge of the developer tools, but does not require anything to be jail-broken.

This is a copy the detailed instructions supplied by "Me" to the ApprenticeAlf blog in the comments.  The kindle3.patch described below is included in this folder in the tools:
 
From the ApprenticeAlf Comments:

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

