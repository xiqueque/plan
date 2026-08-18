import 'dart:convert';
import 'dart:io';

import 'package:path_provider/path_provider.dart';

import 'models.dart';

class Storage {
  static Future<File> _file() async {
    final dir = await getApplicationDocumentsDirectory();
    return File('${dir.path}/plan.json');
  }

  static Future<PlanData> load() async {
    try {
      final f = await _file();
      if (!await f.exists()) return PlanData();
      final s = await f.readAsString();
      return PlanData.fromJson(jsonDecode(s) as Map<String, dynamic>);
    } catch (_) {
      return PlanData();
    }
  }

  static Future<void> save(PlanData data) async {
    try {
      final f = await _file();
      await f.writeAsString(jsonEncode(data.toJson()));
    } catch (_) {
      // 保存失败不影响界面，下次操作会再尝试
    }
  }
}
