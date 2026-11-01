import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:image_picker/image_picker.dart';

class ApiException implements Exception {
  ApiException(this.message);
  final String message;
  @override
  String toString() => message;
}

class ApiService {
  ApiService({http.Client? client, this.baseUrl = defaultUrl})
    : _client = client ?? http.Client();

  static const defaultUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );
  final String baseUrl;
  final http.Client _client;

  Uri _uri(String path) =>
      Uri.parse('${baseUrl.replaceAll(RegExp(r'/+$'), '')}$path');

  Future<Map<String, dynamic>> _request(
    Future<http.Response> Function() send,
  ) async {
    try {
      final response = await send().timeout(const Duration(seconds: 60));
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw ApiException(switch (response.statusCode) {
          400 =>
            'The photo could not be read. Choose a JPEG, PNG or WebP image.',
          413 => 'The photo is too large. Choose an image smaller than 10 MB.',
          422 =>
            'Check the selected food and enter a positive weight in grams.',
          _ => 'The server could not complete the request. Please try again.',
        });
      }
      return jsonDecode(response.body) as Map<String, dynamic>;
    } on TimeoutException {
      throw ApiException(
        'The server took too long. Check the connection and retry.',
      );
    } on http.ClientException {
      throw ApiException(
        'Cannot reach the backend. Check that it is running and the API address is correct.',
      );
    } on FormatException {
      throw ApiException('The backend returned an unreadable response.');
    }
  }

  Future<List<String>> classes() async {
    final data = await _request(() => _client.get(_uri('/classes')));
    return List<String>.from(data['classes'] as List);
  }

  Future<Map<String, dynamic>> predict(XFile photo) async {
    if (await photo.length() > 10 * 1024 * 1024) {
      throw ApiException(
        'The photo is too large. Choose an image smaller than 10 MB.',
      );
    }
    final bytes = await photo.readAsBytes();
    // Identify bytes rather than trusting a gallery filename or extension.
    final String subtype;
    if (bytes.length >= 3 &&
        bytes[0] == 0xff &&
        bytes[1] == 0xd8 &&
        bytes[2] == 0xff) {
      subtype = 'jpeg';
    } else if (bytes.length >= 8 &&
        bytes.take(8).join(',') == '137,80,78,71,13,10,26,10') {
      subtype = 'png';
    } else if (bytes.length >= 12 &&
        ascii.decode(bytes.sublist(0, 4), allowInvalid: true) == 'RIFF' &&
        ascii.decode(bytes.sublist(8, 12), allowInvalid: true) == 'WEBP') {
      subtype = 'webp';
    } else {
      throw ApiException('Choose a JPEG, PNG or WebP photo.');
    }
    final request = http.MultipartRequest('POST', _uri('/predict'))
      ..files.add(
        http.MultipartFile.fromBytes(
          'file',
          bytes,
          filename: 'meal.$subtype',
          contentType: MediaType('image', subtype),
        ),
      );
    return _request(
      () async => http.Response.fromStream(await _client.send(request)),
    );
  }

  Future<Map<String, dynamic>> estimate(String food, double grams) {
    return _request(
      () => _client.post(
        _uri('/estimate-calories'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'confirmed_food': food,
          'food_confirmed': true,
          'portion_grams': grams,
        }),
      ),
    );
  }

  void close() => _client.close();
}
