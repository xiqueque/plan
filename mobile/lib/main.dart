import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'main_screen.dart';
import 'theme.dart';

void main() {
  runApp(const DailyPlanApp());
}

class DailyPlanApp extends StatefulWidget {
  const DailyPlanApp({super.key});

  @override
  State<DailyPlanApp> createState() => _DailyPlanAppState();
}

class _DailyPlanAppState extends State<DailyPlanApp> {
  @override
  void initState() {
    super.initState();
    T.notifier.addListener(_onThemeChanged);
  }

  @override
  void dispose() {
    T.notifier.removeListener(_onThemeChanged);
    super.dispose();
  }

  void _onThemeChanged() {
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '每日计划',
      debugShowCheckedModeBanner: false,
      theme: buildTheme(T.t),
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: const [Locale('zh', 'CN'), Locale('en')],
      locale: const Locale('zh', 'CN'),
      home: const MainScreen(),
    );
  }
}
