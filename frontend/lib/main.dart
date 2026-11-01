import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'api_service.dart';

void main() => runApp(const MainApp());

class MainApp extends StatelessWidget {
  const MainApp({super.key, this.api, this.pickPhoto});
  final ApiService? api;
  final Future<XFile?> Function()? pickPhoto;

  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'Ghiza-o-Sehat',
    theme: ThemeData(colorSchemeSeed: Colors.green, useMaterial3: true),
    home: MealScreen(api: api, pickPhoto: pickPhoto),
  );
}

class MealScreen extends StatefulWidget {
  const MealScreen({super.key, this.api, this.pickPhoto});
  final ApiService? api;
  final Future<XFile?> Function()? pickPhoto;
  @override
  State<MealScreen> createState() => _MealScreenState();
}

class _MealScreenState extends State<MealScreen> {
  late final ApiService _api = widget.api ?? ApiService();
  final _weight = TextEditingController();
  List<String> _classes = [];
  Map<String, dynamic>? _prediction;
  Map<String, dynamic>? _result;
  String? _food;
  String? _error;
  String? _photoName;
  bool _confirmed = false;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _loadClasses();
  }

  Future<void> _run(Future<void> Function() action) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await action();
    } catch (error) {
      if (mounted) {
        setState(
          () => _error = error is ApiException
              ? error.message
              : 'Something went wrong. Please try again or select another photo.',
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _loadClasses() => _run(() async {
    final foods = await _api.classes();
    if (foods.isEmpty) {
      throw ApiException('No foods were returned. Please retry.');
    }
    if (mounted) setState(() => _classes = foods);
  });

  Future<void> _selectPhoto() => _run(() async {
    final photo =
        await (widget.pickPhoto?.call() ??
            ImagePicker().pickImage(source: ImageSource.gallery));
    if (photo == null || !mounted) return;
    setState(() {
      _photoName = photo.name;
      _prediction = null;
      _result = null;
      _food = null;
      _confirmed = false;
      _weight.clear();
    });
    final prediction = await _api.predict(photo);
    if (!mounted) return;
    setState(() {
      _prediction = prediction;
      final predictedFood = prediction['prediction'] as String;
      _food = _classes.contains(predictedFood) ? predictedFood : null;
      // A prediction is a suggestion, never user confirmation.
      _confirmed = false;
    });
  });

  void _changeFood(String? food) => setState(() {
    _food = food;
    _confirmed = false;
    _result = null;
    _error = null;
  });

  Future<void> _estimate() async {
    final grams = double.tryParse(_weight.text.trim());
    if (grams == null || !grams.isFinite || grams <= 0) {
      setState(() => _error = 'Enter a positive weight in grams, such as 50.');
      return;
    }
    if (!_confirmed || _food == null) return;
    await _run(() async {
      setState(() => _result = null);
      final result = await _api.estimate(_food!, grams);
      if (mounted) setState(() => _result = result);
    });
  }

  @override
  void dispose() {
    _weight.dispose();
    if (widget.api == null) _api.close();
    super.dispose();
  }

  String _label(String food) => food.replaceAll('_', ' ');

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Ghiza-o-Sehat')),
    body: SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(
            'Understand your meal',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 8),
          const Text(
            'Choose a photo, confirm the food, then enter its cooked weight in grams.',
          ),
          const SizedBox(height: 16),
          if (_busy) ...[
            const LinearProgressIndicator(),
            const Text('Please wait…'),
            const SizedBox(height: 12),
          ],
          if (_error != null) ...[
            Text(
              _error!,
              key: const Key('error'),
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
            const SizedBox(height: 12),
          ],
          if (_classes.isEmpty)
            OutlinedButton(
              onPressed: _busy ? null : _loadClasses,
              child: const Text('Retry connection'),
            ),
          FilledButton.icon(
            key: const Key('selectPhoto'),
            onPressed: _busy || _classes.isEmpty ? null : _selectPhoto,
            icon: const Icon(Icons.photo_library_outlined),
            label: const Text('Select food photograph'),
          ),
          if (_photoName != null) Text('Photo: $_photoName'),
          if (_prediction != null) ...[
            const SizedBox(height: 20),
            Text(
              'Prediction: ${_label(_prediction!['prediction'] as String)}',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const Text('Model suggestions — please check them yourself.'),
            for (final candidate in _prediction!['top3'] as List)
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(_label(candidate['class'] as String)),
                subtitle: Text(
                  '${(candidate['confidence'] as num).toStringAsFixed(1)}% model confidence',
                ),
                trailing: TextButton(
                  onPressed: _busy
                      ? null
                      : () => _changeFood(candidate['class'] as String),
                  child: const Text('Choose'),
                ),
              ),
            DropdownButtonFormField<String>(
              key: ValueKey(_food),
              initialValue: _food,
              isExpanded: true,
              decoration: const InputDecoration(
                labelText: 'Choose or correct the food',
              ),
              items: _classes
                  .map(
                    (food) => DropdownMenuItem(
                      value: food,
                      child: Text(_label(food)),
                    ),
                  )
                  .toList(),
              onChanged: _busy ? null : _changeFood,
            ),
            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('I confirm this is the food I ate'),
              value: _confirmed,
              onChanged: _busy || _food == null
                  ? null
                  : (value) => setState(() {
                      _confirmed = value ?? false;
                      _result = null;
                    }),
            ),
            TextField(
              controller: _weight,
              enabled: !_busy && _confirmed,
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              decoration: const InputDecoration(
                labelText: 'Cooked food weight (grams)',
                hintText: '50',
              ),
              onChanged: (_) => setState(() {
                _result = null;
                _error = null;
              }),
            ),
            const SizedBox(height: 8),
            const Text(
              'Only chapati currently has nutrition data. Weight must come from you, not the photograph.',
            ),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: _busy || !_confirmed ? null : _estimate,
              child: const Text('Estimate calories'),
            ),
          ],
          if (_result != null) ...[
            const Divider(height: 32),
            if (_result!['status'] == 'unavailable') ...[
              Text(
                'Nutrition data unavailable',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              Text(_result!['reason'] as String),
            ] else ...[
              Text(
                'Estimated calories: ${_result!['calories']} kcal',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              Text(
                '${_label(_result!['confirmed_food'] as String)} · ${_result!['portion_grams']} g',
              ),
              Text('${_result!['kcal_per_100g']} kcal per 100 g'),
              const SizedBox(height: 8),
              Text(_result!['source_name'] as String),
              SelectableText(_result!['source_reference'] as String),
              for (final note in _result!['notes'] as List)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(note as String),
                ),
            ],
          ],
        ],
      ),
    ),
  );
}
