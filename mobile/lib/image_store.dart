import 'dart:io';

import 'package:path_provider/path_provider.dart';

/// 图片文件管理：图片复制到应用目录，文件名记录在数据里。
class ImageStore {
  static Future<Directory> _dir() async {
    final base = await getApplicationDocumentsDirectory();
    final d = Directory('${base.path}/images');
    if (!await d.exists()) {
      await d.create(recursive: true);
    }
    return d;
  }

  /// 把选择的图片复制进应用目录，返回存储文件名。
  static Future<String> import(File src) async {
    final dir = await _dir();
    final dot = src.path.lastIndexOf('.');
    final ext = dot >= 0 ? src.path.substring(dot).toLowerCase() : '';
    final safe = const ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']
            .contains(ext)
        ? ext
        : '.png';
    final name =
        '${DateTime.now().microsecondsSinceEpoch.toRadixString(16)}$safe';
    await src.copy('${dir.path}/$name');
    return name;
  }

  static Future<File?> file(String name) async {
    if (name.isEmpty) return null;
    final dir = await _dir();
    final f = File('${dir.path}/$name');
    return await f.exists() ? f : null;
  }

  static Future<void> delete(String name) async {
    try {
      final f = await file(name);
      if (f != null && await f.exists()) {
        await f.delete();
      }
    } catch (_) {
      // 忽略删除失败
    }
  }
}
