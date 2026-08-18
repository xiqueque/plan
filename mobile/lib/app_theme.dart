// 由 scripts/extract_themes.py 从 peise 图片自动生成，与电脑版配色一致
import 'package:flutter/material.dart';

/// 一套主题配色
class AppTheme {
  final String id;
  final Color bg;
  final Color primary;
  final Color button;
  final Color text;
  final Color hint;
  final Color card;

  const AppTheme({
    required this.id,
    required this.bg,
    required this.primary,
    required this.button,
    required this.text,
    required this.hint,
    required this.card,
  });
}

/// 默认淡蓝主题
const appThemeDefault = AppTheme(
  id: '默认淡蓝',
  bg: Color(0xFFEAF6FC),
  primary: Color(0xFF7FB8D4),
  button: Color(0xFFADD8E6),
  text: Color(0xFF1F3A4D),
  hint: Color(0xFF6B8CA3),
  card: Color(0xFFFFFFFF),
);

/// 8 套图片主题
final Map<String, AppTheme> appThemes = {
  '碧海晴空': AppTheme(
    id: '碧海晴空',
    bg: Color(0xFFF6F2F0),
    primary: Color(0xFFE7CACA),
    button: Color(0xFFE6A6AC),
    text: Color(0xFF5D5666),
    hint: Color(0xFFA6A2AB),
    card: Color(0xFFFCFAFA),
  ),
  '青翠山林': AppTheme(
    id: '青翠山林',
    bg: Color(0xFFF7F6F4),
    primary: Color(0xFFF0D6D6),
    button: Color(0xFFF1CB8D),
    text: Color(0xFF64675B),
    hint: Color(0xFFAAABA5),
    card: Color(0xFFFCFCFB),
  ),
  '暖阳橙光': AppTheme(
    id: '暖阳橙光',
    bg: Color(0xFFF6F5F4),
    primary: Color(0xFFE1DBD9),
    button: Color(0xFFD2CECD),
    text: Color(0xFF505861),
    hint: Color(0xFF9FA3A8),
    card: Color(0xFFFCFCFB),
  ),
  '桃粉春色': AppTheme(
    id: '桃粉春色',
    bg: Color(0xFFF7F6F4),
    primary: Color(0xFFEEE2D3),
    button: Color(0xFFC7D4E6),
    text: Color(0xFF4D677E),
    hint: Color(0xFF9DABB8),
    card: Color(0xFFFCFCFB),
  ),
  '紫霞暮色': AppTheme(
    id: '紫霞暮色',
    bg: Color(0xFFF9F8F5),
    primary: Color(0xFFECE0D1),
    button: Color(0xFFE2D3C2),
    text: Color(0xFF596166),
    hint: Color(0xFFA4A8AB),
    card: Color(0xFFFDFCFC),
  ),
  '金秋麦浪': AppTheme(
    id: '金秋麦浪',
    bg: Color(0xFFF6F5F4),
    primary: Color(0xFFE5D9C9),
    button: Color(0xFFC6D1BE),
    text: Color(0xFF4B6466),
    hint: Color(0xFF9CAAAB),
    card: Color(0xFFFCFCFB),
  ),
  '冰川银雪': AppTheme(
    id: '冰川银雪',
    bg: Color(0xFFF7F7F8),
    primary: Color(0xFFDCDCDB),
    button: Color(0xFFB8CBCA),
    text: Color(0xFF48646F),
    hint: Color(0xFF9AAAB0),
    card: Color(0xFFFCFCFC),
  ),
  '莓果甜心': AppTheme(
    id: '莓果甜心',
    bg: Color(0xFFF6F6F7),
    primary: Color(0xFFD9E2E7),
    button: Color(0xFFC7C5D5),
    text: Color(0xFF4A5F74),
    hint: Color(0xFF9BA7B3),
    card: Color(0xFFFCFCFC),
  ),
};
