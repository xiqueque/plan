import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'main_screen.dart';

void main() {
  runApp(const DailyPlanApp());
}

class DailyPlanApp extends StatelessWidget {
  const DailyPlanApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '每日计划',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF7FB8D4)),
        scaffoldBackgroundColor: const Color(0xFFEAF6FC),
      ),
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
