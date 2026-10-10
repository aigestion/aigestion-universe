## Crash Details

**Crash Thread**: `Thread[main,5,main]`  
**Crash Timestamp**: `2026-08-29 12:58:28.308 UTC`  

**Crash Message**:
```
Unable to stop service com.termux.api.apis.MicRecorderAPI$MicRecorderService@b657c5c
```


### Stacktrace

```
java.lang.RuntimeException: Unable to stop service com.termux.api.apis.MicRecorderAPI$MicRecorderService@b657c5c
	at android.app.ActivityThread.handleStopService(ActivityThread.java:5862)
	at android.app.ActivityThread.-$$Nest$mhandleStopService(ActivityThread.java:0)
	at android.app.ActivityThread$H.handleMessage(ActivityThread.java:2870)
	at android.os.Handler.dispatchMessageImpl(Handler.java:142)
	at android.os.Handler.dispatchMessage(Handler.java:125)
	at android.os.Looper.loopOnce(Looper.java:296)
	at android.os.Looper.loop(Looper.java:397)
	at android.app.ActivityThread.main(ActivityThread.java:9523)
	at java.lang.reflect.Method.invoke(Native Method)
	at com.android.internal.os.RuntimeInit$MethodAndArgsCaller.run(RuntimeInit.java:575)
	at com.android.internal.os.ZygoteInit.main(ZygoteInit.java:939)
Caused by: java.lang.RuntimeException: stop failed.
	at android.media.MediaRecorder.stop(Native Method)
	at com.termux.api.apis.MicRecorderAPI$MicRecorderService.cleanupMediaRecorder(SourceFile:137)
	at com.termux.api.apis.MicRecorderAPI$MicRecorderService.onDestroy(SourceFile:129)
	at android.app.ActivityThread.handleStopService(ActivityThread.java:5844)
	... 10 more

```
##


## Termux:API App Info (Current)

**APP_NAME**: `Termux:API`  
**PACKAGE_NAME**: `com.termux.api`  
**VERSION_NAME**: `0.53.0`  
**VERSION_CODE**: `1002`  
**UID**: `10431`  
**TARGET_SDK**: `28`  
**IS_DEBUGGABLE_BUILD**: `false`  
**SE_PROCESS_CONTEXT**: `u:r:untrusted_app_27:s0:c175,c257,c512,c768`  
**SE_FILE_CONTEXT**: `u:object_r:app_data_file:s0:c175,c257,c512,c768`  
**SE_INFO**: `default:targetSdkVersion=28:complete`  
**APK_RELEASE**: `F-Droid`  
**SIGNING_CERTIFICATE_SHA256_DIGEST**: `228FB2CFE90831C1499EC3CCAF61E96E8E1CE70766B9474672CE427334D41C42`  
##


## Termux App Info

**APP_NAME**: `Termux`  
**PACKAGE_NAME**: `com.termux`  
**VERSION_NAME**: `0.118.3`  
**VERSION_CODE**: `1002`  
**UID**: `10431`  
**TARGET_SDK**: `28`  
**IS_DEBUGGABLE_BUILD**: `false`  
**SE_PROCESS_CONTEXT**: `u:r:untrusted_app_27:s0:c175,c257,c512,c768`  
**SE_FILE_CONTEXT**: `u:object_r:app_data_file:s0:c175,c257,c512,c768`  
**SE_INFO**: `default:targetSdkVersion=28:complete`  
**TERMUX_APP_PACKAGE_MANAGER**: -  
**TERMUX_APP_PACKAGE_VARIANT**: -  
**APK_RELEASE**: `F-Droid`  
**SIGNING_CERTIFICATE_SHA256_DIGEST**: `228FB2CFE90831C1499EC3CCAF61E96E8E1CE70766B9474672CE427334D41C42`  
##


## Device Info

### Software

**OS_VERSION**: `6.1.157-android14-11-gbd23337e42e7-ab14791245`  
**SDK_INT**: `37`  
**RELEASE**: `17`  
**ID**: `CP2A.260805.005`  
**DISPLAY**: `CP2A.260805.005`  
**INCREMENTAL**: `15828068`  
**SECURITY_PATCH**: `2026-08-05`  
**IS_TREBLE_ENABLED**: `true`  
**TYPE**: `user`  
**TAGS**: `release-keys`  
**MAX_PHANTOM_PROCESSES**: - (*Requires `DUMP` and `PACKAGE_USAGE_STATS` permission*)  
**MONITOR_PHANTOM_PROCS**: `true`  
**DEVICE_CONFIG_SYNC_DISABLED**: -  

### Hardware

**MANUFACTURER**: `Google`  
**BRAND**: `google`  
**MODEL**: `Pixel 8a`  
**PRODUCT**: `akita`  
**BOARD**: `akita`  
**HARDWARE**: `akita`  
**DEVICE**: `akita`  
**SUPPORTED_ABIS**: `arm64-v8a`  
##
