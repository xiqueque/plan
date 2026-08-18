import 'package:flutter/material.dart';

import 'app_theme.dart';

extension AppThemeX on AppTheme {
  /// 浅色边框/分隔色
  Color get borderSoft => primary.withValues(alpha: 0.35);

  /// 选中底色
  Color get selection => primary.withValues(alpha: 0.45);
}

/// 全局当前主题：切换后整个应用重建。
class T {
  T._();

  static AppTheme t = appThemeDefault;
  static final ValueNotifier<String> notifier =
      ValueNotifier(appThemeDefault.id);

  static void apply(String id) {
    final theme = appThemes[id] ?? appThemeDefault;
    t = theme;
    if (notifier.value != theme.id) {
      notifier.value = theme.id;
    }
  }
}

ThemeData buildTheme(AppTheme t) {
  final scheme = ColorScheme.fromSeed(
    seedColor: t.primary,
    primary: t.primary,
    secondary: t.button,
    surface: t.card,
    onSurface: t.text,
    onSurfaceVariant: t.hint,
  );
  return ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    scaffoldBackgroundColor: t.bg,
    dialogTheme: DialogThemeData(backgroundColor: t.card),
    snackBarTheme: SnackBarThemeData(backgroundColor: t.text),
    floatingActionButtonTheme: FloatingActionButtonThemeData(
      backgroundColor: t.primary,
      foregroundColor: Colors.white,
    ),
  );
}
