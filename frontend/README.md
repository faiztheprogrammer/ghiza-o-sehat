# Ghiza-o-Sehat Android interface

Select a JPEG, PNG or WebP photo, review the prediction/top three, correct the
food using `/classes`, explicitly confirm it, and enter cooked food weight in
grams. Only chapati has nutrition data; other foods show "Nutrition data
unavailable". No nutrition or weight is calculated from an image.

## Environment and prerequisites

Created with Flutter 3.35.5 / Dart 3.9.2. Android is the only generated target.
No prior Flutter project existed. At implementation time there was no connected
Android phone, no configured emulator, and some Android SDK licenses were not
accepted. Android Studio was not installed.

Review and accept SDK terms yourself:

```powershell
flutter doctor --android-licenses
flutter doctor
```

Either connect an Android phone with USB debugging enabled and approve its
debugging prompt, or install Android Studio and create/start an Android virtual
device through Device Manager. Use `flutter devices` to get its device ID.

## Run

Terminal 1, from the repository root (wait for model loading to finish):

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Verify `http://127.0.0.1:8000/health` on the PC. Keep this terminal running.

Terminal 2, from the repository root:

```powershell
cd frontend
flutter pub get
flutter devices
# Replace ANDROID_DEVICE_ID with the ID shown by flutter devices.
flutter run -d ANDROID_DEVICE_ID --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

The default address `10.0.2.2` reaches the host PC from an Android emulator.
The emulator's `localhost` refers to the emulator itself.

### Physical Android phone

Put phone and PC on the same Wi-Fi. Run `ipconfig` on the PC to find its active
Wi-Fi IPv4 address. If it is `192.168.1.20`, first open
`http://192.168.1.20:8000/health` in the phone browser, then run from `frontend`:

```powershell
flutter run -d ANDROID_DEVICE_ID --dart-define=API_BASE_URL=http://192.168.1.20:8000
```

Replace the example address and ID. If Windows Firewall prompts, allow Python
on the private network. Check firewall rules and Wi-Fi client isolation if the
phone cannot reach `/health`. Do not use `0.0.0.0` as the app address.

USB alternative, with Android SDK `adb` on PATH:

```powershell
adb -s ANDROID_DEVICE_ID reverse tcp:8000 tcp:8000
flutter run -d ANDROID_DEVICE_ID --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

Restart `flutter run` after changing the address. Local HTTP is allowed in the
Android **debug** manifest only. Release builds require HTTPS; deployment is
outside this milestone.

## API behavior

- `/classes`: reads `classes` for correction.
- `/predict`: multipart field `file` with image MIME type; reads `prediction`
  and `top3` entries (`class`, `confidence`).
- `/estimate-calories`: sends this only after explicit confirmation:

```json
{"confirmed_food":"chapati","food_confirmed":true,"portion_grams":50}
```

Results display backend `calories`, `portion_grams`, `kcal_per_100g`, food,
`source_name`, `source_reference` and `notes`. For `status: unavailable`, display
the backend `reason` without calories. Creamy chicken curry remains unsupported.
There are no client-side calorie formulas or predefined servings.

Changing food/new photo clears confirmation and old results. Changing weight
clears old results. Invalid, nonpositive and nonfinite weights are blocked.
Requests time out after 60 seconds. Connection and server errors are shown
with retry options. Cancelling photo selection keeps the current meal.

## Checks

Verified on 2026-10-20: `flutter analyze --no-pub` reported **No issues found**
(9.7 seconds); `flutter test --no-pub` reported **3 tests passed**.
No backend files were changed, so backend tests were not rerun for this milestone.
Android APK build and real-device smoke testing were not performed: no device or
emulator was available and SDK license setup is incomplete.

From `frontend`:

```powershell
dart format --output=none --set-exit-if-changed lib test
flutter analyze
flutter test
```

Widget/API tests inject a gallery selection and mock HTTP. They check multipart
upload, the confirmation gate, gram validation, exact estimate request, calorie
display, food correction, unavailable food, new-photo reset and connection errors.
These tests do not verify Android gallery permissions or real device networking.

Manual Android smoke test:

1. Put a photo in the device's photo library and select it in the app.
2. Check prediction and three suggestions. Estimation must start disabled.
3. Select chapati, explicitly confirm, enter 50 g and submit: expect 129.5 kcal.
4. Enter zero/negative weight or text: expect a validation message.
5. Select biryani or creamy chicken curry, confirm again and submit positive
   grams: expect "Nutrition data unavailable".
6. Select another photo: old confirmation/results must be cleared.
7. Stop the backend and retry: expect a readable connection error.

The meal is held only in memory. Restarting the app, including an Android process
restart during photo picking, requires selecting the photo again. Authentication,
history, summaries, Gemini and persistence are not included.

## Structure

- `lib/main.dart`: single-screen flow and temporary state.
- `lib/api_service.dart`: requests, multipart upload and error messages.
- `test/meal_flow_test.dart`: widget/API contract checks.
- `android/`: generated runner, internet permission and debug HTTP configuration.
- `pubspec.yaml` / `pubspec.lock`: dependencies and resolved versions.

Direct packages: `image_picker` (gallery), `http` (requests), `http_parser`
(multipart media type). References: [Flutter networking](https://docs.flutter.dev/cookbook/networking/send-data)
and [image_picker](https://pub.dev/packages/image_picker).

Creation commands, run from the repository root and then `frontend` respectively:

```powershell
flutter create --platforms=android --project-name ghiza_o_sehat --org com.ghizaosehat --empty frontend
cd frontend
flutter pub add http image_picker http_parser
```
