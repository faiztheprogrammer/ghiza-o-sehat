import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:image_picker/image_picker.dart';
import 'package:ghiza_o_sehat/api_service.dart';
import 'package:ghiza_o_sehat/main.dart';

void main() {
  testWidgets('confirmation, weight, correction and unsupported meal flow', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(800, 1600));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final requests = <Map<String, dynamic>>[];
    var uploads = 0;
    final api = ApiService(
      client: MockClient((request) async {
        switch (request.url.path) {
          case '/classes':
            return http.Response(
              jsonEncode({
                'classes': ['chapati', 'biryani', 'creamy_chicken_curry'],
                'count': 3,
              }),
              200,
            );
          case '/predict':
            uploads++;
            expect(
              request.headers['content-type'],
              contains('multipart/form-data'),
            );
            final multipart = latin1.decode(request.bodyBytes);
            expect(multipart, contains('name="file"'));
            expect(multipart, contains('image/jpeg'));
            return http.Response(
              jsonEncode({
                'prediction': 'chapati',
                'confidence': 80,
                'needs_confirmation': true,
                'model_version': 'v1',
                'top3': [
                  {'class': 'chapati', 'confidence': 80},
                  {'class': 'biryani', 'confidence': 15},
                  {'class': 'creamy_chicken_curry', 'confidence': 5},
                ],
              }),
              200,
            );
          case '/estimate-calories':
            final body = jsonDecode(request.body) as Map<String, dynamic>;
            requests.add(body);
            expect(body['food_confirmed'], isTrue);
            expect(body['portion_grams'], 50);
            if (body['confirmed_food'] != 'chapati') {
              return http.Response(
                jsonEncode({
                  'status': 'unavailable',
                  'confirmed_food': body['confirmed_food'],
                  'reason': 'No supported nutrition data for this food.',
                }),
                200,
              );
            }
            return http.Response(
              jsonEncode({
                'status': 'estimated',
                'confirmed_food': 'chapati',
                'portion_grams': 50,
                'kcal_per_100g': 259,
                'calories': 129.5,
                'source_name': 'Pakistan food table',
                'source_reference': 'row 19',
                'notes': ['This is an estimate.'],
              }),
              200,
            );
          default:
            return http.Response('Not found', 404);
        }
      }),
    );
    addTearDown(api.close);
    await tester.pumpWidget(
      MainApp(
        api: api,
        pickPhoto: () async => XFile.fromData(
          Uint8List.fromList([255, 216, 255, 0]),
          name: 'food.jpg',
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Select food photograph'));
    await tester.pumpAndSettle();
    expect(uploads, 1);
    expect(find.text('Prediction: chapati'), findsOneWidget);
    expect(find.text('80.0% model confidence'), findsOneWidget);
    expect(
      tester
          .widget<FilledButton>(
            find.widgetWithText(FilledButton, 'Estimate calories'),
          )
          .onPressed,
      isNull,
    );
    expect(requests, isEmpty);
    await tester.tap(find.byType(CheckboxListTile));
    await tester.pumpAndSettle();
    for (final invalid in ['0', '-1', 'hello', 'NaN', 'Infinity']) {
      await tester.enterText(find.byType(TextField), invalid);
      await tester.tap(find.text('Estimate calories'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Enter a positive weight'), findsOneWidget);
      expect(requests, isEmpty);
    }
    await tester.enterText(find.byType(TextField), '50');
    await tester.tap(find.text('Estimate calories'));
    await tester.pumpAndSettle();
    expect(find.text('Estimated calories: 129.5 kcal'), findsOneWidget);
    expect(requests.single, {
      'confirmed_food': 'chapati',
      'food_confirmed': true,
      'portion_grams': 50,
    });
    // Correct via the backend-provided list; this invalidates confirmation/result.
    await tester.tap(find.byType(DropdownButtonFormField<String>));
    await tester.pumpAndSettle();
    await tester.tap(find.text('biryani').last);
    await tester.pumpAndSettle();
    expect(find.text('Estimated calories: 129.5 kcal'), findsNothing);
    expect(
      tester.widget<CheckboxListTile>(find.byType(CheckboxListTile)).value,
      isFalse,
    );
    await tester.tap(find.byType(CheckboxListTile));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Estimate calories'));
    await tester.pumpAndSettle();
    expect(find.text('Nutrition data unavailable'), findsOneWidget);
    expect(requests.last['confirmed_food'], 'biryani');
    // A newly selected photograph must clear confirmation and old results.
    await tester.tap(find.text('Select food photograph'));
    await tester.pumpAndSettle();
    expect(
      tester.widget<CheckboxListTile>(find.byType(CheckboxListTile)).value,
      isFalse,
    );
    expect(find.text('Nutrition data unavailable'), findsNothing);
  });

  testWidgets('connection error can be retried', (tester) async {
    var fail = true;
    final api = ApiService(
      client: MockClient((_) async {
        if (fail) throw http.ClientException('offline');
        return http.Response('{"classes":["chapati"],"count":1}', 200);
      }),
    );
    addTearDown(api.close);
    await tester.pumpWidget(MainApp(api: api));
    await tester.pumpAndSettle();
    expect(find.textContaining('Cannot reach the backend'), findsOneWidget);
    fail = false;
    await tester.tap(find.text('Retry connection'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Cannot reach the backend'), findsNothing);
    expect(
      tester
          .widget<FilledButton>(find.byKey(const Key('selectPhoto')))
          .onPressed,
      isNotNull,
    );
  });

  test('HTTP server failure has a readable message', () async {
    final api = ApiService(
      client: MockClient((_) async => http.Response('failed', 500)),
    );
    addTearDown(api.close);
    await expectLater(api.classes(), throwsA(isA<ApiException>()));
  });
}
