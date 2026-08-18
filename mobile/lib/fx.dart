import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/services.dart';

/// 按键交互反馈：可爱小音效 + 轻微震动（仿电脑版）。
class Fx {
  Fx._();

  static final AudioPlayer _clickPlayer = AudioPlayer();
  static final AudioPlayer _donePlayer = AudioPlayer();
  static bool _init = false;

  static Future<void> _ensure() async {
    if (_init) return;
    _init = true;
    await _clickPlayer.setReleaseMode(ReleaseMode.stop);
    await _clickPlayer.setVolume(0.15);
    await _donePlayer.setReleaseMode(ReleaseMode.stop);
    await _donePlayer.setVolume(0.15);
  }

  /// 普通按键：轻震 + 可爱小音效
  static Future<void> tap() async {
    try {
      await HapticFeedback.lightImpact();
      await _ensure();
      await _clickPlayer.stop();
      await _clickPlayer.play(AssetSource('sounds/click.wav'));
    } catch (_) {
      // 音效/震动失败不影响使用
    }
  }

  /// 完成任务：略强一点的震动 + 完成音效
  static Future<void> complete() async {
    try {
      await HapticFeedback.mediumImpact();
      await _ensure();
      await _donePlayer.stop();
      await _donePlayer.play(AssetSource('sounds/done.wav'));
    } catch (_) {
      // 音效/震动失败不影响使用
    }
  }
}
